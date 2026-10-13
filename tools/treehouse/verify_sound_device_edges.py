"""DSP/DMA register and scheduling-effect edge checks without PCM playback."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False);source=(ROOT/'treehouse-demo/sound-device-work.js').read_bytes()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(content=source.decode())
        checks=page.evaluate('''()=>{
          const checks=[],initial={base:544,irq:7,dmaChannel:1,dspState:2,writeBusy:0,outputUsed:0,pending8:0,pending16:0,command:0,commandLength:0,commandPosition:0,timeConstant:45,frequency:11111,mode:0,dmaMode:0,remaining:0,singleSize:0,baseAddress:0,currentAddress:0,baseCount:0,currentCount:0,page:0,masked:1,request:0,terminalCount:0,autoInit:0,increment:0,speaker:1,type:6,stereo:0,rate:11111,minimum:33};
          const make=(patch={})=>{const effects=[],device=new OriginalSoundDeviceWork({state:{...initial,...patch},effect:e=>effects.push(e)});return {device,effects};};
          for(const seed of [0,6,7,14,15,0xffffffff]){
            const {device}=make({writeBusy:seed}),values=Array.from({length:18},()=>device.read(556)),expected=values.map((_,i)=>(((seed+i+1)>>>0)&8)?255:127);
            checks.push({name:'DSP busy counter '+seed,passed:JSON.stringify(values)===JSON.stringify(expected)&&device.state.writeBusy===((seed+18)>>>0)});
          }
          for(const dspState of [0,1,3]){const {device}=make({dspState,writeBusy:10});checks.push({name:'DSP unavailable '+dspState,passed:device.read(556)===255&&device.state.writeBusy===10});}
          const ack=make({pending8:1,outputUsed:1});const a=ack.device.read(558),b=ack.device.read(558);
          checks.push({name:'DSP acknowledge once, output remains ready',passed:a===255&&b===255&&ack.effects.length===1&&ack.effects[0].kind==='irq-lower'&&!ack.device.state.pending8});
          const dma=make({baseAddress:0xabcd,currentAddress:0x1ffff,baseCount:0x9876,currentCount:0x5432});
          [[12,0],[2,0x34],[2,0x12],[3,0x78],[3,0x56],[131,0x9a],[11,0x71],[10,1]].forEach(([p,v])=>dma.device.write(p,v));
          const d=dma.device.state;checks.push({name:'DMA byte registers, page and mode',passed:d.baseAddress===0x1234&&d.currentAddress===0x1234&&d.baseCount===0x5678&&d.currentCount===0x5678&&d.page===0x9a&&d.autoInit===1&&d.increment===1&&d.masked===0});
          for(const config of [{name:'short audible',count:1,speaker:1,type:6,scheduled:'schedule-end-dma'},{name:'minimum audible',count:33,speaker:1,type:6},{name:'long audible',count:65536,speaker:1,type:6},{name:'silent pre-SB16',count:100,speaker:0,type:4,scheduled:'schedule-silent-dma'},{name:'SB16 speaker ignored',count:100,speaker:0,type:6},{name:'masked transfer',count:1,speaker:1,type:6,masked:1}]){
            const {device,effects}=make({speaker:config.speaker,type:config.type,masked:config.masked||0}),n=config.count-1;
            [20,n&255,n>>>8].forEach(v=>device.write(556,v));const s=device.state,scheduled=effects.filter(e=>e.kind.startsWith('schedule-'));
            const count=Math.min(config.count,33),wanted=config.scheduled;
            checks.push({name:config.name,passed:s.command===0&&s.commandLength===0&&s.commandPosition===0&&s.remaining===config.count&&s.singleSize===0&&s.mode===(config.masked?4:2)&&s.dmaMode===4&&s.request===1&&scheduled.length===Number(!!wanted)&&(!wanted||(scheduled[0].kind===wanted&&scheduled[0].count===count&&scheduled[0].delay===Math.fround(Math.fround(count*1000)/Math.fround(11111))))&&effects.filter(e=>e.kind==='remove-end-dma').length===1});
          }
          for(const constant of [0,166,255]){const {device}=make();device.write(556,64);device.write(556,constant);checks.push({name:'timeconstant rate '+constant,passed:device.state.frequency===Math.floor(1000000/(256-constant))&&device.state.timeConstant===45&&device.state.command===0});}
          for(const mode of [0,2,3,4]){
            const {device,effects}=make({mode,dmaMode:4,remaining:123,dspAutoInit:0});device.write(556,0xd0);
            checks.push({name:'pause DMA mode '+mode,passed:device.state.mode===3&&device.state.remaining===123&&effects.length===1&&effects[0].kind==='remove-end-dma'});
            [20,99,0].forEach(v=>device.write(556,v));
            checks.push({name:'replace paused single-cycle mode '+mode,passed:device.state.mode===4&&device.state.remaining===100&&device.state.dspAutoInit===0&&device.state.command===0});
          }
          const learned=make({masked:0});[20,99,0,208,20,79,0].forEach(v=>learned.device.write(556,v));
          checks.push({name:'single-cycle command establishes replacement ownership',passed:learned.device.state.dspAutoInit===0&&learned.device.state.remaining===80&&learned.device.state.mode===2});
          for(const dspAutoInit of [undefined,1]){
            const {device}=make({mode:3,dmaMode:4,dspAutoInit});let rejected=false;
            try{[20,9,0].forEach(v=>device.write(556,v));}catch(e){rejected=String(e).includes('auto-init ownership');}
            checks.push({name:'reject unknown/auto-init transfer '+dspAutoInit,passed:rejected});
          }
          return checks;
        }''');browser.close()
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,model_sha256=hashlib.sha256(source).hexdigest(),scope='DSP busy/ack/reset status, DMA register bytes/page/mode, command parsing, frequency and generated short/silent DMA scheduling effects. Active PCM production and mixer time are not established.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
