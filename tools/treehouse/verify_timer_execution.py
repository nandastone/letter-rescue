"""Execute each complete timer IRQ against its initial RAM/CPU/PIC fixture."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('IRQ route differs')
    meta=trace['timer_execution'];stream=trace_path.parent/meta['path'];imeta=irq['irq'];istream=irq_path.parent/imeta['path'];initial_path=irq_path.parent/imeta['initial_path']
    for path,digest in [(stream,meta['sha256']),(istream,imeta['sha256']),(initial_path,imeta['initial_sha256'])]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Fixture digest differs')
    rows=[json.loads(s) for s in stream.read_text().splitlines()];ops=[json.loads(s) for s in istream.read_text().splitlines()];deliveries=[i for i,o in enumerate(ops) if o['vector']==8]
    if len(deliveries)!=len(rows) or len(rows)!=meta['calls'] or meta['partial_final_calls']:raise ValueError('Incomplete timer capture or delivery sequence')
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples'][:1]) for r in rows],irq,irq_path)
    modules=['resident-timer-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js','interrupt-controller.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules};results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for n,b in sources.items():page.add_script_tag(content=b.decode())
        for row in rows:
            packed=(trace_path.parent/row['memory']['path']).read_bytes();data=gzip.decompress(packed)
            if len(data)!=2*row['memory']['ram_size'] or hashlib.sha256(data).hexdigest()!=row['memory']['sha256']:raise ValueError('RAM fixture differs')
            # PIC time can move back by one exhausted instruction at a tick
            # rollover. Preserve operation order; use the matching IRQ0
            # admission as the initial controller boundary, never time sorting.
            admission=ops[deliveries[row['ordinal']]]
            if not 0<=row['samples'][0]['milliseconds']-admission['milliseconds']<0.001:raise ValueError('Timer entry does not follow its IRQ admission')
            inside=[o for o in ops[deliveries[row['ordinal']]+1:] if row['samples'][0]['milliseconds']<=o['milliseconds']<=row['samples'][-1]['milliseconds']]
            initial=admission['after']
            result=page.evaluate('''async ({row,packed,queueState,initialPic,expectedOps,residentBase})=>{
              let index=0,operation=0;const recent=[];
              try{
                const compressed=Uint8Array.from(atob(packed),c=>c.charCodeAt(0)),bytes=new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()),size=row.memory.ram_size,memory=bytes.slice(0,size),expected=bytes.subarray(size);
                const assert=(ok,message)=>{if(!ok)throw new Error(message);},same=(a,b)=>Object.keys(b).every(k=>b[k]&&typeof b[k]==='object'?same(a[k],b[k]):a[k]===b[k]);
                assert(JSON.stringify(row.bios_code.slice(0,19))===JSON.stringify([251,254,56,6,0,30,80,82,205,28,250,176,32,230,32,90,88,31,207]),'Unresearched BIOS IRQ0 stub');
                assert(JSON.stringify(row.user_code.slice(0,5))===JSON.stringify([254,56,18,0,207]),'Unresearched BIOS user timer stub');
                const first=row.samples[0],cpu=new OriginalCpuBudget({cycles:first.budget+1,left:first.left,maximum:first.maximum,io:first.io}),pic=new OriginalInterruptController({...initialPic,cycles:cpu.cycles,left:cpu.left,interrupt_enabled:Number(!!(first.flags&512)),trap:0});
                queueState.state={...queueState.state,...cpu.snapshot(),ticks:first.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:first.parts_left,linesDone:first.lines_done}),clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q)});
                const timer=new OriginalResidentTimerWork({memory,ds:row.data_segment}),runner=new OriginalWorkRunner(timer.run(),{onInstruction:(label,b)=>{
                  const [region,offset]=label.split(':'),address=parseInt(offset,16)+(region==='resident'?residentBase:0),s=row.samples[index];
                  assert(s&&s.address===address,'Instruction '+index+' '+label+' != '+s?.address.toString(16));
                  const actual={budget:b.cycles,left:b.left,maximum:b.maximum,io:b.io,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                  for(const key of Object.keys(actual))assert(actual[key]===s[key],key+' at '+label+': '+actual[key]+' != '+s[key]);
                  assert(pic.interrupt_enabled===Number(!!(s.flags&512)),'Interrupt flag at '+label+' differs');
                  index++;recent.push(label);if(recent.length>10)recent.shift();
                }});
                let stop,callbacks=0;
                for(let guard=0;guard<100;guard++){
                  stop=clock.run(runner);if(stop.kind==='complete')break;assert(stop.kind==='call','Unexpected timer suspension');const action=stop.action;
                  if(action.call==='interrupt-flags')pic.interrupt_enabled=Number(action.enabled);
                  else if(action.call==='bios-clock'||action.call==='bios-user-timer')callbacks++;
                  else if(action.call==='port-write'){
                    cpu.port('write');pic.setCpu({...cpu.snapshot(),interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});const native=expectedOps[operation++];
                    assert(native&&native.kind===4&&native.arg===action.port&&native.value===action.value,'PIC output differs');assert(same(pic.snapshot(),native.before),'PIC before output differs');
                    assert(clock.state().milliseconds===native.milliseconds,'PIC output time differs');cpu.interrupt(pic,{kind:4,arg:action.port,value:action.value,interrupt_enabled:pic.interrupt_enabled,trap:pic.trap});
                    assert(same(pic.snapshot(),native.after),'PIC after output differs');
                  }else throw new Error('Unsupported timer action '+action.call);
                  runner.resume();
                }
                assert(stop.kind==='complete'&&index===row.samples.length&&operation===expectedOps.length,'Incomplete IRQ execution');
                const lo=16*row.entry_ss+row.stack_low,hi=16*row.entry_ss+row.entry_sp,differences=[];let checked=0,changed=0;
                for(let i=0;i<size;i++){if(i>=lo&&i<hi)continue;checked++;if(memory[i]!==bytes[i])changed++;if(memory[i]!==expected[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expected[i]});}
                assert(!differences.length,'Timer memory differs '+JSON.stringify(differences));
                return {passed:true,instructions:index,ports:operation,callbacks,chainBios:stop.value.chainBios,checkedBytes:checked,changedBytes:changed,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),index,operation,recent};}
            }''',dict(row=row,packed=base64.b64encode(packed).decode(),queueState=queues[row['ordinal']],initialPic=initial,expectedOps=inside,residentBase=trace['location']['main_base']+0xd510))
            results.append(dict(ordinal=row['ordinal'],**result))
            if not result['passed']:break
        browser.close()
    passed=bool(results) and len(results)==len(rows) and all(r['passed'] for r in results)
    report=dict(passed=passed,full_cpu_scheduling_parity=False,calls=len(rows),matching_calls=sum(r['passed'] for r in results),**{n:sum(r.get(n,0) for r in results) for n in ['instructions','ports','callbacks','checkedBytes','changedBytes','refills']},bios_chains=sum(r.get('chainBios',False) for r in results),events=[e for r in results for e in r.get('events',[])],failures=[r for r in results if not r['passed']],models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Each IRQ0 starts from one initial RAM/CPU/queue/controller state. Resident timer and chained pinned BIOS stubs generate all instructions, every sampled clock/budget/I/O debit, IF transitions, timer/BIOS memory and PIC EOI effects. Expected paths, times and after-memory only compare. Captured RAM outside measured active stack must match. Hardware IRQ delivery, interrupt entry stack/register mechanics, sound/mouse IRQs and continuous interpreter/live integration remain separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
