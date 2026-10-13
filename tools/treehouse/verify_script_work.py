"""Compare generated intrinsic SCR interpreter work with original invocations."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output,drawing=False):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());meta=trace['script_work']
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    path=trace_path.parent/meta['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=meta['sha256']:raise ValueError('Script work digest differs')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    if len(rows)!=meta['records'] or sum(r['repeats'] for r in rows)!=meta['calls']:raise ValueError('Script call counts differ')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/script-work.js'))
        if drawing:page.add_script_tag(path=str(ROOT/'treehouse-demo/animation-work.js'))
        page.evaluate('value=>window.composeDrawing=value',drawing)
        page.evaluate('''()=>{
          window.scriptReport={records:0,calls:0,instructions:0,drawingInstructions:0,fullMemoryCalls:0,delegatedMemoryCalls:0,actions:{},opcodes:{},failures:[]};
          window.fromHex=s=>Uint8Array.from(s.match(/../g)||[],h=>parseInt(h,16));
          window.hex=b=>Array.from(b,n=>n.toString(16).padStart(2,'0')).join('');
        }''')
        for start in range(0,len(rows),100):
            ok=page.evaluate('''rows=>{
              const r=scriptReport;
              for(const row of rows){
                const state={...row.before,memory:fromHex(row.before.memory),code:fromHex(row.before.code)},counts={},drawingCounts={},actions=[];
                let hash=2166136261,drawingHash=2166136261,instructions=0,drawingInstructions=0,index=0,currentTick=null;
                try{
                  if((row.before.ticks>>>16)!==(row.after.ticks>>>16))throw new Error('Capture needs separate high-word timer observations at rollover');
                  const readTick=at=>{
                    if([0xbde0,0xbe15,0xbe8f,0xbec6,0xbf0c,0xc799].includes(at)){
                      if(index>=row.tick_reads.length)throw new Error('Missing timer operand');currentTick=row.tick_reads[index++];
                    }
                    if(currentTick===null)throw new Error('High word read before low word');return currentTick;
                  };
                  const compose=function*(g){
                    let n=g.next();
                    while(!n.done){
                      const s=n.value;let answer;
                      if(composeDrawing&&typeof s!=='string'&&['frame-update','scene-compose','slot-bounds'].includes(s.call)){
                        actions.push({call:s.call,slot:s.slot});
                        answer=yield* compose(s.call==='frame-update'?OriginalAnimationWork.frame(state,{readTick}):s.call==='scene-compose'?OriginalAnimationWork.compose(state):OriginalAnimationWork.bounds(state,s.slot));
                      }else answer=yield s;
                      n=g.next(answer);
                    }return n.value;
                  };
                  const g=compose(OriginalScriptWork.run(state,{readTick}));let next=g.next();
                  for(let guard=0;!next.done&&guard<100000;guard++){
                    const step=next.value;
                    if(typeof step==='string'){
                      const at=parseInt(step.split(':')[1],16);
                      if(at>=0xc78a&&at<0xcd40){
                        drawingCounts[at]=(drawingCounts[at]||0)+1;drawingInstructions++;
                        for(let shift=0;shift<32;shift+=8)drawingHash=Math.imul(drawingHash^((at>>>shift)&255),16777619)>>>0;
                      }else{
                        counts[at]=(counts[at]||0)+1;instructions++;
                        for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((at>>>shift)&255),16777619)>>>0;
                      }
                      next=g.next();
                    }else{
                      actions.push({call:step.call,id:step.id,slot:step.slot});
                      // The intrinsic proof stops at named callees. It does not
                      // supply expected after-memory as a substitute for them.
                      if(step.call==='sound-status'||step.call==='script-callback')throw new Error('Callee return needs independent composition');
                      if(step.call==='slot-reset'){
                        const at=0x78+step.slot*0x22;state.memory.fill(0,at,at+0x22);const v=new DataView(state.memory.buffer);v.setUint16(at+6,2,true);v.setUint32(at+0xa,0x80000000,true);v.setUint32(at+0xe,0x80000000,true);
                      }
                      next=g.next(step.call==='shape-header'?{height:state.dimensions[2*step.shape],width:state.dimensions[2*step.shape+1]}:undefined);
                    }
                  }
                  if(!next.done||index!==row.tick_reads.length)throw new Error('Unconsumed interpreter work or timer reads');
                  const differences={};
                  if(next.value!==row.result)differences.result={expected:row.result,actual:next.value};
                  if(hash!==row.path_hash)differences.path_hash={expected:row.path_hash,actual:hash};
                  const all=new Set([...Object.keys(counts),...Object.keys(row.counts)]),bad={};
                  for(const at of all)if((counts[at]||0)!==(row.counts[at]||0))bad[at]={expected:row.counts[at]||0,actual:counts[at]||0};
                  if(Object.keys(bad).length)differences.counts=bad;
                  if(composeDrawing){
                    if(drawingHash!==row.drawing_hash)differences.drawing_hash={expected:row.drawing_hash,actual:drawingHash};
                    const allDrawing=new Set([...Object.keys(drawingCounts),...Object.keys(row.drawing_counts)]),badDrawing={};
                    for(const at of allDrawing)if((drawingCounts[at]||0)!==(row.drawing_counts[at]||0))badDrawing[at]={expected:row.drawing_counts[at]||0,actual:drawingCounts[at]||0};
                    if(Object.keys(badDrawing).length)differences.drawing_counts=badDrawing;
                  }
                  for(const name of ['context','display_count'])if(state[name]!==row.after[name])differences[name]={expected:row.after[name],actual:state[name]};
                  const delegated=!composeDrawing&&actions.some(a=>['frame-update','scene-compose','slot-bounds'].includes(a.call)),expected=fromHex(row.after.memory),memory=[];
                  for(let i=0;i<state.memory.length;i++)if((!delegated||(i>=0x4e&&i<0x56)||(i>=0x5a&&i<0x5c))&&state.memory[i]!==expected[i])memory.push({offset:i,expected:expected[i],actual:state.memory[i]});
                  if(memory.length)differences.memory=memory;
                  if(Object.keys(differences).length){r.failures.push({ordinal:row.ordinal,differences,actions});return false;}
                  r.records++;r.calls+=row.repeats;r.instructions+=instructions*row.repeats;r.drawingInstructions+=drawingInstructions*row.repeats;r[delegated?'delegatedMemoryCalls':'fullMemoryCalls']+=row.repeats;
                  const opcode=state.code[0];r.opcodes[opcode]=(r.opcodes[opcode]||0)+row.repeats;
                  for(const action of actions)r.actions[action.call]=(r.actions[action.call]||0)+row.repeats;
                }catch(e){r.failures.push({ordinal:row.ordinal,error:String(e),actions});return false;}
              }
              return true;
            }''',rows[start:start+100])
            if not ok:break
        result=page.evaluate('()=>scriptReport')
        checks=page.evaluate('''()=>{
          if(!composeDrawing)return [];
          const make=()=>{const s={instance:100,memory:new Uint8Array(726),drawing:[0,0,0,0]},v=OriginalAnimationWork.view(s);
            v.put(0x14,50);v.put(0x16,50);v.put(0x78,1);v.put(0x7a,1);v.put(0x7c,3);v.put(0x29c,7);return s;};
          const drive=g=>{let n=g.next(),calls=[],path=[];
            while(!n.done){const s=n.value;if(typeof s==='string')path.push(s);else calls.push(s.call);n=g.next(s.call==='shape-header'?{width:10,height:10}:undefined);}return {calls,path};};
          const frame=s=>drive(OriginalAnimationWork.frame(s,{readTick:()=>65537})),view=s=>OriginalAnimationWork.view(s);
          const a=make();frame(a);const av=view(a);
          const b=make();view(b).put(0x78,3);frame(b);
          const c=make();view(c).put(0x7e,0x1000);frame(c);
          const d=make();view(d).put(0x78,3);view(d).put(0x7e,0x2000);frame(d);
          const e=make();view(e).put(0x7e,0x3000);frame(e);
          const f=make();view(f).put(0x7e,0x0100);frame(f);const f1=view(f).word(0x78);frame(f);
          const g=make();view(g).put32(0x82,0x18000);view(g).put32(0x86,0x28000);view(g).put32(0x8a,0x18000);view(g).put32(0x8e,0xffff0000);view(g).put32(0x92,0x8000);view(g).put32(0x96,0x8000);frame(g);
          const h=make();view(h).put32(0x82,0xffff0000);view(h).put32(0x86,0xffff0000);drive(OriginalAnimationWork.bounds(h,0));
          const i=make();view(i).put32(0x82,60<<16);drive(OriginalAnimationWork.bounds(i,0));
          return [
            {name:'display increments and stamps both timer words',passed:av.word(0x58)===1&&av.dword(0x5c)===65537},
            {name:'forward frame advances',passed:av.word(0x78)===2},
            {name:'forward end wraps to first',passed:view(b).word(0x78)===1},
            {name:'reverse first wraps to last',passed:view(c).word(0x78)===3},
            {name:'ping-pong end reverses direction',passed:view(d).word(0x78)===2&&(view(d).word(0x7e)&0x1000)!==0},
            {name:'ping-pong first restores forward direction',passed:view(e).word(0x78)===2&&(view(e).word(0x7e)&0x1000)===0},
            {name:'frame delay compares the old counter',passed:f1===1&&view(f).word(0x78)===2},
            {name:'movement and acceleration preserve fixed-point carry',passed:view(g).dword(0x82)===0x30000&&view(g).dword(0x86)===0x18000&&view(g).dword(0x8a)===0x20000&&view(g).dword(0x8e)===0xffff8000},
            {name:'bounds intersect negative position with surface',passed:[0,2,4,6].map(n=>view(h).signed(0x46+n)).join(',')==='0,0,9,9'},
            {name:'outside bounds leave dirty rectangle empty',passed:[0,2,4,6].every(n=>view(i).word(0x46+n)===0)}
          ];
        }''');browser.close()
    report=dict(passed=not result['failures'] and result['calls']==meta['calls'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,**result,checks=checks,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/script-work.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),script_sha256=meta['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Intrinsic BDA0 interpreter instruction counts and ordered paths, return values, restored context and display count. Calls without drawing/bounds callees compare all 726 instance bytes; other calls compare only interpreter-owned PC/scratch/delay fields. Every native call is covered through exact-state/work coalescing. Initial instance/code and timer operands are explicit fixtures. Callee execution, caller loops and generated scheduling remain separate; no expected callee after-memory is injected.')
    if drawing:
        report['drawing_model_sha256']=hashlib.sha256((ROOT/'treehouse-demo/animation-work.js').read_bytes()).hexdigest()
        report['scope']='Composed interpreter/frame/scene/slot bounds intrinsic instructions, ordered hashes and all 726 instance bytes for every invocation. Initial instance/code, shape dimensions, scene flags and timer operands are explicit fixtures; no expected after-memory is injected. Resident graphics, resource and sound callee execution and generated CPU scheduling remain uncomposed. Pixel output is not compared by this component check.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--drawing',action='store_true')
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output,a.drawing) else 1)
