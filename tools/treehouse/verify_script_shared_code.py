"""Shared script memory: backwards branches, effective-offset wrap and word loads."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    source=(ROOT/'treehouse-demo/script-work.js').read_bytes()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(content=source.decode())
        checks=page.evaluate('''()=>{
          const checks=[];
          function setup(pc){
            const memory=new Uint8Array(726),view=new DataView(memory.buffer),code=new Uint8Array(65537),reads=[];
            view.setUint16(0x4e,pc,true);
            const state={memory,instance:123,context:456,sound_enabled:1,display_count:0,readCode:at=>{reads.push(at);return code[at];}};
            return {state,view,code,reads};
          }
          function run(t){const calls=[],g=OriginalScriptWork.run(t.state,{readTick:()=>100});let n=g.next();for(let guard=0;guard<10000&&!n.done;guard++){if(typeof n.value!=='string')calls.push(n.value);n=g.next();}if(!n.done)throw new Error('Script failed to terminate');return calls;}
          for(const pc of [65533,65534,65535]){
            const t=setup(pc),at=(pc+1)&65535;t.code[pc]=3;t.code[at]=0x34;t.code[at+1]=0x12;
            if(at===65535)t.code[0]=0x99;
            const calls=run(t);checks.push({name:'sound word effective offset '+at,passed:calls.length===1&&calls[0].call==='sound-start'&&calls[0].id===0x1234&&t.view.getUint16(0x4e,true)===((pc+3)&65535)&&t.state.context===456});
          }
          const t=setup(100);t.code.set([0x14,2,0,0xe9,0xff],100);t.code.set([3,0x78,0x56],80);
          const calls=run(t);checks.push({name:'backwards immediate branch reads earlier shared bytes',passed:calls.length===1&&calls[0].id===0x5678&&t.view.getUint16(0x4e,true)===83&&t.view.getUint16(0x70,true)===2&&t.reads.includes(80)&&t.state.context===456});
          const u=setup(65534);u.code[65534]=0x10;u.code[65535]=0x22;u.code[65536]=0x11;u.code.set([0x33,3,0x44,0x55],0);u.view.setUint32(0x60,1,true);
          const actions=run(u);checks.push({name:'callback word crossing and next opcode wrap',passed:actions.length===2&&actions[0].call==='script-callback'&&actions[0].argument===0x1122&&actions[1].id===0x5544&&u.view.getUint16(0x4e,true)===4});
          return checks;
        }''');browser.close()
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,model_sha256=hashlib.sha256(source).hexdigest(),scope='Shared code bytes, generated backwards branches, wrapped effective offsets and physically contiguous 16-bit operands. Far segment and mutable global integration have separate continuous-loop fixtures.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
