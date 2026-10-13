"""Generate copy-loop CPU budgets from one initial budget, without per-REP resets."""
from pathlib import Path
from collections import Counter
import argparse,copy,gzip,hashlib,json,struct,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def initial_queues(rows,trace,path,*,tick_order=False):
    """Replay only past queue mutations to construct explicit initial fixtures."""
    meta=trace['pic'];initial_path=path.parent/meta['initial_path'];stream_path=path.parent/meta['path']
    if hashlib.sha256(initial_path.read_bytes()).hexdigest()!=meta['initial_sha256']:raise ValueError('Initial PIC digest differs')
    with stream_path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=meta['sha256']:raise ValueError('PIC stream digest differs')
    initial=json.loads(initial_path.read_text());queue=initial['entries'];state=initial['state'];result={}
    # An exhausted instruction can place FullIndex just beyond the next tick,
    # then the millisecond reset moves it backwards. Device entries at that
    # boundary must compare the integer tick before the fractional timestamp.
    key=lambda s:(s['ticks'],s['milliseconds']) if tick_order else s['milliseconds']
    targets=iter(sorted((key(r['slices'][0]),r['ordinal']) for r in rows if r['slices']));target=next(targets,None)
    f32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]
    def save():
        result[target[1]]=dict(state=copy.deepcopy(state),entries=copy.deepcopy(queue))
    with stream_path.open() as f:
        for line in f:
            row=json.loads(line)
            while target and target[0]<key(row['before']):
                save();target=next(targets,None)
            if target is None:break
            k=row['kind']
            if k==1:
                index=f32(row['delay']+(row['before']['service_index'] if row['before']['servicing'] else row['before']['tick_index']))
                at=next((i for i,e in enumerate(queue) if e['index']>index),len(queue));queue.insert(at,dict(handler=row['handler'],value=row['value'],index=index))
            elif k in [2,3]:queue=[e for e in queue if e['handler']!=row['handler'] or (k==3 and e['value']!=row['value'])]
            elif k==5:
                if not queue or queue[0]!=dict(handler=row['handler'],value=row['value'],index=row['delay']):raise ValueError('PIC past replay head differs')
                queue.pop(0)
            elif k==7:
                for e in queue:e['index']=f32(e['index']-1)
            state=row['after']
            if len(queue)!=state['count']:raise ValueError('PIC past replay count differs')
    if target is not None:raise ValueError('Missing queue initial context')
    return result


