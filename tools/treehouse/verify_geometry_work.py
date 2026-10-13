"""Compare resident geometry/memory work, outputs and independently executed clocks."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,video_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());video=json.loads(video_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    if trace['events']!=irq['events'] or trace['events']!=video['events']:raise ValueError('Independent fixture routes differ')
    meta=trace['geometry'];path=trace_path.parent/meta['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256'] or meta['partial_final_calls']:raise ValueError('Geometry stream incomplete or changed')
    rows=sorted((json.loads(s) for s in path.read_text().splitlines()),key=lambda r:r['ordinal'])
    if len(rows)!=meta['calls']:raise ValueError('Geometry call count differs')
    video_stream=video_path.parent/video['sprites']['path']
    if hashlib.sha256(video_stream.read_bytes()).hexdigest()!=video['sprites']['sha256']:raise ValueError('Video configuration fixture changed')
    configs={json.dumps({k:r[k] for k in ['video_delays','parts_total','parts_lines','lines_total']},sort_keys=True) for line in video_stream.read_text().splitlines() if (r:=json.loads(line))}
    if len(configs)!=1:raise ValueError('Video configuration changed during route')
    config=json.loads(next(iter(configs)))
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples']) for r in rows],irq,irq_path)
    irq_stream=irq_path.parent/irq['irq']['path']
    if hashlib.sha256(irq_stream.read_bytes()).hexdigest()!=irq['irq']['sha256']:raise ValueError('IRQ fixture changed')
    deliveries=[r['milliseconds'] for line in irq_stream.read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    skipped=Counter();results=[];modules=['geometry-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js']
    model_sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(content=model_sources[name].decode('utf-8'))
        for row in rows:
            clock=row['kind']!=7 and not any(row['begin']<=t<=row['end'] for t in deliveries)
            if not clock:skipped['clear wrapper requires pixel callee' if row['kind']==7 else 'IRQ during helper']+=1
            actual=page.evaluate('''({row,queueState,config,clockEnabled})=>{
              try{
                const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),assert=(test,message)=>{if(!test)throw new Error(message);},isRep=s=>s.call?.startsWith('rep-');
                function inputs(){
                  const memory=new Uint8Array(65536),length=row.args[2];
                  if(row.kind>=8){
                    if(row.kind===8)for(let i=0;i<length;i++)memory[(row.args[1]+i)&65535]=row.source_bytes[i];
                    for(let i=0;i<length;i++)memory[(row.args[0]+i)&65535]=row.before_bytes[i];
                    if(row.kind===8)for(let i=0;i<length;i++)assert(memory[(row.args[1]+i)&65535]===row.source_bytes[i],'Overlapping source fixture inconsistent');
                  }
                  return {a:row.a.slice(),b:row.b.slice(),out:row.before.slice(),surface:row.surface.slice(),memory,stack:row.kind===6?[row.b.slice()]:[]};
                }
                function generator(input){
                  const g=OriginalGeometryWork,{a,b,out,surface,memory,stack}=input;
                  switch(row.kind){
                    case 0:return g.offset(a,row.args[0],row.args[1],out);
                    case 1:return g.intersection(a,b,out);
                    case 2:return g.empty(a);
                    case 3:return g.union(a,b,out);
                    case 4:return g.localPoint(a,surface,out);
                    case 5:return g.clipPush(surface,(row.args[0]||row.args[1])?a:null,stack);
                    case 6:return g.clipPop(surface,stack);
                    case 7:return g.clear(row.args[0],a);
                    case 8:return g.nearCopy(memory,row.args[1],row.args[0],row.args[2]);
                    case 9:return g.nearFill(memory,row.args[0],row.args[2],row.args[1]);
                  }
                }
                function* compose(gen,includeChildren){
                  let n=gen.next();while(!n.done){const step=n.value;let answer;
                    if(typeof step==='string'||isRep(step))answer=yield step;
                    else{
                      let child;if(step.call==='point-local')child=OriginalGeometryWork.localPoint(step.point,step.surface);
                      else if(step.call==='rectangle-intersection')child=OriginalGeometryWork.intersection(step.a,step.b,step.out);
                      else if(step.call!=='rectangle-fill')throw new Error('Unknown geometry callee');
                      if(child){if(includeChildren)answer=yield* compose(child,true);else{let c=child.next();while(!c.done)c=child.next(isRep(c.value)?c.value.remaining:undefined);answer=c.value;}}
                    }
                    n=gen.next(answer);
                  }return n.value;
                }
                function checkOutput(input,result){
                  if([0,1,3,4].includes(row.kind))assert(equal(input.out.slice(0,row.kind===4?2:4),row.after.slice(0,row.kind===4?2:4)),'Rectangle output differs');
                  if(row.kind===1)assert(Number(result.nonempty)===row.result[0],'Intersection return differs');
                  if(row.kind===2)assert(Number(result)===row.result[0],'Empty return differs');
                  if(row.kind===5||row.kind===6)assert(equal(input.surface,row.after_surface),'Clip surface state differs');
                  if(row.kind>=8){assert(result===row.result[0],'Near memory return differs');for(let i=0;i<row.args[2];i++)assert(input.memory[(row.args[0]+i)&65535]===row.after_bytes[i],'Near output differs at '+i);}
                }
                const input=inputs(),counts={},samples=row.samples.filter(s=>[0x8415,0x7de9,0x098e,0x0992,0x09bc,0x09c0].includes(s.address));let hash=2166136261,dispatch=0;
                const gen=compose(generator(input),false);let n=gen.next();while(!n.done){let answer;const step=n.value;
                  if(typeof step==='string'){const at=parseInt(step.split(':')[1],16);counts[at]=(counts[at]||0)+1;for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((at>>>shift)&255),16777619)>>>0;}
                  else {const s=samples[dispatch++];assert(s&&s.address===step.address&&s.remaining===step.remaining,'Intrinsic REP operands differ');answer=Math.min(step.remaining,Math.max(1,s.budget));}
                  n=gen.next(answer);
                }
                assert(dispatch===samples.length,'Unused REP observations');assert(hash===row.path_hash,'Intrinsic ordered instructions differ');
                for(const key of new Set([...Object.keys(counts),...Object.keys(row.counts)]))assert((counts[key]||0)===(row.counts[key]||0),'Intrinsic count differs at '+(+key).toString(16));checkOutput(input,n.value);
                let execution=null;
                if(clockEnabled){
                  const state=inputs(),initial=row.samples[0],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:initial.left,maximum:initial.maximum});queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                  const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:config.video_delays,partsTotal:config.parts_total,partsLines:config.parts_lines,linesTotal:config.lines_total,partsLeft:initial.parts_left,linesDone:initial.lines_done}),clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q)});let sample=0;
                  const runner=new OriginalWorkRunner(compose(generator(state),true),{singleStrings:OriginalGeometryWork.singleStrings,onInstruction:(label,b)=>{
                    const at=parseInt(label.split(':')[1],16),expected=row.samples[sample];if(!expected||at!==expected.address)return;
                    const actual={budget:b.cycles,left:b.left,maximum:b.maximum,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                    for(const key of Object.keys(actual))assert(actual[key]===expected[key],'Clock '+key+' differs at '+at.toString(16)+': '+actual[key]+' != '+expected[key]);sample++;
                  }});
                  const end=clock.run(runner);assert(end.kind==='complete'&&sample===row.samples.length,'Incomplete clock execution');checkOutput(state,end.value);
                  execution={samples:sample,instructions:runner.instructions,strings:runner.strings,refills:clock.refills,events:clock.events};
                }
                return {passed:true,instructions:Object.values(counts).reduce((a,b)=>a+b,0),execution};
              }catch(e){return {passed:false,error:String(e)};}
            }''',dict(row=row,queueState=queues[row['ordinal']],config=config,clockEnabled=clock))
            results.append(dict(ordinal=row['ordinal'],kind=row['kind'],**actual))
            if not actual['passed']:break
        checks=page.evaluate('''()=>{
          const g=OriginalGeometryWork,drive=gen=>{let n=gen.next();while(!n.done){const s=n.value;let a;if(s.call?.startsWith('rep-'))a=s.remaining;else if(s.call==='point-local')a=drive(g.localPoint(s.point,s.surface));else if(s.call==='rectangle-intersection')a=drive(g.intersection(s.a,s.b));n=gen.next(a);}return n.value;},checks=[],eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
          for(const [name,a,b,want] of [['overlap',[0,0,10,10],[5,3,20,8],[5,3,10,8]],['horizontal empty',[0,0,10,2],[0,2,10,8],[0,0,0,0]],['vertical empty',[0,0,2,10],[2,0,10,10],[0,0,0,0]],['negative',[65530,65530,2,2],[65532,65532,4,4],[65532,65532,2,2]]]){
            const out=drive(g.intersection(a,b));checks.push({name:'intersection '+name,passed:eq(out.rect,want)});
            const alias=a.slice();drive(g.intersection(alias,b,alias));checks.push({name:'intersection aliases '+name,passed:eq(alias,want)});
          }
          const rect=[65535,32767,0,32768];drive(g.offset(rect,2,2,rect));checks.push({name:'offset wraps 16-bit words in place',passed:eq(rect,[1,32769,2,32770])});
          for(const length of [0,1,2,3,8,9,64])for(const offset of [100,101])for(const delta of [-2,-1,0,1,2,100]){
            const m=Uint8Array.from({length:65536},(_,i)=>(i*17+9)&255),want=m.slice(),dst=offset,src=offset+delta;let si=src,di=dst,n=length;
            if(n&&(di&1)){want[di++]=want[si++];n--;}
            for(let i=0;i<(n>>>1);i++){const a=want[si],b=want[si+1];want[di]=a;want[di+1]=b;si+=2;di+=2;}if(n&1)want[di]=want[si];
            drive(g.nearCopy(m,src,dst,length));checks.push({name:'near copy '+length+' dst '+offset+' delta '+delta,passed:m.every((v,i)=>v===want[i])});
          }
          for(const length of [0,1,2,3,8,9,64])for(const offset of [100,101,65535]){
            const m=new Uint8Array(65536),want=m.slice();for(let i=0;i<length;i++)want[(offset+i)&65535]=0x5a;drive(g.nearFill(m,offset,length,0x15a));checks.push({name:'near fill '+length+' dst '+offset,passed:m.every((v,i)=>v===want[i])});
          }
          const surface=[0,0,10,20,110,120,100,0,0,0,0,0,0,0,100,100],stack=[];drive(g.clipPush(surface,[20,30,40,50],stack));const once=surface.slice(12);drive(g.clipPush(surface,null,stack));const cleared=surface.slice(12);drive(g.clipPop(surface,stack));const restored=surface.slice(12);drive(g.clipPop(surface,stack));
          checks.push({name:'nested clip stack converts coordinates and restores null clipping',passed:eq(once,[10,10,30,30])&&eq(cleared,[0,0,0,0])&&eq(restored,once)&&eq(surface.slice(12),[0,0,100,100])&&!stack.length});
          const literalMemory=new Uint8Array(65536),literal=Uint8Array.from([1,2,3,4,5,6,7,8,9]),copy=g.nearCopy(literalMemory,0,101,9,{sourceBytes:literal});let n=copy.next();while(!n.done&&n.value.call!=='rep-move-words')n=copy.next();n=copy.next(1);
          const partial=literalMemory[101]===1&&literalMemory[102]===2&&literalMemory[103]===3&&literalMemory[104]===0;while(!n.done)n=copy.next(n.value.call?.startsWith('rep-')?n.value.remaining:undefined);
          checks.push({name:'literal local rectangle copy publishes partial words in shared data',passed:partial&&literal.every((v,i)=>literalMemory[101+i]===v)});
          const live=[0,0,100,100],target=g.wordSlice(live,0,4),intersection=g.intersection([5,10,20,30],[0,0,100,100],target);n=intersection.next();while(n.value!=='resident:83de')n=intersection.next();n=intersection.next();
          checks.push({name:'intersection updates shared clip words before return',passed:live[1]===10&&!n.done});
          return checks;
        }''');browser.close()
    report=dict(passed=len(results)==len(rows) and all(r['passed'] for r in results+checks),full_cpu_scheduling_parity=False,calls=len(rows),matching_calls=sum(r['passed'] for r in results),instructions=sum(r.get('instructions',0) for r in results),kinds=dict(Counter(r['kind'] for r in results)),clock_calls=sum(bool(r.get('execution')) for r in results),clock_samples=sum(r['execution']['samples'] for r in results if r.get('execution')),clock_skipped=dict(skipped),refills=sum(r['execution']['refills'] for r in results if r.get('execution')),failures=[r for r in results if not r['passed']],checks=checks,models={n:hashlib.sha256(model_sources[n]).hexdigest() for n in modules},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Intrinsic geometry/short memory calls compare generated outputs and ordered work. Separate clock execution composes point/intersection callees from one CPU/queue state per call. Clear wrappers and IRQ-containing calls are excluded from clock proof. Initial operands, surfaces, memory bytes and queues remain fixtures; full animation/live integration remains separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'checks':dict(total=len(checks),failures=[c for c in checks if not c['passed']])},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','video','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.video,a.control,a.output) else 1)
