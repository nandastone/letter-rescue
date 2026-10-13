"""Generate the first embedded font load from executable/platform source data."""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile
from playwright.sync_api import sync_playwright
from executable import unpack
from verify_dos_resource_startup import startup_inputs,mcbs
from verify_resource_growth import ROOT,DATA,digest,arena_state
from verify_near_heap import parse as parse_near


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    startup,font_size=startup_inputs()
    with zipfile.ZipFile(DATA/'source/The_Treehouse_1991.zip') as archive:
        image,_=unpack(archive.read('TheTreeh/treehse.exe'))
    entry=image[0x31660+10:0x31660+25]
    offset,segment=struct.unpack_from('<HH',entry,6)
    payload=image[16*segment+offset:16*segment+offset+font_size]
    assert len(payload)==font_size and entry[12]==0x10
    folder=DATA/'resource-startup-font-a'
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
    assert run['passed'] and run['fixed_clock'] and len(run['heap'])==4
    raw=[]
    for fixture in run['heap'][:2]:
        path=folder/fixture['path'];assert digest(path)==fixture['sha256'];raw.append(path.read_bytes())
    ss=run['heap'][0]['ss']
    expected=arena_state(raw[1],ss)[0]
    returned=next(e['ax'] for e in run['events'] if e['label']=='font.source.return')
    modules=['heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js','resource-loading.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        actual=page.evaluate('''a=>{
          const platform=OriginalResourceStartup.memory(a.startup),m=platform.memory;
          const initial={arena:{...m.arena,heap:m.heap.snapshot()},near:m.near.snapshot()};
          const loader=new OriginalResourceLoading(m,0,{observeWork:false,embeddedCatalog:true});
          const handle=loader.source('builtin:FONT:0',a.payload,a.flags);
          const result=structuredClone({initial,handle,arena:{...m.arena,heap:m.heap.snapshot()},near:m.near.snapshot(),dos:platform.dos.snapshot(),
            bytes:Array.from(loader.payloads.get(handle)),operations:loader.operations.slice(),catalogState:loader.embeddedCatalog.state});
          const before=JSON.stringify(m.heap.snapshot()),opCount=loader.operations.length;
          const warm=loader.source('builtin:FONT:0',a.payload,a.flags);
          result.warm=warm===handle&&loader.operations.length===opCount&&JSON.stringify(m.heap.snapshot())===before;
          m.discard(handle);loader.source('builtin:FONT:0',a.payload,a.flags);
          result.reload=loader.sources.get('builtin:FONT:0')===handle&&loader.operations.at(-2).kind==='handle.reallocate'&&loader.operations.at(-1).kind==='resource.copy';
          result.noWork=typeof OriginalResourceWork==='undefined'&&loader.sourceWork.length===0;
          return result;
        }''',dict(startup=startup,payload=list(payload),flags=entry[12]))
        browser.close()
    # The model owns bytes; hash them only in this comparison adapter, using
    # the same representation as the native arena parser.
    block=next(b for b in actual['arena']['heap']['blocks'] if b.get('handle')==actual['handle'])
    block['payload']=hashlib.sha256(bytes(actual['bytes'])).hexdigest()
    pairs=[('initial arena',actual['initial']['arena'],arena_state(raw[0],ss)[0]),
           ('initial near state',actual['initial']['near'],parse_near(raw[0],ss)),
           ('returned font handle',actual['handle'],returned),
           ('complete arena including font payload',actual['arena'],expected),
           ('complete near state',actual['near'],parse_near(raw[1],ss)),
           ('DOS ownership',actual['dos'],mcbs(raw[1])),
           ('static catalog lock restored',actual['catalogState'],0),
           ('source copy operations',actual['operations'],[dict(kind='handle.allocate',bytes=font_size),dict(kind='resource.copy',bytes=font_size)])]
    checks=[dict(name=n,passed=a==e,actual=a,expected=e) for n,a,e in pairs]
    focused=[dict(name=n,passed=actual[k]) for n,k in [('warm embedded cache avoids allocation/copy','warm'),('discarded embedded source reloads same handle','reload'),('no instruction-work dependency','noWork')]]
    report=dict(passed=all(c['passed'] for c in checks+focused),checks=checks,focused=focused,
                models={n:digest(ROOT/'treehouse-demo'/n) for n in modules},reference_sha256=digest(folder/'run.json'),
                inputs=startup,font_sha256=hashlib.sha256(payload).hexdigest(),full_game_parity=False,playable_changed=False,
                scope='Continuous source-generated startup through first FONT 0 source load, including exact loaded bytes and cache ownership. No native memory initializes the model. The second font load and later startup/activity lifetimes remain open; focused warm/reload checks are not additional native comparisons.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=[dict(name=c['name'],passed=c['passed']) for c in checks+focused]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
