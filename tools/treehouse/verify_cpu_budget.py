"""Verify normal-run and supported callback budget arithmetic against native."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def callback_kind(description,begin,end):
    if description=='Mouse' and begin['ax']==3:return 'mouse-position'
    if description=='DOS Int 21':
        if begin['ax']==0x0c06 and begin['dx']&255==255:return 'keyboard-poll'
        if begin['ax']==0x4200:return 'file-seek'
        if begin['ax']>>8==0x3f:
            if begin['cx']!=end['ax']:raise ValueError('File read did not return all requested bytes')
            return 'file-read'
    if description=='Int 15 Bios' and begin['ax']==0x91f0:return 'bios-device-post'
    fixed={'IRQ 0 Clock':'bios-clock','Int 1c Timer':'bios-user-timer','int 74':'mouse-irq','int 74 ret':'mouse-return','mouse uir ret':'mouse-user-return'}
    if description in fixed:return fixed[description]
    raise ValueError('Unknown callback function: '+str((description,begin['ax'])))


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted CPU probe control')
    path=trace_path.parent/trace['cpu_runs']['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['cpu_runs']['sha256']:raise ValueError('CPU observations differ')
    def batches():
        stack=[];batch=[];count=0
        with path.open() as f:
            for ordinal,line in enumerate(f):
                e=json.loads(line);count+=1
                if e['kind'] in [1,3]:stack.append(e);continue
                if not stack:raise ValueError('Unpaired CPU boundary')
                begin=stack.pop()
                if stack or e['kind']!=begin['kind']+1 or e['id']!=begin['id']:raise ValueError('Unexpected nested or mismatched CPU boundary')
                state=[begin[k] for k in ['cycles','left','maximum','io']];expected=[e[k] for k in ['cycles','left','maximum','io']]
                if e['kind']==2:
                    if e['id']!=1 or 'credits' not in e:raise ValueError('Unobserved decoder or stack-segment credits')
                    mode='callback' if e['result']>0 else 'exhausted' if e['cycles']<0 else 'early'
                    costs=[e[k]-begin[k] for k in ['instructions','strings','credits','io']]
                    batch.append([ordinal,0,state,expected,costs,mode])
                else:
                    if e['instructions']!=begin['instructions'] or e['strings']!=begin['strings'] or e['credits']!=begin['credits']:raise ValueError('Callback executed unmodeled nested guest code')
                    kind=callback_kind(trace['cpu_runs']['callback_descriptions'].get(str(e['id'])),begin,e)
                    batch.append([ordinal,1,state,expected,begin['cx'],kind])
                if len(batch)==4000:yield batch;batch=[]
        if stack or count!=trace['cpu_runs']['events']:raise ValueError('Incomplete CPU boundaries')
        if batch:yield batch
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for filename in ['resource-work.js','cpu-budget.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        page.evaluate('''()=>{window.budgetReport={cpuRuns:0,callbacks:0,matching:0,instructions:0,stringIterations:0,stackSegmentCredits:0,ioDebit:0,callbackKinds:{},failures:[]};}''')
        for batch in batches():
            page.evaluate('''rows=>{
              const r=budgetReport;
              for(const [ordinal,type,s,expected,work,kind] of rows){
                const state={cycles:s[0],left:s[1],maximum:s[2],io:s[3]};let actual;
                if(!type){
                  actual=OriginalCpuBudget.normalRun(state,{instructions:work[0],strings:work[1],credits:work[2],ioDebit:work[3],exit:kind});
                  r.cpuRuns++;r.instructions+=work[0];r.stringIterations+=work[1];r.stackSegmentCredits+=work[2];r.ioDebit+=work[3];
                }else{
                  actual=OriginalCpuBudget.callback(kind,state,{bytes:work});r.callbacks++;r.callbackKinds[kind]=(r.callbackKinds[kind]||0)+1;
                }
                const result=[actual.cycles,actual.left,actual.maximum,actual.io];
                if(result.every((v,i)=>v===expected[i]))r.matching++;
                else if(r.failures.length<30)r.failures.push({ordinal,type,kind,expected,actual:result,state,work});
              }
            }''',batch)
        result=page.evaluate('()=>budgetReport')
        checks=page.evaluate('''()=>{
          const make=cycles=>new OriginalCpuBudget({cycles,left:0,maximum:10000,io:0});
          const a=make(0),dispatched=a.dispatch();
          const b=make(1);b.dispatch();b.stackSegmentCredit();const atomic=b.dispatch();
          const c=make(5),read=c.port('read');
          const d=make(100),write=d.port('write');
          const e=make(-1),negative=e.port('read');
          const f=make(0),more=f.stringIteration();
          let rejected=false;try{OriginalCpuBudget.callback('unknown',{cycles:10,left:0,maximum:10000});}catch(e){rejected=true;}
          return [
            {name:'failed dispatch check still decrements budget',passed:!dispatched&&a.cycles===-1},
            {name:'stack segment credit permits the following instruction',passed:atomic&&b.cycles===0},
            {name:'port read clamps to remaining budget',passed:read===5&&c.cycles===0&&c.io===5},
            {name:'port write uses integer divisor 1365',passed:write===7&&d.cycles===93},
            {name:'negative I/O budget follows original signed clamp',passed:negative===-1&&e.cycles===0&&e.io===-1},
            {name:'string iteration can overrun the dispatch budget',passed:!more&&f.cycles===-1},
            {name:'unknown callback fails explicitly',passed:rejected}
          ];
        }''');browser.close()
    report=dict(passed=not result['failures'] and result['matching']==result['cpuRuns']+result['callbacks'] and 2*result['matching']==trace['cpu_runs']['events'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,**result,checks=checks,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in ['resource-work.js','cpu-budget.js']},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),cpu_sha256=trace['cpu_runs']['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Normal CPU-run budget arithmetic and supported callback budget changes. Instruction/string/stack-credit counts, I/O debit and exit mode remain explicit observed work inputs. Callback kinds and requested read lengths come from observed arguments; all full-read lengths are checked against native results. This does not generate instruction paths, IRQ admission, callback register/RAM effects or a live execution schedule.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
