"""Execute complete cursor roots on shared surfaces and one CPU/queue state each."""
from pathlib import Path
from collections import Counter
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('Independent IRQ route differs')
    streams={}
    for kind in ['cursors','blits','sprites']:
        meta=trace[kind];path=trace_path.parent/meta['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Observation digest differs')
        if meta['partial_final_calls']:raise ValueError('Incomplete final call')
        rows=sorted((json.loads(s) for s in path.read_text().splitlines()),key=lambda r:r['ordinal'])
        if len(rows)!=meta['calls']:raise ValueError('Call count differs')
        for row in rows:
            if 'pixels' in row:
                payload=gzip.decompress((trace_path.parent/row['pixels']['path']).read_bytes())
                if hashlib.sha256(payload).hexdigest()!=row['pixels']['sha256']:raise ValueError('Pixel digest differs')
                row['payload']=base64.b64encode(payload).decode()
        streams[kind]=rows
    roots=[r for r in streams['cursors'] if r['parent']==-1]
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples']) for r in roots],irq,irq_path)
    irq_stream=irq_path.parent/irq['irq']['path']
    if hashlib.sha256(irq_stream.read_bytes()).hexdigest()!=irq['irq']['sha256']:raise ValueError('IRQ digest differs')
    deliveries=[r['milliseconds'] for line in irq_stream.read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    skipped=Counter();results=[]
    modules=['cursor-work.js','surface-copy-work.js','mono-sprite-work.js','sprite-work.js','rect-fill-work.js','graphics-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        for root in roots:
            if any(root['begin']<=t<=root['end'] for t in deliveries):skipped['IRQ during cursor root']+=1;continue
            contained={k:[r for r in rows if root['begin']<=r['begin'] and r['end']<=root['end']] for k,rows in streams.items()}
            actual=page.evaluate('''({root,streams,queueState})=>{
              try{
                const assert=(test,message)=>{if(!test)throw new Error(message);},equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),u16=a=>Array.from(a,v=>v&65535);
                const decode=r=>{const b=Uint8Array.from(atob(r.payload||''),c=>c.charCodeAt(0));return {source:b.slice(0,r.source_size),before:b.slice(r.source_size,r.source_size+r.destination_size),after:b.slice(r.source_size+r.destination_size)};};
                const state=Uint16Array.from(root.before),buffers=new Map(),rows=new Map(),shapes=new Map(),cursors=streams.cursors.slice(),copies=streams.blits.slice(),sprites=streams.sprites.slice(),stack=[];
                const first=copies[0];
                if(first){
                  const pixels=decode(first);for(const [id,header,table,bytes] of [[first.source_id,first.source,first.source_rows,pixels.source],[first.destination_id,first.destination,first.destination_rows,pixels.before]]){
                    const address=16*header[1]+header[0];assert(!buffers.has(address),'Initial cursor surfaces alias unexpectedly');buffers.set(address,bytes);rows.set(id,table);
                  }
                }
                for(const native of sprites){
                  assert(native.kind===1&&[1,3].includes(native.mode),'Unexpected cursor sprite');const slot=native.mode===1?0:1,handle=state[7+slot],words={state:root.handles[2*slot],segment:root.handles[2*slot+1]},pixels=decode(native).source;
                  const item={header:native.shape,pixels,handleWords:words,address:16*words.segment+(words.state&15)+6};
                  if(shapes.has(handle))assert(equal(Array.from(shapes.get(handle).pixels),Array.from(pixels)),'Cursor shape changed within a root');else shapes.set(handle,item);
                }
                function surface(id){
                  assert(id===0x2088||id===0x20d0,'Unknown cursor surface');const header=Array.from(state.slice(id===0x2088?10:26,id===0x2088?26:42)),pixels=buffers.get(16*header[1]+header[0]);
                  assert(pixels&&rows.has(id),'Missing cursor surface input');return {header,pixels,rows:rows.get(id)};
                }
                const initial=root.samples[0],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:initial.left,maximum:initial.maximum});queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:root.video_delays,partsTotal:root.parts_total,partsLines:root.parts_lines,linesTotal:root.lines_total,partsLeft:initial.parts_left,linesDone:initial.lines_done});
                const clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q)});let cursorCalls=0,graphicCalls=0,clockSamples=0,pixelChecks=0,writes=0;
                function checkClock(expected,b){
                  const actual={budget:b.cycles,left:b.left,maximum:b.maximum,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                  for(const key of Object.keys(actual))assert(actual[key]===expected[key],'Clock '+key+' differs: '+actual[key]+' != '+expected[key]);clockSamples++;
                }
                const graphics=new OriginalGraphicsWork({cursorState:state,surface,shape:handle=>{assert(shapes.has(handle),'Missing cursor shape');return shapes.get(handle);},onOperation:operation=>{
                  const row=operation.kind==='cursor'?cursors.shift():operation.kind==='copy'?copies.shift():sprites.shift();assert(row,'Missing native operation '+operation.kind);
                  if(operation.kind==='cursor'){
                    assert(row.kind===['prepare','hide','restore'].indexOf(operation.operation),'Cursor operation order differs');assert(equal(Array.from(state),row.before),'Cursor entry state differs');
                    if(row.kind===0){assert(equal(u16(operation.input.pointer),row.pointer),'Cursor pointer differs');assert(equal(u16(operation.input.rect),row.rect),'Cursor rect differs');}cursorCalls++;
                  }else{
                    const i=operation.input;assert(row.context===state[1]&&row.mode===i.mode,'Graphics context/mode differs');
                    if(operation.kind==='copy')for(const key of ['source_id','destination_id','source','destination','source_rect','destination_rect'])assert(equal(typeof i[key]==='number'?i[key]:u16(i[key]),row[key]),'Copy operand differs: '+key);
                    else for(const key of ['color','x','y','shape','surface'])assert(equal(typeof i[key]==='number'?i[key]&65535:u16(i[key]),row[key]),'Sprite operand differs: '+key);
                    graphicCalls++;
                  }
                  stack.push({kind:operation.kind,row,counts:{},hash:2166136261,sample:0,input:operation.input,pixels:operation.kind==='cursor'?null:decode(row)});
                },onReturn:operation=>{
                  const frame=stack.pop();assert(frame&&frame.kind===operation.kind,'Return nesting differs');const {row}=frame;
                  assert(frame.hash===row.path_hash,'Instruction order differs '+frame.kind+' '+row.ordinal);
                  for(const key of new Set([...Object.keys(row.counts),...Object.keys(frame.counts)]))assert((row.counts[key]||0)===(frame.counts[key]||0),'Instruction count differs');
                  if(frame.kind==='cursor'){assert(equal(Array.from(state),row.after),'Cursor return state differs');assert(frame.sample===2,'Missing cursor clock samples');}
                  else {assert(frame.sample===(row.samples||row.slices).length,'Missing graphics clock samples');writes+=operation.value.writes;}
                }});
                const runner=new OriginalWorkRunner(graphics.cursor(['prepare','hide','restore'][root.kind],{pointer:root.pointer,rect:root.rect}),{singleStrings:OriginalGraphicsWork.singleStrings,onInstruction:(label,b)=>{
                  const at=parseInt(label.split(':')[1],16),frame=stack[stack.length-1];assert(frame,'No active graphics frame');const {row,kind}=frame;
                  const intrinsic=kind==='cursor'?(row.kind===0?at>=0x8955&&at<0x89b2:row.kind===1?at>=0x857a&&at<0x85b1:at>=0x8822&&at<0x88ca):kind==='copy'?at>=0x9a68&&at<0x9c58:at>=0x9ed6&&at<0xa024;
                  if(intrinsic){frame.counts[at]=(frame.counts[at]||0)+1;for(let shift=0;shift<32;shift+=8)frame.hash=Math.imul(frame.hash^((at>>>shift)&255),16777619)>>>0;}
                  if(kind==='cursor'){
                    if(at===[0x8955,0x857a,0x8822][row.kind]||at===row.last)checkClock(row.samples[frame.sample++],b);
                  }else{
                    const samples=row.samples||row.slices,s=samples[frame.sample];if(s&&s.address===at){checkClock(s,b);frame.sample++;}
                    const before=kind==='copy'?0x9b73:0x9f5b,after=kind==='copy'?0x9c22:0x9fbe;
                    if(at===before){const {input,pixels}=frame;assert(input.sourcePixels.length===pixels.source.length&&input.sourcePixels.every((v,i)=>v===pixels.source[i]),'Shared source pixels differ');assert(input.destinationPixels.length===pixels.before.length&&input.destinationPixels.every((v,i)=>v===pixels.before[i]),'Shared destination before draw differs');pixelChecks+=2;}
                    if(at===after){const {input,pixels}=frame;assert(input.destinationPixels.length===pixels.after.length&&input.destinationPixels.every((v,i)=>v===pixels.after[i]),'Shared destination after draw differs');pixelChecks++;}
                  }
                }});
                const end=clock.run(runner);assert(end.kind==='complete'&&!stack.length&&!cursors.length&&!copies.length&&!sprites.length,'Incomplete composed cursor');
                return {passed:true,cursorCalls,graphicCalls,clockSamples,pixelChecks,writes,instructions:runner.instructions,strings:runner.strings,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e)};}
            }''',dict(root=root,streams=contained,queueState=queues[root['ordinal']]))
            results.append(dict(ordinal=root['ordinal'],**actual))
            if not actual['passed']:break
        browser.close()
    report=dict(passed=all(r['passed'] for r in results) and len(results)+sum(skipped.values())==len(roots),full_cpu_scheduling_parity=False,roots=len(roots),matching_roots=sum(r['passed'] for r in results),skipped=dict(skipped),**{key:sum(r.get(key,0) for r in results) for key in ['cursorCalls','graphicCalls','clockSamples','pixelChecks','writes','instructions','strings','refills']},events=dict(Counter(e['handler'] for r in results for e in r.get('events',[]))),failures=[r for r in results if not r['passed']],models={n:hashlib.sha256((ROOT/'treehouse-demo'/n).read_bytes()).hexdigest() for n in modules},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='One cursor-state/CPU/queue fixture and one initial screen/backup pixel pair per root. All nested helper, copy, mask and handle-query work shares the CPU and pixel buffers. Later per-operation states, pixels, REP splits and clocks are comparisons only. Shape bytes/handle words and row tables remain inputs. IRQ-containing roots are explicitly excluded; this is not whole-game or live-build parity.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
