"""Focused timer/BIOS edge cases, independent of native delivery fixtures."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False);names=['resident-timer-work.js','timer-work.js','cpu-budget.js','work-runner.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in names}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for n,b in sources.items():page.add_script_tag(content=b.decode())
        checks=page.evaluate('''()=>{
          const checks=[];
          const cases=[
            {name:'ordinary tick',ticks:0,phase:0,step:19886,bios:1,motor:2,flag:0},
            {name:'low tick carry',ticks:65535,phase:0,step:19886,bios:1,motor:0,flag:0},
            {name:'full tick wrap',ticks:0xffffffff,phase:0,step:19886,bios:1,motor:0,flag:0},
            {name:'BIOS phase carry',ticks:0,phase:65535,step:19886,bios:50,motor:2,flag:0},
            {name:'BIOS midnight and motor stop',ticks:0,phase:0,step:65536,bios:0x1800af,motor:1,flag:255},
            {name:'BIOS zero motor saturates',ticks:0,phase:0,step:65536,bios:0,motor:0,flag:0},
            {name:'BIOS high ADC wraps',ticks:0,phase:1,step:0xffffffff,bios:0,motor:1,flag:0}
          ];
          for(const input of cases)for(const slice of [3,10000]){
            const memory=new Uint8Array(0x50000),v=new DataView(memory.buffer),ds=0x2000,base=16*ds,put=(a,n)=>v.setUint16(a,n&65535,true),countdowns=[0,1,2,65535];
            v.setUint32(base+0x201e,input.ticks,true);countdowns.forEach((n,i)=>put(base+0x2016+2*i,n));v.setUint32(base+0x2030,input.step,true);put(base+0x2034,input.phase);
            put(base+0x202a,0xfea5);put(base+0x202c,0xf000);put(0x70,0x1240);put(0x72,0xf000);
            v.setUint32(0x46c,input.bios,true);memory[0x440]=input.motor;memory[0x470]=input.flag;memory[0x43f]=0xab;const before=memory.slice();
            const old=new OriginalTimerWork({ticks:input.ticks,countdowns,biosStep:input.step,biosPhase:input.phase}),expectedWork=old.tick(),expected=old.snapshot(),path={},ports=[];
            const timer=new OriginalResidentTimerWork({memory,ds}),runner=new OriginalWorkRunner(timer.run(),{onInstruction:label=>{if(label.startsWith('resident:')){const key=parseInt(label.slice(9),16);path[key]=(path[key]||0)+1;}}}),cpu=new OriginalCpuBudget({cycles:slice,left:0,maximum:10000});let end,callbacks=0,enabled=0;
            for(let guard=0;guard<10000;guard++){
              end=runner.runSlice(cpu);if(end.kind==='complete')break;
              if(end.kind==='exhausted'){cpu.cycles=slice;continue;}
              const a=end.action;
              if(a.call==='port-write'){cpu.port('write');ports.push([a.port,a.value]);}
              else if(a.call==='interrupt-flags')enabled=Number(a.enabled);
              else if(a.call==='bios-clock'||a.call==='bios-user-timer')callbacks++;
              else throw new Error('Unexpected action');runner.resume();
            }
            const ticks=v.getUint32(base+0x201e,true),counts=countdowns.map((_,i)=>v.getUint16(base+0x2016+2*i,true)),chain=expectedWork.chainBios,biosNext=chain?input.bios+1:input.bios,midnight=chain&&biosNext>=0x1800b0;
            const allowed=new Set([...Array.from({length:12},(_,i)=>base+0x2016+i),base+0x2034,base+0x2035,0x43f,0x440,0x46c,0x46d,0x46e,0x46f,0x470]);
            const passed=end.kind==='complete'&&end.value.chainBios===chain&&ticks===expected.ticks&&JSON.stringify(counts)===JSON.stringify(expected.countdowns)&&v.getUint16(base+0x2034,true)===expected.biosPhase&&JSON.stringify(path)===JSON.stringify(expectedWork.entries)&&callbacks===2*Number(chain)&&JSON.stringify(ports)==='[[32,32]]'&&!enabled&&v.getUint32(0x46c,true)===(midnight?0:biosNext)&&memory[0x470]===((input.flag+Number(midnight))&255)&&memory[0x440]===(chain&&input.motor?input.motor-1:input.motor)&&memory[0x43f]===(chain&&input.motor===1?0xa0:0xab)&&memory.every((n,i)=>allowed.has(i)||n===before[i]);
            checks.push({name:input.name+' budget '+slice,passed});
          }return checks;
        }''');browser.close()
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},scope='Focused generated timer state/work, BIOS midnight/motor behavior, callback/port/IF effects and write extent with full and tiny instruction budgets. Does not establish hardware delivery or real-time scheduling.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
