"""Check generated periodic PIT phase against all queued timer events."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output,handler,counter):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted probe control')
    path=trace_path.parent/trace['pic']['path'];initial_path=trace_path.parent/trace['pic']['initial_path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['pic']['sha256']:raise ValueError('Corrupt PIC observations')
    if hashlib.sha256(initial_path.read_bytes()).hexdigest()!=trace['pic']['initial_sha256']:raise ValueError('Corrupt initial queue')
    initial=json.loads(initial_path.read_text());entry=[e for e in initial['entries'] if e['handler']==handler]
    if len(entry)!=1:raise ValueError('Expected one initial PIT event')
    rows=[]
    with path.open() as f:
        for line in f:
            if line.startswith(('{"kind":1,','{"kind":5,','{"kind":7,')):
                r=json.loads(line)
                if r['kind']==7 or r['handler']==handler:rows.append(dict(kind=r['kind'],delay=r['delay'],ticks=r['before']['ticks'],tickIndex=r['before']['tick_index'],milliseconds=r['before']['milliseconds']))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for filename in ['clock-queue.js','pit-clock.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        result=page.evaluate('''a=>{
          const pit=new OriginalPitClock({counter:a.counter,index:a.index});let ticks=a.ticks,pending=false,adds=0,shifts=0;const failures=[];
          for(let ordinal=0;ordinal<a.rows.length;ordinal++){
            const row=a.rows[ordinal];
            if(row.ticks!==ticks){failures.push({ordinal,error:'Millisecond differs'});break;}
            if(row.kind===7){pit.millisecond();ticks++;shifts++;}
            else if(row.kind===5){
              if(pending||pit.index!==row.delay||pit.index>row.tickIndex){failures.push({ordinal,error:'Scheduled timer phase differs',expected:pit.index,actual:row.delay,tickIndex:row.tickIndex});break;}
              pending=true;
            }else{
              if(!pending||row.delay!==pit.delay){failures.push({ordinal,error:'Timer reschedule differs',expected:pit.delay,actual:row.delay});break;}
              pit.fire();adds++;pending=false;
            }
          }
          return {failures,events:pit.events,reschedules:adds,milliseconds:shifts,pending,delay:pit.delay,finalIndex:pit.index};
        }''',dict(counter=counter,index=entry[0]['index'],ticks=initial['state']['ticks'],rows=rows));browser.close()
    timer_calls=len(trace['work']['timer_states'])
    report=dict(passed=not result['failures'] and not result['pending'] and result['events']==timer_calls and result['reschedules']==timer_calls,**result,timer_calls=timer_calls,handler_fixture=handler,counter_fixture=counter,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in ['clock-queue.js','pit-clock.js']},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),pic_sha256=trace['pic']['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Constant-counter PIT0 scheduled phase evolves from one initial queue index using native float rounding. Every timer service and reschedule is compared, with no phase resets. Counter and handler identity are explicit fixtures; millisecond/service driving, IRQ admission and initial hardware programming remain outside this component.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--handler',type=int,required=True);p.add_argument('--counter',type=int,required=True);a=p.parse_args()
    sys.exit(0 if verify(a.trace,a.control,a.output,a.handler,a.counter) else 1)
