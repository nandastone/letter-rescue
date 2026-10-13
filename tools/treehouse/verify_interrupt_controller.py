"""Compare continuous dual PIC state and interrupt delivery with native operations."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    paths={k:trace_path.parent/trace['irq'][k] for k in ['path','initial_path']}
    for key,path in paths.items():
        with path.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=trace['irq']['sha256' if key=='path' else 'initial_sha256']:raise ValueError('IRQ capture digest differs')
    initial=json.loads(paths['initial_path'].read_text())
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/interrupt-controller.js'))
        page.evaluate('''initial=>{
          window.controller=new OriginalInterruptController(initial);
          window.irqReport={operations:0,deliveries:0,kindCounts:{},vectors:{},budgetTransfers:[],failures:[]};
          window.compareIrq=(a,b,path='')=>{
            let differences=[];
            for(const k of Object.keys(b)){
              const name=path?path+'.'+k:k;
              if(typeof b[k]==='object')differences.push(...compareIrq(a[k],b[k],name));
              else if(a[k]!==b[k])differences.push({field:name,expected:b[k],actual:a[k]});
            }
            return differences;
          };
        }''',initial)
        with paths['path'].open() as f:
            while True:
                batch=[json.loads(s) for s in itertools.islice(f,2000)]
                if not batch:break
                ok=page.evaluate('''rows=>{
                  const q=controller,r=irqReport;
                  for(const row of rows){
                    const ordinal=r.operations++;q.setCpu(row.before);
                    let differences=compareIrq(q.snapshot(),row.before);
                    if(differences.length){r.failures.push({ordinal,phase:'before',differences,row});return false;}
                    let vector;
                    try{vector=q.apply(row.kind,row.arg,row.value);}
                    catch(e){r.failures.push({ordinal,phase:'operation',error:String(e),row});return false;}
                    differences=compareIrq(q.snapshot(),row.after);
                    if(vector!==row.vector)differences.push({field:'vector',expected:row.vector,actual:vector});
                    if(differences.length){r.failures.push({ordinal,phase:'after',differences,row});return false;}
                    r.kindCounts[row.kind]=(r.kindCounts[row.kind]||0)+1;
                    if(vector>=0){r.deliveries++;r.vectors[vector]=(r.vectors[vector]||0)+1;}
                    if(q.left!==row.before.left)r.budgetTransfers.push({ordinal,kind:row.kind,arg:row.arg,value:row.value,context:row.context,milliseconds:row.milliseconds,cyclesBefore:row.before.cycles,cyclesAfter:q.cycles,leftBefore:row.before.left,leftAfter:q.left});
                  }
                  return true;
                }''',batch)
                if not ok:break
        result=page.evaluate('()=>({...irqReport,finalState:controller.snapshot()})');browser.close()
    report=dict(passed=not result['failures'] and result['operations']==trace['irq']['operations'],full_cpu_scheduling_parity=False,**result,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/interrupt-controller.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_sha256=trace['irq']['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Continuous controller state from one initial fixture; full before/after states and delivered vectors compared. CPU budgets, interrupt-enable/trap flags and controller operation requests remain observed external inputs. Guest interrupt entry, generated requests and live integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
