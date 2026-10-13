"""Compare forward resource packing with original operation-boundary fixtures."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright
from verify_heap import parse,ROOT


def verify(reference,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    fixtures=trace['heap'];assert len(fixtures)==4 and trace['passed']
    states=[]
    for f in fixtures:
        data=(reference/f['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==f['sha256']
        states.append(parse(data,f['ss']))
    report=dict(passed=False,reference=str(reference),source_sha256=hashlib.sha256((ROOT/'treehouse-demo/heap.js').read_bytes()).hexdigest(),checks=[],errors=[],full_game_parity=False)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/heap.js'))
        try:
            for i in range(0,len(fixtures),2):
                assert fixtures[i]['phase']==0 and fixtures[i+1]['phase']==1
                assert fixtures[i]['requested']==fixtures[i+1]['requested']
                result=page.evaluate('a=>{const heap=new OriginalHeap({...a.state,closedArena:true});const available=heap.pack(a.requested);return {state:heap.snapshot(),available,moves:heap.moves};}',dict(state=states[i],requested=fixtures[i]['requested']))
                actual=result['state'];expected=states[i+1]
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in expected if expected[k]!=actual[k]}
                end=next(e for e in trace['events'] if e['label']=='heap.pack.return' and e['milliseconds']==fixtures[i+1]['milliseconds'])
                available=end['ax']+65536*end['dx']
                if result['available']!=available:differences['available']=dict(expected=available,actual=result['available'])
                report['checks'].append(dict(name=f'packing {i//2}',requested=fixtures[i]['requested'],passed=not differences,differences=differences,available=result['available'],moves=result['moves']))
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==2 and all(c['passed'] for c in report['checks'])
    report['scope']='Two complete resident 6652 packing operations from explicit offline initial heap fixtures. Compare all block geometry, flags, payload hashes, handles and search cursor. No CPU instruction counts or runtime fixture use. Does not prove whole-game resource lifetimes or fix the served game.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors'],checks=[dict(name=c['name'],passed=c['passed'],moves=len(c['moves']),different_fields=list(c['differences'])) for c in report['checks']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/board-cursor-relocation-c')
    a=p.parse_args();raise SystemExit(0 if verify(a.reference,a.output) else 1)
