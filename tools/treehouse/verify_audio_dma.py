"""Verify DMA consumption, PCM, mixer phase and output against native calls."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('IRQ route differs')
    meta=trace['audio_dma'];stream=trace_path.parent/meta['path'];imeta=irq['irq'];istream=irq_path.parent/imeta['path']
    for path,digest in [(stream,meta['sha256']),(istream,imeta['sha256'])]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Fixture digest differs')
    rows=list(map(json.loads,stream.read_text().splitlines()))
    if len(rows)!=meta['calls']:raise ValueError('Audio DMA call count differs')
    expected_irqs=[]
    with istream.open() as f:
        for o in map(json.loads,f):
            if o['kind']==1 and o['arg']==7 and rows[0]['milliseconds']<=o['milliseconds']<=rows[-1]['milliseconds']:expected_irqs.append(o['milliseconds'])
    pic_path=irq_path.parent/irq['pic']['path']
    if hashlib.sha256(pic_path.read_bytes()).hexdigest()!=irq['pic']['sha256']:raise ValueError('PIC queue fixture digest differs')
    call_times={r['milliseconds'] for r in rows};expected_removals=[]
    with pic_path.open() as f:
        for o in map(json.loads,f):
            if o['kind']==2 and o['handler']==8 and o['before']['milliseconds'] in call_times:expected_removals.append(o['before']['milliseconds'])
    names=['sound-device-work.js','mixer-channel-work.js','sound-dma-work.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in names}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for b in sources.values():page.add_script_tag(content=b.decode())
        result=page.evaluate('''({rows,expectedIrqs,expectedRemovals})=>{
          const hardwareFields=['base','irq','dmaChannel','dspState','writeBusy','outputUsed','pending8','pending16','command','commandLength','commandPosition','timeConstant','frequency','mode','dmaMode','remaining','singleSize','baseAddress','currentAddress','baseCount','currentCount','page','masked','request','terminalCount','autoInit','increment','speaker','type','stereo','rate','minimum'];
          const dmaFields=['autoInit','autoSize','stereo','sign','fade','multiplier','remainingBytes','dma16'];
          const channelFields=['enabled','done','needed','frequencyAdd','frequencyCounter','previousLeft','previousRight','nextLeft','nextRight','interpolate','lastSilence','lastStereo','offsetLeft','offsetRight','volumeLeft','volumeRight'];
          const from=(fields,data)=>Object.fromEntries(fields.map((k,i)=>[k,data[i]])),assert=(ok,message)=>{if(!ok)throw new Error(message);};
          const result={calls:rows.length,matchingCalls:0,pcmBytes:0,mixedFrames:0,hardwareChecks:0,channelChecks:0,transferChecks:0,fadeCalls:0,terminalCalls:0,irqs:[],removals:[],failures:[]};
          for(const row of rows){
            try{
              const source=Uint8Array.from(row.source.match(/../g),h=>parseInt(h,16)),expectedPcm=Uint8Array.from(row.pcm.match(/../g),h=>parseInt(h,16)),effects=[],mixed=[];
              const device=new OriginalSoundDeviceWork({state:{...from(hardwareFields,row.hardware_before),dspAutoInit:row.dma_before[0]},effect:e=>effects.push(e)});
              const channel=new OriginalMixerChannelWork({state:from(channelFields,row.channel_before),output:(l,r)=>mixed.push(l,r)});
              const pageBase=device.state.page*65536,start=device.state.currentAddress&65535;
              const dma=new OriginalSoundDmaWork({device,transfer:from(dmaFields,row.dma_before),channel,readByte:address=>{
                const offset=(address-pageBase-start)&65535;assert(address>=pageBase&&address<pageBase+65536&&offset<1024,'Read outside initial DMA source');return source[offset];
              }});dma.lastCallback=row.last_before;
              const pcm=dma.consume(row.requested,row.milliseconds);
              for(let i=0;i<pcm.length;i++)assert(pcm[i]===expectedPcm[i],'PCM byte '+i+': '+pcm[i]+' != '+expectedPcm[i]);
              assert(mixed.length===row.mixed_delta.length,'Mixed frame count '+mixed.length/2+' != '+row.frames);
              for(let i=0;i<mixed.length;i++)assert(mixed[i]===row.mixed_delta[i],'Mixed sample '+i+': '+mixed[i]+' != '+row.mixed_delta[i]);
              for(const [fields,state,after] of [[hardwareFields,device.state,row.hardware_after],[dmaFields,dma.transfer,row.dma_after],[channelFields,channel.state,row.channel_after]]){
                for(let i=0;i<fields.length;i++)assert(state[fields[i]]===after[i],fields[i]+': '+state[fields[i]]+' != '+after[i]);
              }
              assert(dma.lastCallback===row.last_after,'Last DMA callback time differs');
              assert(JSON.stringify(row.mixer_before)===JSON.stringify(row.mixer_after),'Unexpected global mixer mutation');
              for(const effect of effects){
                if(effect.kind==='irq-raise'){assert(effect.irq===7,'Unexpected IRQ line');result.irqs.push(row.milliseconds);}
                else if(effect.kind==='remove-end-dma')result.removals.push(row.milliseconds);
                else throw new Error('Unexpected DMA effect '+effect.kind);
              }
              result.matchingCalls++;result.pcmBytes+=pcm.length;result.mixedFrames+=mixed.length/2;result.hardwareChecks+=32;result.transferChecks+=8;result.channelChecks+=16;
              result.fadeCalls+=Number(row.dma_before[4]>0);result.terminalCalls+=Number(row.hardware_before[20]!==65535&&device.state.currentCount===65535);
            }catch(e){result.failures.push({ordinal:row.ordinal,milliseconds:row.milliseconds,error:String(e)});break;}
          }
          result.irqTimesMatch=JSON.stringify(result.irqs)===JSON.stringify(expectedIrqs);result.removalTimesMatch=JSON.stringify(result.removals)===JSON.stringify(expectedRemovals);return result;
        }''',dict(rows=rows,expectedIrqs=expected_irqs,expectedRemovals=expected_removals));browser.close()
    passed=result['matchingCalls']==len(rows) and not result['failures'] and result['irqTimesMatch'] and result['removalTimesMatch']
    report=dict(passed=passed,full_sound_hardware_parity=False,continuous_scheduling_parity=False,**result,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Every captured GenerateDMASound call starts from its own initial device/transfer/channel state and source PCM bytes. Generated PCM, signed-32-bit mixer output contributions, counters, phase, flags and IRQ effects compare to native. Requests and call times are fixtures here; continuous mixer cadence, host audio consumption, final clipping/resampling and live integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
