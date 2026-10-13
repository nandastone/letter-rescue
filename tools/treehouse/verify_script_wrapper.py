"""Compare generated wrapper continuations between original interpreter calls."""
from pathlib import Path
from collections import Counter
import argparse,bisect,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    for group in ['script_work','irq']:
        with (trace_path.parent/trace[group]['path']).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=trace[group]['sha256']:raise ValueError('Input digest differs')
    rows=[json.loads(s) for s in (trace_path.parent/trace['script_work']['path']).read_text().splitlines()]
    interrupts=[r['context'][0] for line in (trace_path.parent/trace['irq']['path']).read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    def classify(previous,row,repeated=False):
        if previous is None:return None,'initial incomplete context'
        if not repeated:
            lo=previous['last_instruction']+1;hi=row['first_instruction']
            if row['gap_count']!=hi-lo:raise ValueError('Gap differs from CPU counters')
            i=bisect.bisect_left(interrupts,lo)
            if i<len(interrupts) and interrupts[i]<=hi:return None,'interrupt within continuation'
        s=previous['after'];w=s['wrapper']
        if w[:5]!=row['before']['wrapper'][:5]:return None,'caller transition'
        if w[:2]!=[0x485d,trace['location']['main_base']//16]:return None,'other caller'
        if previous['result'] or (w[2] and s['display_count']==1):return None,'wrapper exit'
        if w[3]==70:return None,'interruptible animation input poll'
        if not w[5] and w[6]<32768 and w[6]==s['display_count']:return None,'activity overlay call'
        return dict(result=previous['result'],firstFrame=w[2],displayCount=s['display_count'],baseId=w[3],suppressCallback=w[5],callbackFrame=w[6]),None
    cache={};skipped=Counter();matching=Counter();failures=[];calls=0;instructions=0;previous=None
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/script-wrapper-work.js'))
        page.evaluate('base=>window.mainBase=base',trace['location']['main_base'])
        for row in rows:
            for prior,weight,repeated in [(previous,1,False),(row,row['repeats']-1,True)]:
                if not weight:continue
                calls+=weight;params,reason=classify(prior,row,repeated)
                if reason:skipped[reason]+=weight;continue
                key=json.dumps(params,separators=(',',':'))
                if key not in cache:
                    cache[key]=page.evaluate('''params=>{
                      const g=OriginalScriptWrapperWork.run(params),path=[];let next=g.next();
                      while(!next.done&&typeof next.value==='string'){
                        path.push(mainBase+parseInt(next.value.split(':')[1],16));next=g.next();
                      }
                      let hash=2166136261;for(const word of path)for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((word>>>shift)&255),16777619)>>>0;
                      return {path,hash,finished:next.done,result:next.value};
                    }''',params)
                actual=cache[key]
                if not actual['finished'] or actual['result']['done'] or len(actual['path'])!=row['gap_count'] or actual['hash']!=row['gap_hash'] or actual['path'][:128]!=row['gap_addresses']:
                    failures.append(dict(ordinal=row['ordinal'],repeated=repeated,params=params,actual=actual,expected=dict(count=row['gap_count'],hash=row['gap_hash'],path=row['gap_addresses'])));break
                matching['suppressed' if params['suppressCallback'] else 'callback check']+=weight;instructions+=weight*len(actual['path'])
            previous=row
            if failures:break
        checks=page.evaluate('''()=>{
          const drive=(params,input=0)=>{const g=OriginalScriptWrapperWork.run(params),calls=[],path=[];let next=g.next();
            while(!next.done){if(typeof next.value==='string')path.push(next.value);else calls.push(next.value.call);next=g.next(input);}return {result:next.value,calls,path};};
          const p={result:0,firstFrame:0,displayCount:2,baseId:24100,suppressCallback:0,callbackFrame:10};
          const a=drive({...p,result:1}),b=drive({...p,firstFrame:1,displayCount:1}),c=drive({...p,firstFrame:1});
          const d=drive({...p,baseId:70},1),e=drive({...p,baseId:70}),f=drive({...p,callbackFrame:2});
          const g=drive({...p,callbackFrame:65535}),h=drive({...p,suppressCallback:1,callbackFrame:2});
          return [
            {name:'script result exits wrapper',passed:a.result.reason==='script'&&a.calls.length===0},
            {name:'first-frame request stops after exactly one display',passed:b.result.reason==='first-frame'&&b.calls.length===0},
            {name:'first-frame request otherwise continues',passed:c.result.done===false},
            {name:'interruptible intro input clears callback then exits',passed:d.result.reason==='input'&&d.calls.join(',')==='input-poll,clear-animation-callback'},
            {name:'interruptible intro without input continues',passed:e.result.done===false&&e.calls.join(',')==='input-poll'},
            {name:'matching display invokes activity overlay',passed:f.result.done===false&&f.calls.join(',')==='activity-overlay'},
            {name:'negative callback frame bypasses overlay',passed:g.result.done===false&&g.calls.length===0&&g.path.includes('main:4eae')},
            {name:'suppression bypasses callback helper',passed:h.result.done===false&&h.calls.length===0&&!h.path.includes('main:4e9e')}
          ];
        }''');browser.close()
    report=dict(passed=not failures and calls==trace['script_work']['calls'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,calls=calls,matching=dict(matching),instructions=instructions,skipped=dict(skipped),generated_variants=len(cache),checks=checks,failures=failures,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/script-wrapper-work.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Complete ordered instruction paths for uninterrupted SCR wrapper continuations selected from caller arguments and state. IRQ delivery counters identify interrupted boundaries independently. Exact payload coalescing covers repeated continuations; initial/transition/overlay/IRQ intervals are explicitly uncomposed. Caller state remains an offline fixture; no runtime loop counts or timings come from captures.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