def verify(trace_path,irq_path,control_path,output,clock=False):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('IRQ fixture route instruction events differ')
    for parent,meta in [(trace_path,trace['blits']),(irq_path,irq['irq'])]:
        if hashlib.sha256((parent.parent/meta['path']).read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Input digest differs')
    deliveries=[r['milliseconds'] for line in (irq_path.parent/irq['irq']['path']).read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    rows=[json.loads(s) for s in (trace_path.parent/trace['blits']['path']).read_text().splitlines()];skipped=Counter();results=[]
    queues=initial_queues(rows,irq,irq_path) if clock else {}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['cpu-budget.js','surface-copy-work.js','work-runner.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        if clock:
            for name in ['clock-queue.js','execution-clock.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        for row in rows:
            if not row['slices']:skipped['no copy-loop REP']+=1;continue
            if any(row['begin']<=t<=row['end'] for t in deliveries):skipped['IRQ within complete copy call']+=1;continue
            payload=gzip.decompress((trace_path.parent/row['pixels']['path']).read_bytes())
            if hashlib.sha256(payload).hexdigest()!=row['pixels']['sha256']:raise ValueError('Pixel fixture digest differs')
            a=row['source_size'];b=a+row['destination_size'];inputs={k:row[k] for k in ['mode','context','source_id','destination_id','source','destination','source_rect','destination_rect','source_rows','destination_rows']};inputs.update(sourcePixels=list(payload[:a]),beforePixels=list(payload[a:b]))
            result=page.evaluate('''({input,initial,clockMode,queueState,video})=>{
              try{
                const g=OriginalSurfaceCopyWork.run(input);let next=g.next();
                while(!next.done&&!['resident:9c01','resident:9bf6'].includes(next.value))next=g.next();
                if(next.done)throw new Error('No first REP reached');
                const slices=[],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:clockMode?initial.left:0,maximum:clockMode?initial.maximum:10000});let clock,vga;
                if(clockMode){
                  queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                  const queue=new OriginalClockQueue(queueState);
                  vga=new OriginalVgaEventWork({...video,partsLeft:initial.parts_left,linesDone:initial.lines_done});
                  clock=new OriginalExecutionClock({queue,cpu,onEvent:(event,q)=>vga.service(event,q)});
                }
                const runner=new OriginalWorkRunner(g,{first:next,singleStrings:new Set(['resident:9c05','resident:9bfc']),onInstruction:(at,b)=>{
                  if(['resident:9c01','resident:9bf6'].includes(at)){
                    const row={address:parseInt(at.split(':')[1],16),budget:b.cycles};
                    if(clockMode)Object.assign(row,{left:b.left,maximum:b.maximum,ticks:clock.queue.ticks,milliseconds:clock.state().milliseconds,parts_left:vga.partsLeft,lines_done:vga.linesDone});
                    slices.push(row);
                  }
                }});
                const stop=clockMode?clock.run(runner):runner.runSlice(cpu);
                if(stop.kind==='call'&&stop.action.call!=='cursor-restore')throw new Error('Unexpected guest callee in copy loop');
                return {stop:stop.kind,slices,instructions:runner.instructions,strings:runner.strings,final:cpu.snapshot(),refills:clock?.refills||0,milliseconds:clock?.milliseconds||0,events:clock?.events||[]};
              }catch(e){return {error:String(e)};}
            }''',dict(input=inputs,initial=row['slices'][0],clockMode=clock,queueState=queues.get(row['ordinal']),video=dict(delays=row.get('video_delays'),partsTotal=row.get('parts_total'),partsLines=row.get('parts_lines'),linesTotal=row.get('lines_total'))))
            if result.get('stop')=='exhausted':skipped['copy requires queue/CPU refill']+=1;continue
            fields=['address','budget']+(['left','maximum','ticks','milliseconds','parts_left','lines_done'] if clock else [])
            expected=[{k:s[k] for k in fields} for s in row['slices']]
            passed='error' not in result and result['slices']==expected
            results.append(dict(ordinal=row['ordinal'],passed=passed,**result,expected=expected if not passed else None))
            if not passed:break
        checks=page.evaluate('''()=>{
          let written=0;const g=(function*(){let left=3;do{yield 'rep';const n=yield {call:'rep-move-words',remaining:left};written+=2*n;left-=n;}while(left);yield 'tail';return 7;})();
          const cpu=new OriginalCpuBudget({cycles:2,left:0,maximum:10000}),runner=new OriginalWorkRunner(g),a=runner.runSlice(cpu),partial=written===2&&cpu.cycles===-1;
          cpu.cycles=4;const b=runner.runSlice(cpu);
          const zero=new OriginalWorkRunner((function*(){yield 'rep';yield {call:'rep-move-words',remaining:0};return 1;})()),z=new OriginalCpuBudget({cycles:2,left:0,maximum:10000}),zc=zero.runSlice(z);
          const one=new OriginalWorkRunner((function*(){yield 'lodsb';yield 'next';})(),{singleStrings:new Set(['lodsb'])}),o=new OriginalCpuBudget({cycles:1,left:0,maximum:10000}),oc=one.runSlice(o);
          const call=new OriginalWorkRunner((function*(){yield 'call';const n=yield {call:'child'};yield 'return';return n;})()),c=new OriginalCpuBudget({cycles:4,left:0,maximum:10000}),cc=call.runSlice(c);call.resume(42);const cr=call.runSlice(c);
          return [
            {name:'REP suspends with partial writes before refill',passed:a.kind==='exhausted'&&partial},
            {name:'refill resumes same pending instruction',passed:b.kind==='complete'&&b.value===7&&written===6&&runner.instructions===3&&runner.strings===3&&cpu.cycles===0},
            {name:'zero-count REP costs dispatch only',passed:zc.kind==='complete'&&z.cycles===1&&zero.strings===0},
            {name:'single string still executes with zero post-dispatch budget',passed:oc.kind==='exhausted'&&o.cycles===-2&&one.strings===1},
            {name:'guest call suspension preserves return and CPU budget',passed:cc.kind==='call'&&cr.value===42&&c.cycles===2}
          ];
        }''');browser.close()
    report=dict(passed=bool(results) and all(r['passed'] for r in results+checks) and len(results)+sum(skipped.values())==len(rows),full_cpu_scheduling_parity=False,matching_calls=sum(r['passed'] for r in results),generated_rep_budgets=sum(len(r.get('slices',[])) for r in results),instructions=sum(r.get('instructions',0) for r in results),strings=sum(r.get('strings',0) for r in results),skipped=dict(skipped),failures=[r for r in results if not r['passed']],checks=checks,models={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in ['cpu-budget.js','surface-copy-work.js','work-runner.js']},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),scope='Uninterrupted copy loops that finish within their initial normal-core budget. One budget at the first REP entry initializes each comparison; every later REP budget derives from generated instructions and string iterations, with no resets. Independent IRQ observations and generated exhaustion identify uncomposed intervals. Cursor helpers, queue refills and live integration remain separate.')
    if clock:
        report.update(refills=sum(r.get('refills',0) for r in results),millisecond_transitions=sum(r.get('milliseconds',0) for r in results),events=dict(Counter(e['handler'] for r in results for e in r.get('events',[]))))
        for name in ['clock-queue.js','execution-clock.js']:report['models'][name]=hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest()
        report['scope']='Copy-loop execution from one initial CPU/queue/VGA state per call. All later REP budgets, full float timestamps, remaining cycles and VGA part progress are generated without native resets. Queue contents at entry are reconstructed from past reference mutations only. Original instruction/REP work drives refills and hardware events. IRQ/cursor helpers and whole-game live integration remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','control','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--clock',action='store_true')
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output,a.clock) else 1)
