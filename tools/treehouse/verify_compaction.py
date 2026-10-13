"""Compare generated heap relocation with a read-only native callback subspan."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]

def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-core control')
    if trace['events']!=irq['events']:raise ValueError('Different reference route')
    meta=trace['activity_backdrop'];stream=trace_path.parent/meta['path']
    if hashlib.sha256(stream.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Callback fixture digest differs')
    rows=[json.loads(s) for s in stream.read_text().splitlines()];resident=trace['location']['main_base']+0xd510
    spans=[]
    for row in rows:
        starts=[c for c in row['checkpoints'] if c['address']==resident+0x6b06]
        for start in starts:
            end=next(c for c in row['checkpoints'] if c['address']==resident+0x6bb2 and c['instruction']>start['instruction'])
            samples=row['samples'][start['instruction']:end['instruction']+1]
            buffers=[]
            for c in [start,end]:
                data=gzip.decompress((trace_path.parent/c['path']).read_bytes())
                if hashlib.sha256(data).hexdigest()!=c['sha256']:raise ValueError('Checkpoint RAM digest differs')
                buffers.append(data)
            span=dict(row,samples=samples,ordinal=len(spans),stack_low=min(s['sp'] for s in samples))
            spans.append((span,buffers))
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples'][:1]) for r,_ in spans],irq,irq_path,tick_order=True)
    modules=['resident-resource-work.js','resident-near-work.js','heap-instructions.js','resident-heap-work.js','resident-compaction-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js']
    sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules};results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for data in sources.values():page.add_script_tag(content=data.decode())
        for row,buffers in spans:
            result=page.evaluate('''({row,buffers,queueState,resident})=>{
              let count=0;const recent=[];
              try{
                const assert=(ok,msg)=>{if(!ok)throw new Error(msg);},[memory,expected]=buffers.map(b=>Uint8Array.from(atob(b),c=>c.charCodeAt(0))),first=row.samples[0];
                const cpu=new OriginalCpuBudget({cycles:first.budget+1,left:first.left,maximum:first.maximum,io:first.io});
                queueState.state={...queueState.state,...cpu.snapshot(),ticks:first.ticks,servicing:0};
                const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:first.parts_left,linesDone:first.lines_done});
                const clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(e,q)=>{assert(e.handler!==4&&e.handler!==8,'Hardware interrupt event needs full host');vga.service(e,q);}});
                const view=new DataView(memory.buffer),arg=16*first.ss+first.sp+4,bytes=view.getUint32(arg,true),work=new OriginalResidentCompactionWork({memory,ds:row.data_segment});
                const runner=new OriginalWorkRunner(work.compact(bytes),{singleStrings:OriginalResidentCompactionWork.singleStrings,onInstruction:(label,b)=>{
                  const address=resident+parseInt(label.split(':')[1],16),s=row.samples[count];
                  assert(s&&address===s.address,'Instruction '+count+' '+label+' != '+s?.address.toString(16));
                  const actual={budget:b.cycles,left:b.left,maximum:b.maximum,io:b.io,ticks:q.ticks,parts_left:vga.partsLeft,lines_done:vga.linesDone,milliseconds:clock.state().milliseconds};
                  for(const key of Object.keys(actual))assert(actual[key]===s[key],key+' at '+label+': '+actual[key]+' != '+s[key]);
                  count++;recent.push(label);if(recent.length>10)recent.shift();
                }});
                const stop=clock.run(runner);assert(stop.kind==='complete','Uncomposed compaction action');assert(count===row.samples.length,'Incomplete path');
                const stackStart=16*first.ss+row.stack_low,stackEnd=16*first.ss+first.sp,differences=[];let checked=0,changed=0;
                const original=Uint8Array.from(atob(buffers[0]),c=>c.charCodeAt(0));
                for(let i=0;i<memory.length;i++){if(i>=stackStart&&i<stackEnd)continue;checked++;if(memory[i]!==original[i])changed++;if(memory[i]!==expected[i]&&differences.length<20)differences.push({address:i,actual:memory[i],expected:expected[i]});}
                assert(!differences.length,'RAM mismatch '+JSON.stringify(differences));
                assert(stop.value===row.samples.at(-1).ax+65536*row.samples.at(-1).dx,'Returned free bytes differ');
                return {passed:true,instructions:count,strings:runner.strings,checkedBytes:checked,changedBytes:changed,requestedBytes:bytes,returnedBytes:stop.value,refills:clock.refills,events:clock.events};
              }catch(e){return {passed:false,error:String(e),instructions:count,recent};}
            }''',dict(row=row,buffers=[base64.b64encode(b).decode() for b in buffers],queueState=queues[row['ordinal']],resident=resident))
            results.append(result)
        browser.close()
    report=dict(passed=bool(results) and all(r['passed'] for r in results),results=results,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Native 6B06 compaction entry through pre-RETF, from initial shared RAM and clock/queue. Every instruction and clock sample, returned free space, and all RAM outside measured active stack. Component evidence only; callback and live integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
