"""Generate the first complete handle allocation from the startup arena rules."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
from verify_resource_growth import ROOT,DATA,digest,arena_state,available_paragraphs
from verify_near_heap import parse as parse_near
from verify_dos_resource_startup import startup_inputs,mcbs


def verify(output):
    output.mkdir(parents=True,exist_ok=False);folder=DATA/'resource-startup-handle-b'
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'));assert run['passed'] and len(run['heap'])==2
    raw=[];arenas=[];near=[]
    for f in run['heap']:
        path=folder/f['path'];assert digest(path)==f['sha256'];data=path.read_bytes();raw.append(data)
        arenas.append(arena_state(data,f['ss'])[0]);near.append(parse_near(data,f['ss']))
    initial,expected=arenas;end=next(e for e in run['events'] if e['label']=='handle.allocate.return' and e['milliseconds']==run['heap'][1]['milliseconds'])
    handle=end['ax'];next(b for b in expected['heap']['blocks'] if b.get('handle')==handle).pop('payload')
    startup,font_bytes=startup_inputs();assert font_bytes==run['heap'][0]['requested']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        actual=page.evaluate('''a=>{
          const platform=OriginalResourceStartup.memory(a.startup),memory=platform.memory;
          const initialized={...memory.arena,heap:memory.heap.snapshot()},initialNear=memory.near.snapshot();
          const handle=memory.allocateHandle(a.bytes);
          return {initialized,initialNear,handle,arena:{...memory.arena,heap:memory.heap.snapshot()},near:memory.near.snapshot(),dos:platform.dos.snapshot()};
        }''',dict(startup=startup,bytes=font_bytes))
        browser.close()
    checks=[dict(name='generated initial arena',passed=actual['initialized']==initial),dict(name='returned handle',passed=actual['handle']==handle),
            dict(name='complete arena and handle state',passed=actual['arena']==expected,expected=expected,actual=actual['arena']),
            dict(name='complete near state',passed=actual['near']==near[1],expected=near[1],actual=actual['near']),
            dict(name='generated DOS allocation state',passed=actual['dos']==mcbs(raw[1]),expected=mcbs(raw[1]),actual=actual['dos']),
            dict(name='generated initial near state',passed=actual['initialNear']==near[0],expected=near[0],actual=actual['initialNear'])]
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,reference_sha256=digest(folder/'run.json'),
                models={name:digest(ROOT/'treehouse-demo'/name) for name in ['heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js']},full_game_parity=False,
                inputs=startup,font_bytes=font_bytes,
                scope='First FONT 0 handle allocation generated entirely from pinned executable/configuration bytes and source-defined platform environment. Generates DOS process map, resource arena retries, runtime environment/configuration/scanline near allocations, packing, growth, allocation and ownership. All native near/far/DOS state is comparison output only; no captured state, addresses or allocation request initialize the model. Newly allocated uninitialized payload bytes are outside allocator output. Remaining font loading, other startup resources, complete lifetimes and playable integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=[dict(name=c['name'],passed=c['passed']) for c in checks]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
