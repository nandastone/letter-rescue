"""Compare the board background's complete handle allocation and cursor relocation."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright
from verify_heap import parse as heap_state,ROOT
from verify_near_heap import parse as near_state


def verify(reference,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    fixtures=trace['heap'];assert trace['passed'] and len(fixtures)==2
    states=[]
    for f in fixtures:
        raw=(reference/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256']
        states.append(dict(heap=heap_state(raw,f['ss']),near=near_state(raw,f['ss'])))
    ending=next(e for e in trace['events'] if e['label']=='memory.handle.allocate.return' and e['milliseconds']==fixtures[1]['milliseconds'])
    handle=ending['ax'];expected=states[1]
    # The allocator does not initialize newly allocated payload bytes. Check
    # preservation hashes for every existing resource, and all block metadata.
    allocated=next(b for b in expected['heap']['blocks'] if b.get('handle')==handle)
    allocated.pop('payload')
    report=dict(passed=False,reference=str(reference),errors=[],checks=[],full_game_parity=False)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['heap.js','near-heap.js','memory.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        try:
            actual=page.evaluate('a=>{const memory=new OriginalMemory(a.state),handle=memory.allocateHandle(a.bytes);return {handle,heap:memory.heap.snapshot(),near:memory.near.snapshot(),moves:memory.heap.moves};}',dict(state=states[0],bytes=fixtures[0]['requested']))
            report['checks'].append(dict(name='allocated handle',passed=actual['handle']==handle,expected=handle,actual=actual['handle']))
            for kind in ['heap','near']:
                differences={k:dict(expected=expected[kind][k],actual=actual[kind][k]) for k in expected[kind] if expected[kind][k]!=actual[kind][k]}
                report['checks'].append(dict(name=kind+' state',passed=not differences,differences=differences))
            report['moves']=actual['moves']
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==3 and all(c['passed'] for c in report['checks'])
    report['models']={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in ['heap.js','near-heap.js','memory.js']}
    report['scope']='Complete handle allocation for 24,961 converted board-background bytes, from one offline initial heap/near-heap fixture. Compare returned handle, all allocator metadata, existing resource payload hashes and cursor relocation. Newly allocated payload contents are uninitialized and are not an allocator output. No recorded resource offsets or requests are used by the playable game.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors'],moves=len(report.get('moves',[])),checks=[dict(name=c['name'],passed=c['passed']) for c in report['checks']]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/board-cursor-allocation-a')
    a=p.parse_args();raise SystemExit(0 if verify(a.reference,a.output) else 1)
