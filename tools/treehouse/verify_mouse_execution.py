"""Execute IRQ12 and its resident cursor callback from initial mouse/RAM state."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('IRQ route differs')
    meta=trace['device_execution'];stream=trace_path.parent/meta['path'];imeta=irq['irq'];istream=irq_path.parent/imeta['path'];initial_path=irq_path.parent/imeta['initial_path']
    for path,digest in [(stream,meta['sha256']),(istream,imeta['sha256']),(initial_path,imeta['initial_sha256'])]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Fixture digest differs')
    all_rows=[json.loads(s) for s in stream.read_text().splitlines()];rows=[r for r in all_rows if r['vector']==0x74]
    ops=[json.loads(s) for s in istream.read_text().splitlines()];deliveries=[i for i,o in enumerate(ops) if o['vector']==0x74]
    if len(deliveries)!=len(rows) or len(all_rows)!=meta['calls'] or meta['partial_final_calls']:raise ValueError('Incomplete capture')
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples'][:1]) for r in rows],irq,irq_path,tick_order=True)
    modules=['mouse-interrupt-work.js','cursor-work.js','surface-copy-work.js','mono-sprite-work.js','sprite-work.js','rect-fill-work.js','graphics-work.js','resident-resource-work.js','animation-graphics-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js','interrupt-controller.js']
    sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules};results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        for number,row in enumerate(rows):
            packed=(trace_path.parent/row['memory']['path']).read_bytes();data=gzip.decompress(packed)
            if len(data)!=2*row['memory']['ram_size'] or hashlib.sha256(data).hexdigest()!=row['memory']['sha256']:raise ValueError('RAM fixture differs')
            admission=ops[deliveries[number]]
            if not 0<=row['samples'][0]['milliseconds']-admission['milliseconds']<0.001:raise ValueError('IRQ entry differs')
            inside=[o for o in ops[deliveries[number]+1:] if row['samples'][0]['milliseconds']<=o['milliseconds']<row['samples'][-1]['milliseconds']]
            result=page.evaluate('''async ({row,packed,queueState,initialPic,expectedOps,residentBase})=>{
              let index=0,operation=0;const recent=[];
              try{
                const compressed=Uint8Array.from(atob(packed),c=>c.charCodeAt(0)),bytes=new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()),size=row.memory.ram_size,memory=bytes.slice(0,size),expected=bytes.subarray(size);
                const assert=(ok,message)=>{if(!ok)throw new Error(message);},same=(a,b)=>Object.keys(b).every(k=>b[k]&&typeof b[k]==='object'?same(a[k],b[k]):a[k]===b[k]);
                const first=row.samples[0],cpu=new OriginalCpuBudget({cycles:first.budget+1,left:first.left,maximum:first.maximum,io:first.io}),pic=new OriginalInterruptController({...initialPic,cycles:cpu.cycles,left:cpu.left,interrupt_enabled:Number(!!(first.flags&512)),trap:0});
                queueState.state={...queueState.state,...cpu.snapshot(),ticks:first.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:first.parts_left,linesDone:first.lines_done}),clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q),onInterrupts:()=>{if(pic.check)picOp(6,0);}});
                const hardware=row.mouse_before,state={events:Array.from({length:hardware[0]},(_,i)=>({type:hardware[16+2*i],buttons:hardware[17+2*i]})),inUser:!!hardware[1],mask:hardware[2],callback:16*hardware[3]+hardware[4],x:hardware[5],y:hardware[6],hidden:hardware[9],allowRealMode:!!hardware[10],ps2:!!hardware[11],timerInProgress:!!hardware[12],returnAddress:hardware[13],userReturn:hardware[14],inhibitDraw:!!hardware[15]};
                const graphicsCalls={cursor:0,copy:0,sprite:0};
                const adapter=new OriginalAnimationGraphicsWork({memory,ds:row.data_segment,onOperation:o=>{graphicsCalls[o.kind]++;}}),work=new OriginalMouseInterruptWork({memory,ds:row.data_segment,ss:row.entry_ss,residentSegment:residentBase/16,graphics:adapter.graphics,state,entry:row.entry_address});
                const runner=new OriginalWorkRunner(work.run(),{singleStrings:OriginalGraphicsWork.singleStrings,onInstruction:(label,b)=>{
                  const [region,offset]=label.split(':'),address=parseInt(offset,16)+(region==='resident'?residentBase:0),s=row.samples[index];
                  assert(s&&s.address===address,'Instruction '+index+' '+label+' != '+s?.address.toString(16));
                  const actual={budget:b.cycles,left:b.left,maximum:b.maximum,io:b.io,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                  for(const key of Object.keys(actual))assert(actual[key]===s[key],key+' at '+label+': '+actual[key]+' != '+s[key]);
                  assert(pic.interrupt_enabled===Number(!!(s.flags&512)),'Interrupt flag at '+label+' differs');
                  if(label==='resident:88ca')assert(s.ax===hardware[16+2*(hardware[0]-1)]&&s.bx===hardware[17+2*(hardware[0]-1)]&&s.cx===state.x&&s.dx===state.y&&s.si===hardware[7]&&s.di===hardware[8],'Mouse callback arguments differ');
                  index++;recent.push(label);if(recent.length>10)recent.shift();
                }});
                const picOp=(kind,arg,value=0)=>{
                  pic.setCpu({...cpu.snapshot(),interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});const native=expectedOps[operation++];
                  assert(native&&native.kind===kind&&native.arg===arg&&native.value===value,'PIC operation differs');assert(same(pic.snapshot(),native.before),'PIC before differs');assert(clock.state().milliseconds===native.milliseconds,'PIC time differs');
                  const vector=cpu.interrupt(pic,{kind,arg,value,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});assert(vector<0,'Nested IRQ requires composition');assert(same(pic.snapshot(),native.after),'PIC after differs');
                };
                let stop,callbacks=0,ports=0,credits=0;
                for(let guard=0;guard<1000;guard++){
                  stop=clock.run(runner);if(stop.kind==='complete')break;assert(stop.kind==='call','Unexpected suspension');const a=stop.action;
                  if(a.call==='interrupt-flags')pic.interrupt_enabled=Number(a.enabled);
                  else if(a.call==='stack-segment-credit'){cpu.stackSegmentCredit();credits++;}
                  else if(['mouse-irq','mouse-return','mouse-user-return'].includes(a.call))callbacks++;
                  else if(a.call==='port-write'){
                    const s=row.samples[index-1];assert(s.code[0]===0xe6&&s.code[1]===a.port&&(s.ax&255)===a.value,'Port output differs');
                    cpu.port('write');picOp(4,a.port,a.value);ports++;
                  }else throw new Error('Unsupported action '+a.call);
                  runner.resume();
                }
                assert(stop.kind==='complete'&&index===row.samples.length&&operation===expectedOps.length,'Incomplete IRQ execution');
                assert(state.events.length===row.mouse_after[0]&&Number(state.inUser)===row.mouse_after[1]&&Number(state.timerInProgress)===row.mouse_after[12],'Mouse event state differs');
                const lo=16*row.entry_ss+row.stack_low,hi=16*row.entry_ss+row.entry_sp,differences=[];let checked=0,changed=0;
                for(let i=0;i<size;i++){if(i>=lo&&i<hi)continue;checked++;if(memory[i]!==bytes[i])changed++;if(memory[i]!==expected[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expected[i]});}
                assert(!differences.length,'Mouse memory differs '+JSON.stringify(differences));
                return {passed:true,instructions:index,strings:runner.strings,ports,picOperations:operation,callbacks,credits,graphicsCalls,checkedBytes:checked,changedBytes:changed,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),index,operation,recent};}
            }''',dict(row=row,packed=base64.b64encode(packed).decode(),queueState=queues[row['ordinal']],initialPic=admission['after'],expectedOps=inside,residentBase=trace['location']['main_base']+0xd510))
            results.append(dict(ordinal=row['ordinal'],**result))
            if not result['passed']:break
        browser.close()
    passed=bool(results) and len(results)==len(rows) and all(r['passed'] for r in results)
    report=dict(passed=passed,full_cpu_scheduling_parity=False,calls=len(rows),matching_calls=sum(r['passed'] for r in results),**{n:sum(r.get(n,0) for r in results) for n in ['instructions','strings','ports','picOperations','callbacks','credits','checkedBytes','changedBytes','refills']},results=results,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Each IRQ12 starts from initial RAM/CPU/queue/controller/mouse state. BIOS stubs and resident callback generate cursor drawing, instructions, clocks, IF, port outputs and non-stack RAM. Expected paths/times/after-memory only compare. Hardware entry, nested IRQs, other mouse paths and continuous/live integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
