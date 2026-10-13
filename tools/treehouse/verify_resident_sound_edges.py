"""Resident sound API and driver flag/stop branch checks, separate from native proof."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    names=['resident-sound-work.js','resident-resource-work.js','sound-interrupt-work.js','cpu-budget.js','work-runner.js']
    sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in names}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        checks=page.evaluate('''()=>{
          const checks=[],check=(name,passed)=>checks.push({name,passed});
          const setup=()=>{
            const memory=new Uint8Array(0xb0000),ds=0x3000,base=16*ds,v=new DataView(memory.buffer),put=(at,n)=>v.setUint16(at,n&65535,true),word=at=>v.getUint16(at,true);
            const driver=new OriginalSoundInterruptWork({memory,ds,residentSegment:0x1000,soundSegment:0x2000}),work=new OriginalResidentSoundWork({memory,ds,driver});
            return {memory,base,put,word,driver,work};
          };
          function run(generator,slice,enabled=true,inputs=[]){
            const actions=[],path=[],cpu=new OriginalCpuBudget({cycles:slice,left:0,maximum:10000}),runner=new OriginalWorkRunner(generator,{onInstruction:s=>path.push(s)});let reads=0;
            for(let guard=0;guard<100000;guard++){
              const stop=runner.runSlice(cpu);if(stop.kind==='complete')return {result:stop.value,enabled,actions,path,reads};
              if(stop.kind==='exhausted'){cpu.cycles=slice;continue;}
              const a=stop.action;actions.push(a);let value;
              if(a.call==='read-interrupt-flag')value=enabled;
              else if(a.call==='interrupt-flags')enabled=!!a.enabled;
              else if(a.call==='port-read'){if(reads>=inputs.length)throw new Error('Unexpected port read');value=inputs[reads++];}
              else if(a.call==='stack-segment-credit')cpu.stackSegmentCredit();
              else if(a.call!=='port-write')throw new Error('Unexpected action '+a.call);
              runner.resume(value);
            }throw new Error('Branch did not finish');
          }
          for(const slice of [3,10000]){
            for(const [name,flags,type] of [['prepared',0x2000,1],['non-digital',0x1000,2]]){
              const t=setup(),handle=0x100;t.put(t.base+handle,flags);t.put(t.base+handle+2,0x5000);t.memory[0x50006]=type;
              const r=run(t.work.prepare(handle),slice);check(name+' '+slice,r.result===handle&&r.path.includes('resident:e958')&&t.word(t.base+handle)===(name==='prepared'?flags:flags|0x1f0));
            }
            for(const [offset,segment,wanted] of [[0,0,7],[16,0x5000,1],[32,0x6000,2],[48,0x7000,4],[0,0x5001,0],[16,0x6000,0]]){
              const t=setup();for(const [status,pointer,at,seg,value] of [[0x211c,0x2120,16,0x5000,1],[0x2132,0x2136,32,0x6000,2],[0x2144,0x2148,48,0x7000,4]]){t.put(t.base+status,value);t.put(t.base+pointer,at);t.put(t.base+pointer+2,seg);}
              const r=run(t.work.status({offset,segment}),slice);check('status '+offset+':'+segment+' '+slice,r.result===wanted);
            }
            for(const enabled of [false,true]){
              for(const matched of [false,true]){
                const t=setup(),calls=[];t.put(t.base+0x211c,1);t.put(t.base+0x2120,16);t.put(t.base+0x2122,0x5000);
                t.driver.dispatch=function*(command){calls.push(command);};t.driver.notifyCompletion=function*(){calls.push('notify');};
                const r=run(t.work.stopDigital({offset:matched?16:17,segment:0x5000}),slice,enabled);
                check('stop match '+matched+' IF '+enabled+' '+slice,r.enabled===enabled&&t.word(t.base+0x211c)===Number(!matched)&&JSON.stringify(calls)===JSON.stringify(matched?[3,'notify']:[]));
              }
              const t=setup();t.put(t.base+0x21e8,0x220);t.put(t.base+0x21eb,1);
              const pause=run(t.driver.pause(),slice,enabled,[127,255,255,127]),writes=pause.actions.filter(a=>a.call==='port-write');
              check('pause polling IF '+enabled+' '+slice,pause.enabled===enabled&&pause.reads===4&&writes.length===1&&writes[0].port===556&&writes[0].value===208);
              const vector=4*15;t.put(vector,0x1234);t.put(vector+2,0x5678);
              const install=run(t.driver.installVector(7),slice,enabled);check('install preserves IF '+enabled+' '+slice,install.enabled===enabled&&t.word(vector)===0x4d3c&&t.word(vector+2)===0x2000);
              const restore=run(t.driver.restoreVector(7),slice,enabled);check('restore preserves IF '+enabled+' '+slice,restore.enabled===enabled&&t.word(vector)===0x1234&&t.word(vector+2)===0x5678);
            }
            const t=setup();check('null handle '+slice,run(t.work.playHandle(0),slice).result===0);
            check('driver command five noop '+slice,run(t.driver.dispatch(5),slice).actions.length===0);
          }
          return checks;
        }''');browser.close()
    report=dict(passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},scope='Focused prepared/nondigital resources, far-pointer identity/status, digital stop selection, DSP pause polling and vector IF preservation under tiny/full budgets. Stop selection stubs its driver/completion only; complete prepared native starts separately prove composition. No continuous or live parity claim.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
