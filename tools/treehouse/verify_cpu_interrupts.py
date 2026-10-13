"""Compose continuous PIC state with normal CPU work and callback budgets."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_cpu_budget import callback_kind

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    for group in ['irq','cpu_runs']:
        with (trace_path.parent/trace[group]['path']).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=trace[group]['sha256']:raise ValueError('Observation digest differs')
    initial_path=trace_path.parent/trace['irq']['initial_path']
    if hashlib.sha256(initial_path.read_bytes()).hexdigest()!=trace['irq']['initial_sha256']:raise ValueError('Initial PIC differs')
    irq=[json.loads(s) for s in (trace_path.parent/trace['irq']['path']).read_text().splitlines()]
    if len(irq)!=trace['irq']['operations']:raise ValueError('IRQ count differs')
    def batches():
        batch=[];serial=0;index=0;begin=None;count=0
        with (trace_path.parent/trace['cpu_runs']['path']).open() as f:
            for ordinal,line in enumerate(f):
                e=json.loads(line);count+=1
                if e['kind'] in [1,3]:
                    if begin is not None:raise ValueError('Nested CPU boundary')
                    begin=e
                    if e['kind']==1:
                        serial+=1
                        while index<len(irq) and irq[index]['context'][4]<serial:
                            row=irq[index]
                            if row['context'][3]!=0:raise ValueError('Missed CPU interrupt operation')
                            batch.append([0,index,row]);index+=1
                    continue
                if begin is None or e['kind']!=begin['kind']+1 or e['id']!=begin['id']:raise ValueError('Unpaired CPU boundary')
                state=[begin[k] for k in ['cycles','left','maximum','io']];expected=[e[k] for k in ['cycles','left','maximum','io']]
                if e['kind']==2:
                    if e['id']!=1:raise ValueError('Unsupported decoder')
                    inside=[];cursor=[begin[k] for k in ['instructions','strings','credits','io']]
                    while index<len(irq) and irq[index]['context'][4]==serial and irq[index]['context'][3]==1:
                        row=irq[index];at=row['context'][:3]+[row['io']]
                        inside.append([index,[a-b for a,b in zip(at,cursor)],row]);cursor=at;index+=1
                    tail=[e[k]-cursor[i] for i,k in enumerate(['instructions','strings','credits','io'])]
                    mode='callback' if e['result']>0 else 'exhausted' if e['cycles']<0 else 'early'
                    batch.append([1,ordinal,state,expected,inside,tail,mode])
                else:
                    if any(e[k]!=begin[k] for k in ['instructions','strings','credits']):raise ValueError('Callback executes nested guest work')
                    if index<len(irq) and irq[index]['context'][3]==2 and irq[index]['context'][4]==serial:raise ValueError('Callback controller operation needs explicit composition')
                    kind=callback_kind(trace['cpu_runs']['callback_descriptions'].get(str(e['id'])),begin,e)
                    batch.append([2,ordinal,state,expected,begin['cx'],kind])
                begin=None
                if len(batch)>=3000:yield batch;batch=[]
        if begin is not None or count!=trace['cpu_runs']['events']:raise ValueError('Incomplete CPU boundaries')
        for i in range(index,len(irq)):
            if irq[i]['context'][3]!=0:raise ValueError('Unconsumed CPU interrupt operation')
            batch.append([0,i,irq[i]])
        if batch:yield batch
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['resource-work.js','cpu-budget.js','interrupt-controller.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        page.evaluate('''initial=>{
          window.q=new OriginalInterruptController(initial);
          window.r={cpuRuns:0,callbacks:0,matching:0,controllerOperations:0,insideCpuOperations:0,deliveries:0,budgetTransfers:0,failures:[]};
          window.same=(a,b)=>Object.keys(b).every(k=>typeof b[k]==='object'?same(a[k],b[k]):a[k]===b[k]);
          window.work=w=>({instructions:w[0],strings:w[1],credits:w[2],ioDebit:w[3]});
          window.state=s=>({cycles:s[0],left:s[1],maximum:s[2],io:s[3]});
          window.controllerOperation=(ordinal,row,budget)=>{
            q.setCpu(budget?{cycles:budget.cycles,left:budget.left,interrupt_enabled:row.before.interrupt_enabled,trap:row.before.trap}:row.before);
            if(!same(q.snapshot(),row.before))throw new Error('Controller before state differs at '+ordinal+': '+JSON.stringify(q.snapshot()));
            const vector=budget?budget.interrupt(q,{kind:row.kind,arg:row.arg,value:row.value,interrupt_enabled:row.before.interrupt_enabled,trap:row.before.trap}):q.apply(row.kind,row.arg,row.value);
            if(!same(q.snapshot(),row.after)||vector!==row.vector)throw new Error('Controller after state/vector differs at '+ordinal);
            r.controllerOperations++;if(budget)r.insideCpuOperations++;if(vector>=0)r.deliveries++;
            if(q.left!==row.before.left)r.budgetTransfers++;
          };
        }''',json.loads(initial_path.read_text()))
        for batch in batches():
            ok=page.evaluate('''rows=>{
              for(const row of rows){
                try{
                  const [type,ordinal,s,expected]=row;
                  if(type===0){controllerOperation(ordinal,s);continue;}
                  let actual;
                  if(type===1){
                    const b=new OriginalCpuBudget(state(s));
                    for(const [index,cost,operation] of row[4]){b.consume(work(cost));controllerOperation(index,operation,b);}
                    b.consume(work(row[5]));actual=b.finish(row[6]);r.cpuRuns++;
                  }else{actual=OriginalCpuBudget.callback(row[5],state(s),{bytes:row[4]});r.callbacks++;}
                  const result=[actual.cycles,actual.left,actual.maximum,actual.io];
                  if(result.every((v,i)=>v===expected[i]))r.matching++;
                  else {r.failures.push({ordinal,type,expected,actual:result,row});return false;}
                }catch(e){r.failures.push({error:String(e),row});return false;}
              }
              return true;
            }''',batch)
            if not ok:break
        result=page.evaluate('()=>r');browser.close()
    report=dict(passed=not result['failures'] and 2*result['matching']==trace['cpu_runs']['events'] and result['controllerOperations']==trace['irq']['operations'],full_cpu_scheduling_parity=False,**result,models={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in ['resource-work.js','cpu-budget.js','interrupt-controller.js']},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Continuous PIC state and generated budget transfers composed with observed CPU work segments. All normal-run/callback exit budgets and controller operations compared; no recorded transfer flag or per-operation controller reset. Instruction/string/credit/I/O counts, operation order, flags and CPU-run initial budgets remain observed fixtures. Guest execution, interrupt stack entry and live scheduling remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
