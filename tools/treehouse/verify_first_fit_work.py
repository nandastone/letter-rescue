"""Compare first-fit work from continuous generated state with native execution."""
from pathlib import Path
import argparse,bisect,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False);memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted memory evidence')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated memory model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observers differ')
    if work['routine']!='resident:6D47' or len(work['calls'])!=169:raise ValueError('Incomplete first-fit capture')
    begin,end=scene['heap'][0]['milliseconds'],scene['heap'][-1]['milliseconds'];calls=[c for c in work['calls'] if begin<=c['begin'] and c['end']<=end]
    if len(calls)!=159 or len(memory['allocationChecks'])!=159:raise ValueError('Incomplete generated allocations')
    entries=[e for e in trace['events'] if e['label']=='memory.far.allocate'];entry_times=[e['milliseconds'] for e in entries]
    returns=[e for e in trace['events'] if e['label']=='memory.far.allocate.return'];return_times=[e['milliseconds'] for e in returns]
    counts={c['ordinal']:{} for c in work['calls']};base=trace['location']['main_base']+0xd510;results=[]
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    for call,generated in zip(calls,memory['allocationChecks']):
        entry=entries[bisect.bisect_right(entry_times,call['begin'])-1];returned=returns[bisect.bisect_left(return_times,call['end'])]
        if not entry['milliseconds']<=call['begin']<=call['end']<=returned['milliseconds']:raise ValueError('Allocation boundaries differ')
        actual=counts[call['ordinal']];model=generated['work'];expected=model['entries']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=generated['bytes']==entry['ax']+65536*entry['dx'];return_equal=generated['address']==returned['si']+16*returned['ds']
        results.append(dict(ordinal=call['ordinal'],bytes=generated['bytes'],address=generated['address'],instructions=model['instructions'],differences=differences,input_equal=input_equal,return_equal=return_equal,passed=generated['passed'] and input_equal and return_equal and not differences))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in ['heap.js','heap-instructions.js','memory-copy-work.js','heap-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        checks=page.evaluate('''()=>{
          const make=(sizes,search=16)=>{let at=16;const blocks=sizes.map(([size,flags=0])=>{const b={address:at,size,flags,padding:0};at+=size;return b;});blocks.push({address:at,size:6,flags:0x4000,padding:0});return new OriginalHeapWork({blocks,handles:[],search,closedArena:true});};
          const a=make([[32],[8,0x8000]],48),ar=a.firstFit(10);
          const b=make([[12],[14],[8,0x8000]]),br=b.firstFit(18);
          const c=make([[20]]),cr=c.firstFit(11),d=make([[24]]),dr=d.firstFit(11);
          const e=make([[16],[8,0x8000],[32]]),er=e.firstFit(20),f=make([[65560]]),fr=f.firstFit(65537);
          let rejected=false;try{make([[8,0x8000]]).firstFit(20);}catch(e){rejected=String(e).includes('growth/eviction');}
          return [{name:'search wraps from occupied tail to heap start',passed:ar.address===16&&a.entries[0x6de4]===1},{name:'adjacent holes coalesce before fitting',passed:br.address===16&&br.size===26&&b.blocks.length===3},{name:'remainder under six bytes is consumed',passed:cr.size===20&&cr.padding===3},{name:'six-byte remainder becomes free block',passed:dr.size===18&&d.at(34).size===6},{name:'too-small hole is skipped',passed:er.address===40},{name:'size arithmetic crosses a 16-bit boundary',passed:fr.size===65544&&fr.padding===1},{name:'unreconstructed memory pressure fails explicitly',passed:rejected}];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),calls=results,checks=checks,models=memory['models'],memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='159 first-fit calls derive work from continuous modeled heap state and match native arguments, allocation addresses and instruction paths. Ten earlier calls precede the initial fixture. Startup, pressure/growth/eviction paths and elapsed-time integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
