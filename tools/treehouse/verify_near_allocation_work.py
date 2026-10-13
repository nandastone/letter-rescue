"""Compare near allocation work derived from continuous modeled state."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False);memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted generated memory')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    if work['routine']!='resident:003D+0590':raise ValueError('Missing near allocation profile')
    begin,end=scene['heap'][0]['milliseconds'],scene['heap'][-1]['milliseconds'];calls=[c for c in work['calls'] if begin<=c['begin'] and c['end']<=end]
    if len(calls)!=237 or len(memory['nearChecks'])!=237:raise ValueError('Incomplete generated near allocations')
    counts={c['ordinal']:{} for c in work['calls']};base=trace['location']['main_base']+0xd510;returns={r['call']:r for r in work['results']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for call,generated in zip(calls,memory['nearChecks']):
        model=generated['work'];actual=counts[call['ordinal']];expected=model['entries']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=generated['bytes']==call['stack'][2];return_equal=generated['pointer']==returns[call['ordinal']]['ax'];strings=actual.get(str(0x05c3),0)+actual.get(str(0x05d5),0)
        results.append(dict(ordinal=call['ordinal'],bytes=generated['bytes'],pointer=generated['pointer'],instructions=model['instructions'],string_iterations=model['stringIterations'],differences=differences,input_equal=input_equal,return_equal=return_equal,passed=generated['passed'] and input_equal and return_equal and strings==model['stringIterations'] and not differences))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in ['near-heap.js','near-heap-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        checks=page.evaluate('''()=>{
          const make=(rows,search=100)=>{let at=100;const blocks=rows.map(([size,free])=>{const b={address:at,size,free};at+=size+2;return b;});blocks.push({address:at,size:65534,free:false});return new OriginalNearHeapWork({blocks,start:100,search,end:at});};
          const a=make([[10,true],[8,false],[6,false]],122),ap=a.allocate(4);
          const b=make([[2,true],[6,true],[8,false]]),bp=b.allocate(9);
          const c=make([[8,true]]),cp=c.allocate(5);
          const d=make([[8,true]]),dp=d.allocate(8);
          const e=make([[8,true]]),ep=e.allocate(0);
          const f=make([[2,true],[4,false],[12,true]]),fp=f.allocate(10);
          let rejected=false;try{make([[8,false]]).allocate(4);}catch(e){rejected=String(e).includes('growth/reclamation');}
          return [{name:'search wraps to earlier free block',passed:ap===102&&a.entries[0x05a8]===1},{name:'adjacent holes coalesce with their header bytes',passed:bp===102&&b.at(100).size===10&&b.entries[0x05da]===1},{name:'odd payload rounds up and leaves zero-size free block',passed:cp===102&&c.at(100).size===6&&c.at(108).size===0&&c.at(108).free},{name:'exact fit creates no new header',passed:dp===102&&d.blocks.length===2},{name:'zero payload still consumes an allocation header',passed:ep===102&&e.at(100).size===0&&e.at(102).free},{name:'small hole followed by allocation is skipped',passed:fp===112&&f.at(110).size===10},{name:'unreconstructed growth fails explicitly',passed:rejected}];
        }''');browser.close()
    report=dict(passed=all(c['passed'] for c in results+checks),matching_calls=sum(c['passed'] for c in results),instructions=sum(c['instructions'] for c in results),string_iterations=sum(c['string_iterations'] for c in results),calls=results,checks=checks,models=memory['models'],memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='237 near allocations use continuous modeled near-heap state, with matching native arguments, returned pointers, instruction paths and header reads. Earlier/later calls outside the initial/final fixtures, growth/reclamation and full CPU scheduling remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[c for c in results if not c['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
