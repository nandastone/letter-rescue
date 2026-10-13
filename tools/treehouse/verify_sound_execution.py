"""Compare generated IRQ7 work with native instructions, ports, clocks and RAM.

DSP/DMA scheduling and PCM production are separate: this checks device status
reads and outgoing commands, not a complete SoundBlaster hardware model.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
from collections import Counter
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
    all_rows=[json.loads(s) for s in stream.read_text().splitlines()];rows=[r for r in all_rows if r['vector']==15]
    ops=[json.loads(s) for s in istream.read_text().splitlines()];deliveries=[i for i,o in enumerate(ops) if o['vector']==15]
    if len(deliveries)!=len(rows) or len(all_rows)!=meta['calls'] or meta['partial_final_calls']:raise ValueError('Incomplete capture')
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples'][:1]) for r in rows],irq,irq_path,tick_order=True)
    # Retain only the independently observed DMA-end removals for comparison;
    # the runtime device derives when to emit them from DSP command bytes.
    removals=[]
    with (irq_path.parent/irq['pic']['path']).open() as f:
        for line in f:
            o=json.loads(line)
            if o['kind']==2 and o['handler']==8:removals.append(o)
    modules=['sound-device-work.js','sound-interrupt-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js','interrupt-controller.js']
    sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules};results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        for number,row in enumerate(rows):
            packed=(trace_path.parent/row['memory']['path']).read_bytes();data=gzip.decompress(packed)
            if len(data)!=2*row['memory']['ram_size'] or hashlib.sha256(data).hexdigest()!=row['memory']['sha256']:raise ValueError('RAM fixture differs')
            admission=ops[deliveries[number]]
            if not 0<=row['samples'][0]['milliseconds']-admission['milliseconds']<0.001:raise ValueError('IRQ entry differs')
            # The final sample is before IRET; another admission can happen at
            # that same timestamp after IRET and belongs to the next caller.
            inside=[o for o in ops[deliveries[number]+1:] if row['samples'][0]['milliseconds']<=o['milliseconds']<row['samples'][-1]['milliseconds']]
            device_queue=[o for o in removals if row['samples'][0]['milliseconds']<=o['before']['milliseconds']<row['samples'][-1]['milliseconds']]
            result=page.evaluate('''async ({row,packed,queueState,initialPic,expectedOps,expectedDeviceQueue,residentBase})=>{
              let index=0,operation=0,ports=0;const recent=[];
              try{
                const compressed=Uint8Array.from(atob(packed),c=>c.charCodeAt(0)),bytes=new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()),size=row.memory.ram_size,memory=bytes.slice(0,size),expected=bytes.subarray(size);
                const assert=(ok,message)=>{if(!ok)throw new Error(message);},same=(a,b)=>Object.keys(b).every(k=>b[k]&&typeof b[k]==='object'?same(a[k],b[k]):a[k]===b[k]);
                const first=row.samples[0],cpu=new OriginalCpuBudget({cycles:first.budget+1,left:first.left,maximum:first.maximum,io:first.io}),pic=new OriginalInterruptController({...initialPic,cycles:cpu.cycles,left:cpu.left,interrupt_enabled:Number(!!(first.flags&512)),trap:0});
                queueState.state={...queueState.state,...cpu.snapshot(),ticks:first.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:first.parts_left,linesDone:first.lines_done}),clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>{
                  if(event.handler===4){
                    // PIT edges continue while IF is clear. The controller may
                    // queue IRQ0, but cannot enter its guest handler yet.
                    pic.setCpu({cycles:q.cycles,left:q.left,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});
                    const native=expectedOps[operation++];assert(native&&native.kind===1&&native.arg===0,'PIT IRQ differs');
                    assert(same(pic.snapshot(),native.before),'PIT PIC before differs');pic.apply(1,0);assert(same(pic.snapshot(),native.after),'PIT PIC after differs');
                    q.cycles=pic.cycles;q.left=pic.left;q.add(4,0,OriginalClockQueue.pitDelay(19886));
                  }else vga.service(event,q);
                },onInterrupts:()=>{if(pic.check)picOp(6,0);}});
                const work=new OriginalSoundInterruptWork({memory,ds:row.data_segment,ss:row.entry_ss,residentSegment:residentBase/16,soundSegment:first.cs});
                let callbacks=0,credits=0,queueRemovals=0;const deviceEffects=[];
                const hardwareFields=['base','irq','dmaChannel','dspState','writeBusy','outputUsed','pending8','pending16','command','commandLength','commandPosition','timeConstant','frequency','mode','dmaMode','remaining','singleSize','baseAddress','currentAddress','baseCount','currentCount','page','masked','request','terminalCount','autoInit','increment','speaker','type','stereo','rate','minimum'];
                assert(row.hardware_before[28]>0,'Full sound hardware observation required');
                const device=new OriginalSoundDeviceWork({state:Object.fromEntries(hardwareFields.map((k,i)=>[k,row.hardware_before[i]])),effect:e=>{
                  deviceEffects.push(e);
                  if(e.kind==='irq-lower')picOp(2,e.irq);
                  else if(e.kind==='mixer-fill')assert(e.mode===0||e.mode===4,'Active PCM fill requires composition');
                  else if(e.kind==='remove-end-dma'){
                    const native=expectedDeviceQueue[queueRemovals++];assert(native,'Unexpected DMA event removal');
                    assert(same(clock.state(),native.before),'Queue before DMA removal differs');q.remove(8);
                    assert(same(clock.state(),native.after),'Queue after DMA removal differs');
                  }
                  else if(e.kind!=='mixer-frequency')throw new Error('Uncomposed sound device effect '+e.kind);
                }});
                const runner=new OriginalWorkRunner(work.run(),{onInstruction:(label,b)=>{
                  const [region,offset]=label.split(':'),address=parseInt(offset,16)+(region==='resident'?residentBase:region==='sound'?16*first.cs:0),s=row.samples[index];
                  assert(s&&s.address===address,'Instruction '+index+' '+label+' != '+s?.address.toString(16));
                  const actual={budget:b.cycles,left:b.left,maximum:b.maximum,io:b.io,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                  for(const key of Object.keys(actual))assert(actual[key]===s[key],key+' at '+label+': '+actual[key]+' != '+s[key]);
                  assert(pic.interrupt_enabled===Number(!!(s.flags&512)),'Interrupt flag at '+label+' differs');
                  index++;recent.push(label);if(recent.length>10)recent.shift();
                }});
                const picOp=(kind,arg,value=0)=>{
                  pic.setCpu({...cpu.snapshot(),interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});const native=expectedOps[operation++];
                  assert(native&&native.kind===kind&&native.arg===arg&&native.value===value,'PIC operation differs');
                  assert(same(pic.snapshot(),native.before),'PIC before differs');assert(clock.state().milliseconds===native.milliseconds,'PIC time differs');
                  cpu.interrupt(pic,{kind,arg,value,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});assert(same(pic.snapshot(),native.after),'PIC after differs');
                };
                let stop;
                for(let guard=0;guard<1000;guard++){
                  stop=clock.run(runner);if(stop.kind==='complete')break;assert(stop.kind==='call','Unexpected suspension');const action=stop.action;let value;
                  if(action.call==='read-interrupt-flag')value=!!pic.interrupt_enabled;
                  else if(action.call==='interrupt-flags')pic.interrupt_enabled=Number(action.enabled);
                  else if(action.call==='stack-segment-credit'){cpu.stackSegmentCredit();credits++;}
                  else if(action.call==='bios-device-post')callbacks++;
                  else if(action.call==='port-read'||action.call==='port-write'){
                    ports++;const native=row.samples[index-1],read=action.call==='port-read',code=native.code;
                    const nativePort=[0xec,0xee].includes(code[0])?native.dx:code[1];
                    assert(nativePort===action.port,'Port differs '+action.port+' != '+nativePort);cpu.port(read?'read':'write');
                    if(read){
                      if(action.port===0x21)value=pic.controllers[0].imr;
                      else value=device.read(action.port);
                      assert((row.samples[index].ax&255)===value,'Input value differs');
                    }else{
                      assert((native.ax&255)===action.value,'Output value differs at '+recent.at(-1)+': '+action.value+' != '+(native.ax&255));
                      if(action.port===0x20)picOp(4,action.port,action.value);
                      else if(action.port===0x21)picOp(5,action.port,action.value);
                      else device.write(action.port,action.value);
                    }
                  }else throw new Error('Unsupported action '+action.call);
                  runner.resume(value);
                }
                assert(stop.kind==='complete'&&index===row.samples.length&&operation===expectedOps.length,'Incomplete IRQ execution');
                assert(queueRemovals===expectedDeviceQueue.length,'Missing DMA event removals');
                const hardware=device.snapshot();for(let i=0;i<hardwareFields.length;i++)assert(hardware[hardwareFields[i]]===row.hardware_after[i],'Sound hardware '+hardwareFields[i]+' differs: '+hardware[hardwareFields[i]]+' != '+row.hardware_after[i]);
                const lo=16*row.entry_ss+row.stack_low,hi=16*row.entry_ss+row.entry_sp,differences=[];let checked=0,changed=0;
                for(let i=0;i<size;i++){if(i>=lo&&i<hi)continue;checked++;if(memory[i]!==bytes[i])changed++;if(memory[i]!==expected[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expected[i]});}
                assert(!differences.length,'Sound memory differs '+JSON.stringify(differences));
                return {passed:true,instructions:index,ports,picOperations:operation,callbacks,credits,queueRemovals,deviceEffects,hardwareChecks:hardwareFields.length,checkedBytes:checked,changedBytes:changed,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),index,operation,ports,recent};}
            }''',dict(row=row,packed=base64.b64encode(packed).decode(),queueState=queues[row['ordinal']],initialPic=admission['after'],expectedOps=inside,expectedDeviceQueue=device_queue,residentBase=trace['location']['main_base']+0xd510))
            results.append(dict(ordinal=row['ordinal'],**result))
            if not result['passed']:break
        browser.close()
    passed=bool(results) and len(results)==len(rows) and all(r['passed'] for r in results)
    report=dict(passed=passed,full_cpu_scheduling_parity=False,full_sound_hardware_parity=False,calls=len(rows),matching_calls=sum(r['passed'] for r in results),**{n:sum(r.get(n,0) for r in results) for n in ['instructions','ports','picOperations','callbacks','credits','queueRemovals','hardwareChecks','checkedBytes','changedBytes','refills']},device_effects=dict(Counter(e['kind'] for r in results for e in r.get('deviceEffects',[]))),events=[e for r in results for e in r.get('events',[])],failures=[r for r in results if not r['passed']],models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Each IRQ7 starts from initial RAM/CPU/queue/controller and DSP state. Generated guest instructions, clocks, IF, memory outside measured stack, all port addresses/data, DSP polling and PIC effects compare to native. All 32 captured DSP/DMA state fields and command effects compare. Active PCM fill, DMA consumption and future audio event delivery are not yet composed. Entry/return and mouse IRQ have separate component proofs; continuous register propagation, device scheduling and live integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
