"""Run complete animation frames from one initial guest-memory/CPU/queue fixture."""
from pathlib import Path
from collections import Counter
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output,caption_prefix=False,caption_allocation=False,caption_complete=False):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('Independent IRQ route differs')
    meta=trace['frames_work'];path=trace_path.parent/meta['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256'] or meta['partial_final_calls']:raise ValueError('Frame stream incomplete or changed')
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    if len(rows)!=meta['calls']:raise ValueError('Frame call count differs')
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples']) for r in rows],irq,irq_path)
    irq_stream=irq_path.parent/irq['irq']['path']
    if hashlib.sha256(irq_stream.read_bytes()).hexdigest()!=irq['irq']['sha256']:raise ValueError('IRQ fixture changed')
    deliveries=[r['milliseconds'] for line in irq_stream.read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    skipped=[];results=[];modules=['animation-work.js','cursor-work.js','surface-copy-work.js','mono-sprite-work.js','sprite-work.js','rect-fill-work.js','graphics-work.js','geometry-work.js','resident-resource-work.js','resident-near-work.js','heap-instructions.js','resident-heap-work.js','shape-codec-work.js','shape-conversion-work.js','animation-graphics-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js']
    model_sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(content=model_sources[name].decode('utf-8'))
        for row in rows:
            if any(row['begin']<=t<=row['end'] for t in deliveries):skipped.append(dict(ordinal=row['ordinal'],reason='IRQ within frame'));continue
            payload=gzip.decompress((trace_path.parent/row['memory']['path']).read_bytes())
            if hashlib.sha256(payload).hexdigest()!=row['memory']['sha256'] or len(payload)!=row['memory'].get('ram_images',2)*row['memory']['ram_size']+4*row['instructions']:raise ValueError('Frame memory/path fixture differs')
            # These route frames call a resource-loading caption wrapper, which
            # remains an explicit dependency rather than a free guest call.
            expected_path=memoryview(payload)[row['memory'].get('ram_images',2)*row['memory']['ram_size']:].cast('I')
            main_base=row['samples'][0]['address']-0xc78a
            if not (caption_prefix or caption_allocation or caption_complete) and main_base+0x64a4 in expected_path:skipped.append(dict(ordinal=row['ordinal'],reason='caption resource wrapper'));continue
            actual=page.evaluate('''({row,payload,queueState,mainBase,captionPrefix,captionAllocation,captionComplete})=>{
              let dispatch=0,sample=0,stageChecks=0,stageBytes=0;const recent=[];
              try{
                const bytes=Uint8Array.from(atob(payload),c=>c.charCodeAt(0)),size=row.memory.ram_size,memory=bytes.slice(0,size),path=new DataView(bytes.buffer,bytes.byteOffset+(row.memory.ram_images||2)*size,4*row.instructions);let expected=bytes.slice(size,2*size);
                const assert=(test,message)=>{if(!test)throw new Error(message);},operations={},shapeConverter=captionAllocation||captionComplete?new OriginalShapeConversionWork({memory,ds:row.ds,heap:captionComplete?new OriginalResidentHeapWork({memory,ds:row.ds}):null}):null,adapter=new OriginalAnimationGraphicsWork({memory,ds:row.ds,shapeConverter,onOperation:op=>operations[op.kind]=(operations[op.kind]||0)+1}),state=adapter.state(row.instance);
                const initial=row.samples[0],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:initial.left,maximum:initial.maximum});queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:initial.parts_left,linesDone:initial.lines_done}),clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q)});
                let hash=2166136261;
                const readTick=()=>adapter.view.getUint32(adapter.base+0x201e,true),onInstruction=(label,b)=>{
                  const [region,text]=label.split(':'),address=mainBase+(region==='resident'?0xd510:0)+parseInt(text,16),want=dispatch<row.instructions?path.getUint32(4*dispatch,true):-1;
                  assert(address===want,'Instruction '+dispatch+' differs: '+label+' != '+want.toString(16));dispatch++;recent.push(label);if(recent.length>10)recent.shift();
                  if(captionComplete&&region==='resident'){
                    const i=row.stages.findIndex(s=>s.address===parseInt(text,16));
                    if(i>=0){
                      const native=row.stages[i],start=(3+i)*size,low=16*row.ss+native.stack_low,high=16*row.ss+row.sp,differences=[];
                      for(let a=0;a<size;a++){
                        if(a>=low&&a<high)continue;stageBytes++;
                        if(memory[a]!==bytes[start+a]&&differences.length<12)differences.push({address:a,actual:memory[a],expected:bytes[start+a]});
                      }
                      assert(!differences.length,'Intermediate RAM at '+label+' differs: '+JSON.stringify(differences));stageChecks++;
                    }
                  }
                  for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((address>>>shift)&255),16777619)>>>0;
                  const s=row.samples[sample];if(s&&s.address===address){
                    const actual={budget:b.cycles,left:b.left,maximum:b.maximum,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                    for(const key of Object.keys(actual))assert(actual[key]===s[key],'Clock '+key+' differs at '+label+': '+actual[key]+' != '+s[key]);sample++;
                  }
                };
                const singleStrings=new Set([...OriginalAnimationGraphicsWork.singleStrings,...(captionComplete?OriginalShapeConversionWork.singleStrings:[])]);
                const runner=new OriginalWorkRunner(adapter.frame(state,{readTick}),{singleStrings,onInstruction}),end=clock.run(runner);let complete=end.kind==='complete',observedStack=row.stack_low;
                if(complete){assert(dispatch===row.instructions&&sample===row.samples.length,'Incomplete full frame execution');assert(hash===row.path_hash,'Complete frame path hash differs');assert(!adapter.clipStack.length,'Frame leaves a clip saved');if(captionComplete)assert(stageChecks===row.stages.length,'Missing intermediate stage comparisons');}
                else{
                  const wantedCall=captionAllocation?'allocate-shape':'convert-shape',boundaryOffset=captionAllocation?0x652a:0xd580;
                  assert((captionPrefix||captionAllocation)&&end.kind==='call'&&end.action.call===wantedCall,'Unexpected incomplete frame');assert(row.memory.ram_images>=3&&row.conversion_source,'Missing native conversion boundary');
                  if(captionAllocation){
                    const i=row.stages.findIndex(s=>s.address===boundaryOffset);assert(i>=0,'Missing allocation boundary');const stage=row.stages[i];
                    assert(end.action.bytes===stage.args[0]+65536*stage.args[1],'Allocation size differs');expected=bytes.slice((3+i)*size,(4+i)*size);observedStack=stage.stack_low;
                  }else{assert(end.action.source===row.conversion_source&&end.action.palette===row.conversion_palette,'Conversion input addresses differ');expected=bytes.slice(2*size,3*size);observedStack=row.conversion_stack_low;}
                  // Observe the same post-dispatch/pre-instruction boundary as
                  // the native probe; the conversion body has not run yet.
                  const boundary=new OriginalWorkRunner((function*(){yield 'resident:'+boundaryOffset.toString(16);})(),{onInstruction});assert(clock.run(boundary).kind==='complete','Cannot reach conversion boundary');
                  assert(row.samples[sample-1].address===mainBase+0xd510+boundaryOffset,'Conversion clock sample missing');
                }
                // The independent renderer represents locals as values rather
                // than emulated guest stack bytes. All other captured RAM,
                // including all heap surfaces and VGA memory, must agree.
                const stackBegin=16*row.ss+(observedStack??Math.max(0,row.sp-1024)),stackEnd=16*row.ss+row.sp;let checked=0,changed=0;const differences=[];
                for(let i=0;i<size;i++){
                  if(i>=stackBegin&&i<stackEnd)continue;checked++;if(memory[i]!==bytes[i])changed++;
                  if(memory[i]!==expected[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expected[i]});
                }
                assert(!differences.length,'Frame memory differs: '+JSON.stringify(differences));
                return {passed:true,complete,instructions:dispatch,strings:runner.strings,samples:sample,checkedBytes:checked,changedBytes:changed,stageChecks,stageBytes,operations,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),dispatch,sample,recent};}
            }''',dict(row=row,payload=base64.b64encode(payload).decode(),queueState=queues[row['ordinal']],mainBase=main_base,captionPrefix=caption_prefix,captionAllocation=caption_allocation,captionComplete=caption_complete))
            results.append(dict(ordinal=row['ordinal'],**actual))
            if not actual['passed']:break
        browser.close()
    passed=bool(results) and all(r['passed'] for r in results) and len(results)+len(skipped)==len(rows)
    report=dict(passed=passed,full_frame_coverage=passed and not skipped and all(r.get('complete') for r in results),full_cpu_scheduling_parity=False,frames=len(rows),matching_frames=sum(r['passed'] and r.get('complete',False) for r in results),matching_caption_prefixes=sum(r['passed'] and not r.get('complete',False) for r in results),skipped=skipped,**{key:sum(r.get(key,0) for r in results) for key in ['instructions','strings','samples','checkedBytes','changedBytes','refills']},operations=dict(Counter({kind:sum(r.get('operations',{}).get(kind,0) for r in results) for kind in ['cursor','copy','sprite','fill']})),events=dict(Counter(e['handler'] for r in results for e in r.get('events',[]))),failures=[r for r in results if not r['passed']],models={n:hashlib.sha256(model_sources[n]).hexdigest() for n in modules},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Each complete eligible C78A frame starts from one guest-memory/CPU/queue fixture. Main code, resident geometry, clipping, drawing, cursor and handle-query work share memory and time. All instruction addresses and clock samples compare; all captured RAM outside the observed active guest-stack region (legacy captures use a declared 1 KiB exclusion) compares. With --caption-prefix, caption frames execute up to the independently captured conversion entry and compare input addresses, prefix instructions, clock and memory there. Complete converted-caption frames and IRQ guest execution remain pending; exclusions are explicit. Continuous animation, startup, scanout and live-build integration remain open.')
    report['caption_boundary']='complete-frame' if caption_complete else 'allocation-entry' if caption_allocation else 'conversion-entry' if caption_prefix else None
    report['intermediate_memory_checks']=sum(r.get('stageChecks',0) for r in results)
    report['intermediate_memory_bytes']=sum(r.get('stageBytes',0) for r in results)
    if caption_complete:report['scope']='Complete C78A animation frames including caption resource lookup, palette/conversion planning, allocation, column LZ decode, indexed expansion, resize, rendering and freeing. Each frame uses one initial memory/CPU/queue state; all instruction addresses, clock samples and captured RAM outside its observed active stack compare. IRQ guest execution, continuous scene/startup, live scanout and full-game integration remain separate.'
    if caption_allocation:report['scope']+=' With --caption-allocation, D580/DA63/D5A7 planning continues through the converted-shape allocation entry; native allocation arguments, shared RAM, ordered instructions and clocks compare there.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','control','output']:p.add_argument('--'+name,type=Path,required=True)
    mode=p.add_mutually_exclusive_group()
    for n in ['caption-prefix','caption-allocation','caption-complete']:mode.add_argument('--'+n,action='store_true')
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output,a.caption_prefix,a.caption_allocation,a.caption_complete) else 1)
