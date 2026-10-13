"""Execute whole animation caller spans from one initial RAM/CPU/device state."""
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
    meta=trace['animation_loop'];stream=trace_path.parent/meta['path'];imeta=irq['irq'];istream=irq_path.parent/imeta['path'];initial_path=irq_path.parent/imeta['initial_path']
    for path,digest in [(stream,meta['sha256']),(istream,imeta['sha256']),(initial_path,imeta['initial_sha256'])]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Fixture digest differs')
    rows=[json.loads(s) for s in stream.read_text().splitlines()];ops=[json.loads(s) for s in istream.read_text().splitlines()];pic_initial=json.loads(initial_path.read_text())
    if len(rows)!=meta['calls'] or meta['partial_final_calls']:raise ValueError('Incomplete loop capture')
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples'][:1]) for r in rows],irq,irq_path,tick_order=True)
    modules=['mixer-channel-work.js','sound-dma-work.js','mixer-clock-work.js','resident-sound-work.js','sound-interrupt-work.js','sound-device-work.js','animation-loop-work.js','script-work.js','script-wrapper-work.js','animation-work.js','cursor-work.js','surface-copy-work.js','mono-sprite-work.js','sprite-work.js','rect-fill-work.js','graphics-work.js','geometry-work.js','resident-resource-work.js','resident-near-work.js','heap-instructions.js','resident-heap-work.js','shape-codec-work.js','shape-conversion-work.js','animation-graphics-work.js','resident-timer-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js','interrupt-controller.js']
    sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules};results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        for row in rows:
            packed=(trace_path.parent/row['memory']['path']).read_bytes();data=gzip.decompress(packed)
            if len(data)!=2*row['memory']['ram_size'] or hashlib.sha256(data).hexdigest()!=row['memory']['sha256']:raise ValueError('RAM fixture differs')
            past=[o for o in ops if o['milliseconds']<row['samples'][0]['milliseconds']]
            initial=past[-1]['after'] if past else pic_initial
            result=page.evaluate('''async ({row,packed,queueState,initialPic,expectedAdmissions,mainBase})=>{
              let count=0,sample=0,hash=2166136261,iterations=0,interrupts=0,audioCalls=0,audioPcmBytes=0;const irqCounts={},recent=[];
              try{
                const compressed=Uint8Array.from(atob(packed),c=>c.charCodeAt(0)),bytes=new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()),size=row.memory.ram_size,memory=bytes.slice(0,size),expected=bytes.subarray(size);
                const assert=(ok,message)=>{if(!ok)throw new Error(message);},initial=row.samples[0],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:initial.left,maximum:initial.maximum,io:initial.io}),pic=new OriginalInterruptController({...initialPic,cycles:cpu.cycles,left:cpu.left,interrupt_enabled:Number(!!(initial.flags&512)),trap:0});
                queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:initial.parts_left,linesDone:initial.lines_done});
                let hardwareTime=false,finishedFrame=row.audio_frontend[5]!==row.audio_frontend[6];
                const clock=new OriginalExecutionClock({queue:q,cpu,onMillisecond:()=>{
                  // GFX_Events runs at the exhausted-tick boundary. A completed
                  // VGA update advances the frontend frame and clears its I/O
                  // accounting counter; this never refunds guest CPU cycles.
                  if(finishedFrame){cpu.io=0;mixer.frame();finishedFrame=false;}
                  hardwareTime=true;mixer.tick();hardwareTime=false;
                },onEvent:(e,q)=>{
                  if(e.handler===4){pic.setCpu({cycles:q.cycles,left:q.left,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});pic.apply(1,0);q.cycles=pic.cycles;q.left=pic.left;q.add(4,0,OriginalClockQueue.pitDelay(19886));}
                  else if(e.handler===8){hardwareTime=true;consumeAudio(e.value,q.snapshot().milliseconds);hardwareTime=false;}
                  else{vga.service(e,q);if(e.handler===7&&!vga.partsLeft)finishedFrame=true;}
                },onInterrupts:()=>{
                  if(!pic.check)return;const saved=pic.interrupt_enabled,vector=cpu.interrupt(pic,{kind:6,interrupt_enabled:saved,trap:pic.trap});if(vector<0)return;
                  assert(vector===8||vector===15,'Uncomposed interrupt '+vector);const admission=expectedAdmissions[interrupts];assert(admission&&admission.vector===vector&&admission.milliseconds===clock.state().milliseconds,'Generated IRQ admission differs at '+clock.state().milliseconds);interrupts++;irqCounts[vector]=(irqCounts[vector]||0)+1;
                  const runner=new OriginalWorkRunner(vector===8?new OriginalResidentTimerWork({memory,ds:row.ds}).run():driver.run(),{onInstruction});
                  for(;;){const stop=clock.run(runner);if(stop.kind==='complete')break;const a=stop.action;
                    runner.resume(actionValue(a));
                  }
                  pic.interrupt_enabled=saved;if(saved&&pic.check)clock.refill();
                }});
                const onInstruction=(label,b)=>{
                  const [region,offset]=label.split(':'),address=parseInt(offset,16)+(region==='physical'?0:(region==='sound'?soundSegment*16:mainBase+(region==='resident'?0xd510:0)));
                  for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((address>>>shift)&255),16777619)>>>0;
                  recent.push(label);if(recent.length>10)recent.shift();const s=row.samples[sample];
                  if(s&&s.instruction===count){
                    assert(address===s.address,'Sample address at instruction '+count+' '+label+' != '+s.address.toString(16));
                    const actual={budget:b.cycles,left:b.left,maximum:b.maximum,io:b.io,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                    for(const key of Object.keys(actual))assert(actual[key]===s[key],key+' at '+label+': '+actual[key]+' != '+s[key]);
                    assert(pic.interrupt_enabled===Number(!!(s.flags&512)),'Interrupt flag at '+label+' differs');sample++;
                  }
                  count++;assert(count<=row.instructions,'Generated execution exceeds native span');
                };
                const soundSegment=new DataView(memory.buffer).getUint16(16*row.ds+0x212a,true),driver=new OriginalSoundInterruptWork({memory,ds:row.ds,ss:row.ss,residentSegment:(mainBase+0xd510)/16,soundSegment});
                const hardwareFields=['base','irq','dmaChannel','dspState','writeBusy','outputUsed','pending8','pending16','command','commandLength','commandPosition','timeConstant','frequency','mode','dmaMode','remaining','singleSize','baseAddress','currentAddress','baseCount','currentCount','page','masked','request','terminalCount','autoInit','increment','speaker','type','stereo','rate','minimum'];
                const timeState=()=>hardwareTime?q.snapshot():clock.state();
                const picEffect=(kind,arg,value=0)=>{
                  if(hardwareTime){pic.setCpu({cycles:q.cycles,left:q.left,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});pic.apply(kind,arg,value);q.cycles=pic.cycles;q.left=pic.left;}
                  else cpu.interrupt(pic,{kind,arg,value,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});
                };
                const device=new OriginalSoundDeviceWork({state:{...Object.fromEntries(hardwareFields.map((k,i)=>[k,row.sound_initial[i]])),dspAutoInit:row.dma_autoinit},effect:e=>{
                  if(e.kind==='irq-lower'||e.kind==='irq-raise')picEffect(e.kind==='irq-raise'?1:2,e.irq);
                  else if(e.kind==='remove-end-dma'){timeState();q.remove(8);}
                  else if(e.kind==='mixer-fill')mixer.fill(timeState().tick_index);
                  else if(e.kind==='mixer-frequency')channel.setFrequency(e.frequency,mixer.state.frequency);
                  else if(e.kind==='schedule-end-dma'){timeState();q.add(8,e.count,e.delay);if(!hardwareTime){cpu.cycles=q.cycles;cpu.left=q.left;}}
                  else throw new Error('Uncomposed device effect '+e.kind);
                }});
                const named=(names,values)=>Object.fromEntries(names.map((k,i)=>[k,values[i]]));
                const channel=new OriginalMixerChannelWork({state:named(['enabled','done','needed','frequencyAdd','frequencyCounter','previousLeft','previousRight','nextLeft','nextRight','interpolate','lastSilence','lastStereo','offsetLeft','offsetRight','volumeLeft','volumeRight'],row.channel_initial)});
                const dma=new OriginalSoundDmaWork({device,channel,transfer:named(['autoInit','autoSize','stereo','sign','fade','multiplier','remainingBytes','dma16'],row.dma_initial),readByte:at=>{assert(at<memory.length,'DMA source outside RAM');return memory[at];}});dma.lastCallback=row.last_dma_callback;
                const consumeAudio=(count,now)=>{const pcm=dma.consume(count,now);audioCalls++;audioPcmBytes+=pcm.length;return pcm;};
                const mixer=new OriginalMixerClockWork({state:named(['frequency','done','needed','position','tickAdd','tickCounter','blockSize','minimum','maximum','noSound'],row.mixer_initial),frontend:named(['remaining','sampleRate','fps','mode','rate'],row.audio_frontend),channel,generate:count=>{
                  if(device.state.mode===2)consumeAudio(Math.min(count,device.state.remaining),timeState().milliseconds);
                  else if([0,3,4].includes(device.state.mode))channel.silence();
                  else throw new Error('Unsupported sound output mode '+device.state.mode);
                }});
                const actionValue=a=>{
                  if(a.call==='interrupt-flags')pic.interrupt_enabled=Number(a.enabled);
                  else if(a.call==='read-interrupt-flag')return !!pic.interrupt_enabled;
                  else if(a.call==='stack-segment-credit')cpu.stackSegmentCredit();
                  else if(a.call==='port-read'||a.call==='port-write'){
                    const read=a.call==='port-read';cpu.port(read?'read':'write');
                    if(read)return a.port===0x21?pic.controllers[0].imr:device.read(a.port);
                    else if(a.port===0x20||a.port===0x21)picEffect(a.port===0x20?4:5,a.port,a.value);
                    else device.write(a.port,a.value);
                  }else if(!['bios-clock','bios-user-timer','bios-device-post'].includes(a.call))throw new Error('Uncomposed loop action '+a.call+' id '+a.id);
                };
                const sound=new OriginalResidentSoundWork({memory,ds:row.ds,driver});
                const operations={},heap=new OriginalResidentHeapWork({memory,ds:row.ds}),shapeConverter=new OriginalShapeConversionWork({memory,ds:row.ds,heap}),adapter=new OriginalAnimationGraphicsWork({memory,ds:row.ds,shapeConverter,onOperation:o=>operations[o.kind]=(operations[o.kind]||0)+1}),loop=new OriginalAnimationLoopWork({adapter,instance:row.instance,firstFrame:row.first_frame,baseId:row.base_id,activity:row.activity,sound,onIteration:o=>{iterations=o.iteration;}});
                const runner=new OriginalWorkRunner(loop.run(),{singleStrings:new Set([...OriginalAnimationGraphicsWork.singleStrings,...OriginalShapeConversionWork.singleStrings]),onInstruction});let stop;
                for(;;){
                  stop=clock.run(runner);if(stop.kind==='complete')break;const a=stop.action;let value;
                  runner.resume(actionValue(a));
                }
                assert(stop.kind==='complete','Uncomposed loop action '+stop.action?.call+' id '+stop.action?.id);
                assert(count===row.instructions&&sample===row.samples.length&&hash===row.path_hash,'Complete instruction count/hash/sample coverage differs');
                const lo=16*row.ss+row.stack_low,hi=16*row.ss+row.sp,differences=[];let checked=0,changed=0;
                for(let i=0;i<size;i++){if(i>=lo&&i<hi)continue;checked++;if(memory[i]!==bytes[i])changed++;if(memory[i]!==expected[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expected[i]});}
                assert(!differences.length,'Loop RAM differs '+JSON.stringify(differences));
                return {passed:true,instructions:count,samples:sample,iterations,interrupts,irqCounts,audioCalls,audioPcmBytes,strings:runner.strings,audioFrames:mixer.frames,operations,checkedBytes:checked,changedBytes:changed,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),instructions:count,comparedSamples:sample,iterations,interrupts,irqCounts,audioCalls,audioPcmBytes,recent};}
            }''',dict(row=row,packed=base64.b64encode(packed).decode(),queueState=queues[row['ordinal']],initialPic=initial,expectedAdmissions=[dict(vector=o['vector'],milliseconds=o['milliseconds']) for o in ops if o['vector']>=0 and row['samples'][0]['milliseconds']<=o['milliseconds']<=row['samples'][-1]['milliseconds']],mainBase=trace['location']['main_base']))
            results.append(dict(ordinal=row['ordinal'],**result))
        browser.close()
    passed=bool(results) and all(r['passed'] for r in results)
    report=dict(passed=passed,full_cpu_scheduling_parity=False,loops=len(rows),matching_loops=sum(r['passed'] for r in results),results=results,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Whole 4855..48C0 spans from initial RAM/CPU/queue/controller: generated interpreter repetitions, mutable script/globals, timer reads, composed rendering, generated millisecond mixer cadence, frame audio-buffer consumption and DMA IRQs. Complete spans compare instruction count/hash, sparse clock/IF samples and RAM outside measured active stack. Guest caller registers/stack, mouse input scheduling, final host audio output and uncomposed callees remain explicit limitations; no live/full-game parity claim.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
