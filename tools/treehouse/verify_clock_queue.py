"""Compare continuous queue state and primitive CPU budget changes with native."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    path=trace_path.parent/trace['pic']['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['pic']['sha256']:raise ValueError('PIC capture digest differs')
    initial_path=trace_path.parent/trace['pic']['initial_path']
    if hashlib.sha256(initial_path.read_bytes()).hexdigest()!=trace['pic']['initial_sha256']:raise ValueError('PIC initial state differs')
    initial=json.loads(initial_path.read_text())
    def batches():
        with path.open(encoding='utf-8') as f:
            while True:
                rows=list(itertools.islice(f,2000))
                if not rows:break
                yield [json.loads(row) for row in rows]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/clock-queue.js'))
        page.evaluate('''initial=>{
          window.clockQueue=new OriginalClockQueue(initial);
          window.clockReport={operations:0,externalBudgetInputs:0,kindCounts:{},failures:[]};
          window.clockCompare=(actual,expected)=>Object.fromEntries(Object.keys(expected).filter(k=>actual[k]!==expected[k]).map(k=>[k,{expected:expected[k],actual:actual[k]}]));
          const differences=clockCompare(clockQueue.snapshot(),initial.state);
          if(Object.keys(differences).length)clockReport.failures.push({phase:'initial',differences});
        }''',initial)
        for rows in batches():
            ok=page.evaluate('''rows=>{
              const q=clockQueue,r=clockReport;
              for(const row of rows){
                const ordinal=r.operations++;
                if(q.cycles!==row.before.cycles||q.left!==row.before.left||q.maximum!==row.before.maximum)r.externalBudgetInputs++;
                q.setCpuBudget(row.before);
                if(row.kind===6)q.servicing=false; // PIC_RunQueue leaves service mode before assigning the slice.
                let differences=clockCompare(q.snapshot(),row.before);
                if(Object.keys(differences).length){r.failures.push({ordinal,phase:'before',kind:row.kind,differences});return false;}
                try{
                  if(row.kind===1)q.add(row.handler,row.value,row.delay);
                  else if(row.kind===2)q.remove(row.handler);
                  else if(row.kind===3)q.remove(row.handler,row.value);
                  else if(row.kind===4)q.start();
                  else if(row.kind===5)q.service(row.handler,row.value,row.delay);
                  else if(row.kind===6)q.finish();
                  else if(row.kind===7)q.millisecond();
                  else throw new Error('Unknown primitive');
                }catch(e){r.failures.push({ordinal,phase:'operation',kind:row.kind,error:String(e)});return false;}
                differences=clockCompare(q.snapshot(),row.after);
                if(Object.keys(differences).length){r.failures.push({ordinal,phase:'after',kind:row.kind,differences});return false;}
                r.kindCounts[row.kind]=(r.kindCounts[row.kind]||0)+1;
                if(row.kind===4&&q.left>0)q.servicing=true;
              }
              return true;
            }''',rows)
            if not ok:break
        result=page.evaluate('()=>({...clockReport,finalState:clockQueue.snapshot()})')
        checks=page.evaluate('''()=>{
          const make=()=>new OriginalClockQueue({state:{cycles:500,left:500,maximum:1000,ticks:0,servicing:0,service_index:0},entries:[]});
          const a=make();a.add(1,10,.5);a.add(2,20,.5);a.add(1,30,.5);a.remove(1,10);
          const b=make();b.add(1,0,.1);
          const c=make();c.cycles=0;c.left=1000;c.servicing=true;c.serviceIndex=.25;c.add(1,0,.5);
          const d=make();d.cycles=0;d.left=1000;d.queue=[{handler:1,value:0,index:Math.fround(.0001)}];d.serviceIndexND=0;d.finish();
          const e=make();e.cycles=-1;e.left=1;const ready=e.start();
          const f=make();f.queue=[{handler:1,value:0,index:Math.fround(1.2)}];f.millisecond();
          let bad=false;try{make().setCpuBudget({cycles:0,left:0,maximum:0});}catch(e){bad=true;}
          return [
            {name:'equal-time insertion is stable and selective removal preserves order',passed:JSON.stringify(a.queue.map(e=>[e.handler,e.value]))==='[[2,20],[1,30]]'},
            {name:'earlier event returns current slice to the remaining budget',passed:b.cycles===0&&b.left===1000},
            {name:'event callbacks reschedule from the scheduled index',passed:c.queue[0].index===.75},
            {name:'positive sub-cycle deadline gets one cycle',passed:d.cycles===1&&d.left===999},
            {name:'exhausted millisecond includes dispatch-loop underflow',passed:!ready&&e.left===0&&e.cycles===0},
            {name:'millisecond shift keeps float-rounded event phase',passed:f.queue[0].index===Math.fround(Math.fround(1.2)-1)&&f.ticks===1&&f.left===1000},
            {name:'invalid cycle maximum rejected',passed:bad}
          ];
        }''');browser.close()
    report=dict(passed=not result['failures'] and result['operations']==trace['pic']['operations'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,**result,checks=checks,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/clock-queue.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),pic_sha256=trace['pic']['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Continuous event queue from one initial fixture. Every primitive compares the full ordered queue hash, head, count, float clock values, event-service state and resulting CPU budget. CPU budgets between primitives and event add/remove requests are observed external inputs. Guest instruction execution, event handlers, IRQ admission and live game integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
