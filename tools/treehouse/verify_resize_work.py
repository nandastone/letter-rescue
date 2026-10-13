"""Compare generated in-place resize decisions and native intrinsic work."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False);memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted memory evidence')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    if work['routine']!='resident:70E8' or len(work['calls'])!=106:raise ValueError('Incomplete resize capture')
    begin,end=scene['heap'][0]['milliseconds'],scene['heap'][-1]['milliseconds'];calls=[c for c in work['calls'] if begin<=c['begin'] and c['end']<=end]
    if len(calls)!=97 or len(memory['resizeChecks'])!=97:raise ValueError('Incomplete generated resize work')
    entries={e['milliseconds']:e for e in trace['events'] if e['label']=='memory.resize'};returns={r['call']:r for r in work['results']}
    counts={c['ordinal']:{} for c in work['calls']};base=trace['location']['main_base']+0xd510
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for call,generated in zip(calls,memory['resizeChecks']):
        entry=entries[call['begin']];actual=counts[call['ordinal']];model=generated['work'];expected=model['entries'];returned=returns[call['ordinal']]
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=generated['bytes']==entry['ax']+65536*entry['dx'] and generated['address']==entry['si']+16*entry['ds'];return_equal=generated['bytes']==returned['ax']+65536*returned['dx']
        results.append(dict(ordinal=call['ordinal'],bytes=generated['bytes'],address=generated['address'],instructions=model['instructions'],differences=differences,input_equal=input_equal,return_equal=return_equal,passed=generated['passed'] and input_equal and return_equal and not differences))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in ['heap.js','memory-resize-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        checks=page.evaluate('''()=>{
          const make=(size,padding=0)=>({heap:new OriginalHeap({blocks:[{address:16,size,flags:0x8000,padding},{address:16+size,size:64,flags:0,padding:0},{address:80+size,size:6,flags:0x4000,padding:0}],handles:[],search:16,closedArena:true})});
          const a=make(24),aw=OriginalMemoryResizeWork.resize(a,a.heap.at(16),17);
          const b=make(16),bw=OriginalMemoryResizeWork.resize(b,b.heap.at(16),17);
          const c=make(24),cw=OriginalMemoryResizeWork.resize(c,c.heap.at(16),11);
          const d=make(20),dw=OriginalMemoryResizeWork.resize(d,d.heap.at(16),11);
          const e=make(65560),ew=OriginalMemoryResizeWork.resize(e,e.heap.at(16),65537);
          let unsupported=false;try{const m=make(8);m.heap.at(24).flags=0x8000;OriginalMemoryResizeWork.resize(m,m.heap.at(16),90);}catch(e){unsupported=String(e).includes('pressure');}
          return [{name:'same rounded size preserves original padding',passed:a.heap.at(16).padding===0&&!aw.entries[0x7130]},{name:'growth recomputes padding after coalescing',passed:b.heap.at(16).size===24&&b.heap.at(16).padding===1&&bw.entries[0x7197]===1},{name:'shrink splits six-byte remainder',passed:c.heap.at(16).size===18&&c.heap.at(34).size===6},{name:'small remainder is retained as padding',passed:d.heap.at(16).size===20&&d.heap.at(16).padding===3},{name:'resize arithmetic crosses a word boundary',passed:e.heap.at(16).size===65544&&e.heap.at(16).padding===1},{name:'unreconstructed pressure is rejected',passed:unsupported}];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),calls=results,checks=checks,models=memory['models'],memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='97 successful intrinsic 70E8 resize paths derive work from continuous modeled block state, with matching native addresses, lengths and returned lengths. Nine earlier calls precede the initial fixture. Callee work, failed resize/growth paths, startup and full timing remain separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
