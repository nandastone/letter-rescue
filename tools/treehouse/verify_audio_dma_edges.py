"""Focused PCM, mixer and DMA terminal-count cases outside the native route."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    names=['sound-device-work.js','mixer-channel-work.js','sound-dma-work.js','mixer-clock-work.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in names}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        checks=page.evaluate('''()=>{
          const checks=[],same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),check=(name,passed)=>checks.push({name,passed});
          const channelState={enabled:1,done:0,needed:0,frequencyAdd:16384,frequencyCounter:16384,previousLeft:0,previousRight:0,nextLeft:0,nextRight:0,interpolate:0,lastSilence:1,lastStereo:0,offsetLeft:0,offsetRight:0,volumeLeft:1,volumeRight:1};
          const channel=(patch={})=>{const out=[],work=new OriginalMixerChannelWork({state:{...channelState,...patch},output:(l,r)=>out.push(l,r)});return {out,work};};
          const a=channel();a.work.addPcm8Mono(Uint8Array.of(128,255,0));check('unsigned PCM and one-sample history',same(a.out,[0,0,0,0,32512,32512])&&a.work.state.nextLeft===-32768&&a.work.state.done===3);
          const b=channel({frequencyAdd:8192,interpolate:1});b.work.addPcm8Mono(Uint8Array.of(128,255));check('half-rate linear interpolation',same(b.out,[0,0,0,0,0,0,16256,16256])&&b.work.state.frequencyCounter===16384);
          const c=channel({volumeLeft:2,volumeRight:3});c.work.addPcm8Mono(Uint8Array.of(128,127),true);check('signed PCM and channel volumes',same(c.out,[0,0,-65536,-98304]));
          const d=channel({needed:3,previousLeft:8,previousRight:-8,lastStereo:1});d.work.silence();check('stereo silence decay',same(d.out,[8,-8,4,-4,0,0])&&d.work.state.previousLeft===0&&d.work.state.lastSilence===1&&d.work.state.frequencyCounter===16384);
          const e=channel({needed:3,nextLeft:99,nextRight:99,offsetLeft:5,offsetRight:-5});e.work.silence();check('zero silence resets history and phase',same(e.out,[0,0,0,0,0,0])&&e.work.state.nextLeft===0&&e.work.state.nextRight===0&&e.work.state.offsetLeft===0&&e.work.state.offsetRight===0);
          const f=channel();f.work.setFrequency(11111,48000);check('frequency quantization',f.work.state.frequencyAdd===3792&&f.work.state.interpolate===1);f.work.setFrequency(48000,48000);check('equal-rate interpolation off',f.work.state.frequencyAdd===16384&&!f.work.state.interpolate);
          for(const patch of [{},{frequencyAdd:32768,frequencyCounter:32768}]){
            const t=channel(patch),requests=[];t.work.mix(3,n=>{requests.push(n);t.work.addPcm8Mono(new Uint8Array(n).fill(128));});check('mix request sizing '+t.work.state.frequencyAdd,t.work.state.done>=3&&requests[0]===(patch.frequencyAdd?6:3));
          }
          const initial={base:544,irq:7,dmaChannel:1,dspState:2,writeBusy:0,outputUsed:0,pending8:0,pending16:0,command:0,commandLength:0,commandPosition:0,frequency:11111,mode:2,dmaMode:4,remaining:4,singleSize:0,currentAddress:65534,currentCount:3,page:4,masked:0,request:1,terminalCount:0,autoInit:0,increment:0,speaker:1,type:6,stereo:0,rate:11111,minimum:33,dspAutoInit:0};
          function dma(patch={},transferPatch={}){
            const effects=[],device=new OriginalSoundDeviceWork({state:{...initial,...patch},effect:e=>effects.push(e)}),ch=channel(),addresses=[],data=[0,255,0,255];
            const work=new OriginalSoundDmaWork({device,transfer:{autoInit:0,autoSize:0,stereo:0,sign:0,fade:0,multiplier:16384,remainingBytes:0,dma16:0,...transferPatch},channel:ch.work,readByte:at=>{addresses.push(at);return data[(at-(4*65536+65534))&65535]??128;}});
            return {work,device,effects,addresses};
          }
          const g=dma(),pcm=g.work.consume(1,12.5);check('short tail flush and wrapped DMA addresses',pcm.length===4&&same(g.addresses,[327678,327679,262144,262145])&&g.device.state.currentAddress===65538&&g.device.state.currentCount===65535&&g.device.state.masked===1&&g.device.state.mode===0&&g.device.state.dmaMode===0&&g.device.state.pending8===1&&g.work.lastCallback===12.5&&same(g.effects.map(e=>e.kind),['remove-end-dma','irq-raise']));
          const h=dma({pending8:1});h.work.consume(4,10);check('already pending IRQ is not raised twice',same(h.effects.map(e=>e.kind),['remove-end-dma']));
          const i=dma({singleSize:10});i.work.consume(4,10);check('queued single transfer remains owned',i.device.state.remaining===10&&i.device.state.singleSize===0&&i.device.state.mode===4&&i.device.state.dmaMode===4);
          const j=dma({}, {fade:13});check('unsigned startup fade uses truncation',same(Array.from(j.work.consume(4,10)),[128,137,109,157])&&j.work.transfer.fade===9);
          const k=dma({}, {fade:16});check('startup fade leading mute',same(Array.from(k.work.consume(4,10)),[128,128,128,128])&&k.work.transfer.fade===12);
          const l=dma({}, {fade:13,sign:1});check('signed startup fade',same(Array.from(l.work.consume(4,10)),[0,0,0,0])&&l.work.transfer.fade===9);
          const m=dma({remaining:100,currentCount:99,currentAddress:100});m.work.consume(3,10);check('ordinary partial transfer',m.device.state.remaining===97&&m.device.state.currentCount===96&&m.device.state.currentAddress===103&&m.device.state.mode===2&&!m.effects.length);
          for(const patch of [{autoInit:1},{stereo:1},{dma16:1}]){const t=dma({},patch);let rejected=false;try{t.work.consume(1,0);}catch(e){rejected=String(e).includes('requires composition');}check('unsupported format '+JSON.stringify(patch),rejected);}
          function clock(patch={},frontPatch={}){
            const ch=channel(),state={frequency:48000,done:0,needed:0,position:0,tickAdd:805306368,tickCounter:0,blockSize:2048,minimum:0,maximum:4096,noSound:0,...patch};
            const work=new OriginalMixerClockWork({state,frontend:{remaining:0,sampleRate:48000,fps:60,mode:0,rate:60,...frontPatch},channel:ch.work,generate:n=>ch.work.addPcm8Mono(new Uint8Array(n).fill(128))});return {work,ch};
          }
          const n=clock();for(let j=0;j<10;j++)n.work.tick();check('millisecond mixer cadence',n.work.state.done===432&&n.work.state.needed===480&&n.ch.work.state.done===432&&n.work.state.tickCounter===0);
          const o=clock({done:1000,needed:1048},{remaining:0.5});o.ch.work.state.done=1003;const out=o.work.frame();check('frontend sample fraction and buffer consumption',out===800&&o.work.frontend.remaining===0.5&&o.work.state.done===200&&o.work.state.needed===248&&o.ch.work.state.done===203&&o.work.state.position===800);
          const p=clock({done:5000,needed:5048});p.ch.work.state.done=5003;check('frontend overflow drains mixer buffer',p.work.frame()===800&&p.work.state.done===0&&p.work.state.needed===48&&p.ch.work.state.done===3&&p.work.state.position===5000);
          const q=clock({done:10,needed:100});q.ch.work.state.done=10;q.work.fill(0.5);check('fractional fill uses mixer target',q.work.state.done===10&&q.ch.work.state.done===50&&q.ch.work.state.needed===50);
          const r=clock({done:10,needed:100});r.ch.work.state.done=5;r.work.fill(0.5);check('fill skips lagging channel',r.ch.work.state.done===5&&r.ch.work.state.needed===0);
          const u=clock({frequency:44100,tickAdd:739875225});for(let j=0;j<10;j++)u.work.tick();check('fractional mixer tick rounding',u.work.state.needed===440&&u.work.state.tickCounter===16777210);
          const v=clock({done:100,needed:148},{remaining:-1});check('suspended frontend audio retains buffer',v.work.frame()===0&&v.work.state.done===100&&v.work.state.needed===148);
          return checks;
        }''');browser.close()
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},scope='Focused fixed PCM vectors, interpolation/volume/phase, silence decay, source wrapping, partial/terminal DMA, pending IRQ, queued transfer and startup fade. These are source-derived edge checks; native consumption/output proof remains a separate report.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
