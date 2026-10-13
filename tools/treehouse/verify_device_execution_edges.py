"""Focused sound/mouse branch checks, separate from full native IRQ fixtures."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False);names=['sound-interrupt-work.js','mouse-interrupt-work.js','cpu-budget.js','work-runner.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in names}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        checks=page.evaluate('''()=>{
          const checks=[],equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
          const setup=()=>{const memory=new Uint8Array(0xb0000),ds=0x3000,base=16*ds,v=new DataView(memory.buffer);return {memory,ds,base,v,put:(at,n)=>v.setUint16(at,n&65535,true),word:at=>v.getUint16(at,true)};};
          function run(generator,slice,read=()=>127){
            const path=[],actions=[],cpu=new OriginalCpuBudget({cycles:slice,left:0,maximum:10000}),runner=new OriginalWorkRunner(generator,{onInstruction:s=>path.push(s)});let stop,interruptEnabled=false;
            for(let guard=0;guard<100000;guard++){
              stop=runner.runSlice(cpu);if(stop.kind==='complete')return {path,actions};if(stop.kind==='exhausted'){cpu.cycles=slice;continue;}
              const a=stop.action;actions.push(a);if(a.call==='stack-segment-credit')cpu.stackSegmentCredit();if(a.call==='interrupt-flags')interruptEnabled=!!a.enabled;runner.resume(a.call==='port-read'?read(a):a.call==='read-interrupt-flag'?interruptEnabled:undefined);
            }throw new Error('Work did not terminate');
          }
          for(const slice of [3,10000]){
            for(const c of [{name:'partial last page',offset:100,last:149,flag:0,low:50,high:0,count:49,nextLow:0,nextHigh:0},{name:'cross page',offset:65520,last:19,flag:1,low:36,high:0,count:15,nextLow:20,nextHigh:0},{name:'full 64KiB block',offset:0,last:65535,flag:1,low:0,high:1,count:65535,nextLow:0,nextHigh:0}]){
              const t=setup(),w=new OriginalSoundInterruptWork({...t,residentSegment:0x1000,soundSegment:0x2000});
              t.put(t.base+0x21e8,0x220);t.put(t.base+0x21fe,c.offset);t.put(t.base+0x2207,c.last);t.put(t.base+0x2203,c.low);t.put(t.base+0x2205,c.high);t.memory[t.base+0x2202]=c.flag;t.memory[t.base+0x21fd]=6;
              let polls=0;const result=run(w.nextBlock(),slice,()=>++polls<4?255:127),out=result.actions.filter(a=>a.call==='port-write').map(a=>[a.port,a.value]);
              const expected=[[10,5],[12,0],[11,73],[2,c.offset&255],[2,c.offset>>>8],[3,c.count&255],[3,c.count>>>8],[131,6],[10,1],[556,20],[556,c.count&255],[556,c.count>>>8]];
              checks.push({name:c.name+' budget '+slice,passed:equal(out,expected)&&polls===6&&t.word(t.base+0x2200)===c.count&&t.word(t.base+0x2203)===c.nextLow&&t.word(t.base+0x2205)===c.nextHigh&&t.word(t.base+0x21fe)===0&&t.memory[t.base+0x21fd]===7&&t.memory[t.base+0x2202]===0});
            }
            const cases=[
              {name:'nonloop completion',flag:1,permission:1,state:0,start:0,end:0,command:6},
              {name:'loop disabled',flag:129,permission:0,state:0,start:0,end:0,command:6},
              {name:'loop whole sound',flag:129,permission:1,state:0,start:0,end:0,command:7,length:100,at:26},
              {name:'loop range',flag:129,permission:1,state:0,start:10,end:80,command:7,length:70,at:36},
              {name:'stop positive state',flag:129,permission:1,state:1,start:10,end:80,command:6},
              {name:'negative state tail',flag:129,permission:1,state:-1,start:10,end:80,command:7,length:20,at:106},
              {name:'negative state empty tail',flag:129,permission:1,state:-1,start:10,end:100,command:6},
              {name:'negative state no end',flag:129,permission:1,state:-1,start:10,end:0,command:6}
            ];
            for(const c of cases){
              const t=setup(),w=new OriginalSoundInterruptWork({...t,residentSegment:0x1000,soundSegment:0x2000}),source=0x50010,calls=[];
              t.put(t.base+0x2120,16);t.put(t.base+0x2122,0x5000);t.put(t.base+0x2128,0x4334);t.put(t.base+0x212a,0x2000);
              t.put(t.base+0x212c,c.permission);t.put(t.base+0x211e,c.state);t.put(t.base+0x211c,123);
              t.memory[source]=c.flag;t.put(source+1,11000);t.put(source+4,100);t.put(source+6,c.start);t.put(source+8,c.end);
              let notified=false;w.dispatch=function*(command,args){calls.push({command,args});};w.notifyCompletion=function*(){notified=true;};
              run(w.completion(),slice);const call=calls[0],loop=c.command===7;
              checks.push({name:c.name+' budget '+slice,passed:calls.length===1&&call.command===c.command&&notified===!loop&&t.word(t.base+0x211c)===(loop?123:0)&&(!loop||(call.args.segment===0x5000&&call.args.offset===c.at&&call.args.length===c.length&&call.args.rate===11000&&t.word(t.base+0x21df)===c.at))&&(c.name!=='negative state tail'||t.word(t.base+0x211e)===1)});
            }
            for(const c of [{name:'busy callback',busy:1,type:1,x:100,y:20,count:0,depth:65535,changed:false},{name:'button only',busy:0,type:2,x:100,y:20,count:0,depth:65535,changed:false},{name:'same position',busy:0,type:1,x:80,y:10,count:0,depth:65535,changed:false},{name:'hidden movement',busy:0,type:1,x:100,y:20,count:65535,depth:65535,changed:true},{name:'deferred movement',busy:0,type:1,x:100,y:20,count:1,depth:65535,changed:true,pending:1},{name:'cursor movement',busy:0,type:1,x:100,y:20,count:0,depth:65535,changed:true,draw:true},{name:'nested drawing',busy:0,type:1,x:100,y:20,count:0,depth:0,changed:true}]){
              const t=setup(),calls=[],w=new OriginalMouseInterruptWork({...t,residentSegment:0x1000,graphics:{*cursor(kind){calls.push(kind);}}});
              t.memory[0x1894c]=c.busy;t.put(t.base+0x206c,320);t.put(t.base+0x2066,40);t.put(t.base+0x2064,10);t.put(t.base+0x2062,c.count);t.put(t.base+0x2102,c.depth);
              run(w.movement(c),slice);
              checks.push({name:c.name+' budget '+slice,passed:t.memory[0x1894c]===0&&t.word(t.base+0x2066)===(c.changed?50:40)&&t.word(t.base+0x2064)===(c.changed?20:10)&&t.word(t.base+0x2102)===c.depth&&t.word(t.base+0x2100)===(c.pending||0)&&equal(calls,c.draw?['hide','restore']:[])});
            }
          }
          return checks;
        }''');browser.close()
    report=dict(passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},scope='Focused DMA block arithmetic/commands, DSP busy polling, loop/stop/tail selection, cursor movement/defer/reentrancy paths under full and tiny CPU slices. Completion dispatch/drawing are stubbed only in branch tests; full native IRQ fixtures separately verify composed callees. No full hardware or live parity claim.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
