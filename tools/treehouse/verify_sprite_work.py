"""Compare generated sprite pixels, instruction paths and continuous draw-loop clocks."""
from pathlib import Path
from collections import Counter
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_copy_execution import initial_queues

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('Independent IRQ route events differ')
    path=trace_path.parent/trace['sprites']['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=trace['sprites']['sha256']:raise ValueError('Sprite digest differs')
    irq_stream=irq_path.parent/irq['irq']['path']
    if hashlib.sha256(irq_stream.read_bytes()).hexdigest()!=irq['irq']['sha256']:raise ValueError('IRQ digest differs')
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    queues=initial_queues([dict(ordinal=r['ordinal'],slices=r['samples']) for r in rows],irq,irq_path)
    deliveries=[r['milliseconds'] for line in irq_stream.read_text().splitlines() if (r:=json.loads(line))['vector']>=0]
    skipped=Counter();modes=Counter();results=[]
    modules=['sprite-work.js','mono-sprite-work.js','rect-fill-work.js','cpu-budget.js','work-runner.js','clock-queue.js','execution-clock.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        for row in rows:
            payload=gzip.decompress((trace_path.parent/row['pixels']['path']).read_bytes())
            if hashlib.sha256(payload).hexdigest()!=row['pixels']['sha256']:raise ValueError('Sprite pixel digest differs')
            if len(payload)!=row['source_size']+(2*row['destination_size'] if row['drawn'] else 0):raise ValueError('Sprite pixel length differs')
            clock=bool(row['drawn']) and not any(row['begin']<=t<=row['end'] for t in deliveries)
            if not clock:skipped['IRQ in complete sprite call' if row['drawn'] else 'clipped empty']+=1
            actual=page.evaluate('''({row,pixels,queueState,clockEnabled})=>{
              try{
                const payload=Uint8Array.from(atob(pixels),c=>c.charCodeAt(0)),sourcePixels=payload.slice(0,row.source_size),beforePixels=payload.slice(row.source_size,row.source_size+row.destination_size),expected=payload.slice(row.source_size+row.destination_size),input={...row,sourcePixels,beforePixels};
                const counts={},samples=row.samples.filter(s=>[0xa209,0xa0d8].includes(s.address));let hash=2166136261,dispatch=0;
                const model=[OriginalSpriteWork,OriginalMonoSpriteWork,OriginalRectFillWork][row.kind],g=model.run(input);let next=g.next();
                while(!next.done){const step=next.value;let answer;
                  if(typeof step==='string'){
                    const at=parseInt(step.split(':')[1],16);counts[at]=(counts[at]||0)+1;
                    for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((at>>>shift)&255),16777619)>>>0;
                  }else if(['rep-move-words','rep-store-words'].includes(step.call)){
                    const s=samples[dispatch++];if(!s||s.remaining!==step.remaining)throw new Error('Sprite REP operands differ');answer=Math.min(step.remaining,Math.max(1,s.budget));
                  }
                  next=g.next(answer);
                }
                if(dispatch!==samples.length)throw new Error('Unconsumed sprite REP samples');
                const result=next.value;let different=0,first=[];
                if(result.drawn){
                  if(expected.length!==result.pixels.length)throw new Error('Sprite output size differs');
                  for(let i=0;i<expected.length;i++)if(result.pixels[i]!==expected[i]){different++;if(first.length<8)first.push({at:i,expected:expected[i],actual:result.pixels[i]});}
                }
                let execution=null;
                if(clockEnabled){
                  const gen=model.run(input),entry=['resident:a197','resident:9f5b','resident:a0a9'][row.kind];let pending=gen.next();while(!pending.done&&pending.value!==entry)pending=gen.next();
                  if(pending.done)throw new Error('No sprite loop entry');
                  const initial=row.samples[0],cpu=new OriginalCpuBudget({cycles:initial.budget+1,left:initial.left,maximum:initial.maximum});
                  queueState.state={...queueState.state,...cpu.snapshot(),ticks:initial.ticks,servicing:0};
                  const q=new OriginalClockQueue(queueState),vga=new OriginalVgaEventWork({delays:row.video_delays,partsTotal:row.parts_total,partsLines:row.parts_lines,linesTotal:row.lines_total,partsLeft:initial.parts_left,linesDone:initial.lines_done});
                  const clock=new OriginalExecutionClock({queue:q,cpu,onEvent:(event,q)=>vga.service(event,q)}),budgets=[];
                  const runner=new OriginalWorkRunner(gen,{first:pending,singleStrings:model.singleStrings,onInstruction:(address,b)=>{
                    const at=parseInt(address.split(':')[1],16);
                    if([0xa197,0xa231,0xa209,0xa23c,0x9f5b,0x9fd6,0x9fbe,0xa0a9,0xa0d8,0xa0e3,0xa0c5].includes(at))budgets.push({address:at,budget:b.cycles,left:b.left,maximum:b.maximum,ticks:q.ticks,milliseconds:clock.state().milliseconds,parts_left:vga.partsLeft,lines_done:vga.linesDone});
                  }});
                  const stop=clock.run(runner);if(stop.kind!=='call'||stop.action.call!=='cursor-restore')throw new Error('Unexpected draw-loop exit');
                  execution={samples:budgets,instructions:runner.instructions,strings:runner.strings,refills:clock.refills,milliseconds:clock.milliseconds,events:clock.events};
                }
                return {drawn:result.drawn,writes:result.writes,strings:result.strings,counts,hash,dispatches:dispatch,different,first,execution};
              }catch(e){return {error:String(e)};}
            }''',dict(row=row,pixels=base64.b64encode(payload).decode(),queueState=queues.get(row['ordinal']),clockEnabled=clock))
            differences={}
            if 'error' in actual:differences['error']=actual['error']
            else:
                for key,expected in [('hash',row['path_hash']),('drawn',bool(row['drawn'])),('different',0)]:
                    if actual[key]!=expected:differences[key]=dict(expected=expected,actual=actual[key])
                bad={k:dict(expected=row['counts'].get(k,0),actual=actual['counts'].get(k,0)) for k in row['counts'].keys()|actual['counts'].keys() if row['counts'].get(k,0)!=actual['counts'].get(k,0)}
                if bad:differences['counts']=bad
                if clock:
                    expected=[{k:v for k,v in s.items() if k!='remaining'} for s in row['samples']]
                    if actual['execution']['samples']!=expected:differences['clock']=dict(expected=expected,actual=actual['execution']['samples'])
            results.append(dict(ordinal=row['ordinal'],passed=not differences,differences=differences,actual=actual));modes[['indexed','mask','fill'][row.get('kind',0)]+':'+str(row['mode'])]+=1
            if differences:break
        checks=page.evaluate('''()=>{
          const drive=g=>{let n=g.next();while(!n.done)n=g.next(['rep-move-words','rep-store-words'].includes(n.value.call)?n.value.remaining:undefined);return n.value;};
          const checks=[],surface=[0,0x2000,0,0,6,8,8,0,0,0,6,8,0,0,6,8],rows=[0,8,16,24,32,40];
          for(let mode=0;mode<16;mode++)for(const width of [1,2,3,4]){
            const stride=width+2,source=Array.from({length:3*stride},(_,i)=>i%3===0?0:(i*17+9)&255),before=Array.from({length:48},(_,i)=>40+i),expected=before.slice();
            for(let y=0;y<3;y++)for(let x=0;x<width;x++){
              const pixel=source[y*stride+x],at=(y+1)*8+x+2,a=pixel^(mode&4?255:0),op=mode&3;
              if(mode===8){if(pixel)expected[at]=0;}
              else if(mode===10){if(pixel)expected[at]=pixel;}
              else expected[at]=op===0?a:op===1?a&before[at]:op===2?a|before[at]:a^before[at];
            }
            const r=drive(OriginalSpriteWork.run({mode,x:2,y:1,shape:[3,width,stride],surface,rows,sourcePixels:source,beforePixels:before}));
            checks.push({name:'mode '+mode+' width '+width+' with source padding',passed:r.drawn&&r.pixels.every((v,i)=>v===expected[i])});
          }
          const source=Array.from({length:20},(_,i)=>i+1),base={mode:0,x:-2,y:-1,shape:[4,5,5],surface,rows,sourcePixels:source,beforePixels:Array(48).fill(0)};
          const clipped=drive(OriginalSpriteWork.run(base)),expected=Array(48).fill(0);for(let y=0;y<3;y++)for(let x=0;x<3;x++)expected[y*8+x]=source[(y+1)*5+x+2];
          checks.push({name:'negative positions clip source and destination',passed:clipped.width===3&&clipped.height===3&&clipped.pixels.every((v,i)=>v===expected[i])});
          const empty=drive(OriginalSpriteWork.run({...base,x:20}));checks.push({name:'fully clipped sprite leaves destination unchanged',passed:!empty.drawn&&empty.writes===0});
          const shared=new Uint8Array(48),g=OriginalSpriteWork.run({...base,x:0,y:0,destinationPixels:shared});let n=g.next();while(n.value?.call!=='rep-move-words')n=g.next();n=g.next(1);
          checks.push({name:'partial sprite copy is visible before completion',passed:shared[0]===1&&shared[1]===2&&shared[2]===0&&!n.done});
          for(let mode=0;mode<8;mode++)for(const color of [0,0x5a,0xff]){
            let passed=true;
            for(const width of [1,2,3,4]){
              const stride=width+2,source=Array.from({length:3*stride},(_,i)=>i%3===0?0:(i*17+9)&255),before=Array.from({length:48},(_,i)=>40+i),expected=before.slice(),ink=color^(mode&4?255:0);
              for(let y=0;y<3;y++)for(let x=0;x<width;x++){
                const pixel=source[y*stride+x],at=(y+1)*8+x+2,a=pixel&ink,op=mode&3;
                if(op===0){if(pixel)expected[at]=ink;}else expected[at]=op===1?before[at]&(~a&255):op===2?before[at]|a:before[at]^a;
              }
              const r=drive(OriginalMonoSpriteWork.run({mode,color,x:2,y:1,shape:[3,width,stride],surface,rows,sourcePixels:source,beforePixels:before}));
              passed=passed&&r.drawn&&r.pixels.every((v,i)=>v===expected[i]);
            }
            checks.push({name:'mask mode '+mode+' colour '+color+' across padded odd/even widths',passed});
          }

          for(let mode=0;mode<8;mode++)for(const width of [1,2,3,4]){
            const before=Array.from({length:48},(_,i)=>40+i),expected=before.slice(),color=0x5a,ink=color^(mode&4?255:0),op=mode&3;
            for(let y=1;y<4;y++)for(let x=2;x<2+width;x++){const at=y*8+x;expected[at]=op===0?ink:op===1?before[at]&ink:op===2?before[at]|ink:before[at]^ink;}
            const r=drive(OriginalRectFillWork.run({mode,color,rect:[1,2,4,2+width],surface,rows,beforePixels:before}));
            checks.push({name:'fill mode '+mode+' width '+width,passed:r.drawn&&r.pixels.every((v,i)=>v===expected[i])});
          }
          for(const [name,rect,writes] of [['clipped',[-2,-2,2,2],4],['left',[0,-4,2,-1],0],['right',[0,9,2,10],0],['above',[-4,0,-1,2],0],['below',[7,0,8,2],0]]){
            const r=drive(OriginalRectFillWork.run({mode:0,color:99,rect,surface,rows,beforePixels:Array(48).fill(0)}));
            checks.push({name:'fill '+name,passed:r.writes===writes&&r.pixels.filter(v=>v===99).length===writes});
          }
          const fillPixels=new Uint8Array(48),fg=OriginalRectFillWork.run({mode:0,color:55,rect:[0,0,2,4],surface,rows,destinationPixels:fillPixels});let fn=fg.next();while(fn.value?.call!=='rep-store-words')fn=fg.next();fn=fg.next(1);
          checks.push({name:'partial fill publishes shared word immediately',passed:fillPixels[0]===55&&fillPixels[1]===55&&fillPixels[2]===0&&!fn.done});
          return checks;
        }''');browser.close()
    passed=all(r['passed'] for r in results+checks) and len(results)==trace['sprites']['calls']
    report=dict(passed=passed,full_cpu_scheduling_parity=False,calls=len(results),matching_calls=sum(r['passed'] for r in results),instructions=sum(sum(r['actual'].get('counts',{}).values()) for r in results),pixels_written=sum(r['actual'].get('writes',0) for r in results),modes=dict(modes),clock_calls=sum(bool(r['actual'].get('execution')) for r in results),clock_samples=sum(len(r['actual']['execution']['samples']) for r in results if r['actual'].get('execution')),clock_skipped=dict(skipped),refills=sum(r['actual']['execution']['refills'] for r in results if r['actual'].get('execution')),events=dict(Counter(e['handler'] for r in results if r['actual'].get('execution') for e in r['actual']['execution']['events'])),failures=[r for r in results if not r['passed']],checks=checks,models={n:hashlib.sha256((ROOT/'treehouse-demo'/n).read_bytes()).hexdigest() for n in modules},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='All captured VGA sprites compare generated indexed pixels, intrinsic instruction counts and ordered hashes. REP budgets are fixtures for that intrinsic comparison. Separate uninterrupted draw-loop execution generates all later CPU/queue/VGA samples from one initial state, excluding IRQ-containing calls explicitly. Cursor helper execution and whole-game integration remain separate; expected pixels never drive writes.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'checks':dict(total=len(checks),failures=[c for c in checks if not c['passed']])},indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','irq','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
