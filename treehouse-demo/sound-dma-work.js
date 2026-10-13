"use strict";
// Eight-bit mono PCM consumption from shared DMA registers and guest memory.
// The mixer/clock host decides when and how many samples to request.
class OriginalSoundDmaWork {
  constructor({device,transfer,channel,readByte}){this.device=device;this.transfer={...transfer};this.channel=channel;this.readByte=readByte;this.lastCallback=0;}
  consume(requested,milliseconds){
    const s=this.device.state,t=this.transfer;
    if(!Number.isInteger(requested)||requested<0||!Number.isFinite(milliseconds))throw new Error('Invalid DMA consumption request');
    if(s.dmaMode!==4||t.stereo||t.dma16)throw new Error('DMA format requires composition');
    if(t.autoInit||s.autoInit)throw new Error('Auto-init DMA consumption requires composition');
    this.lastCallback=milliseconds;
    const count=Math.min(1024,s.remaining<=s.minimum?s.remaining:requested);
    s.currentAddress&=65535;const available=s.currentCount+1,read=Math.min(count,available),pcm=new Uint8Array(read);
    if(read>s.remaining)throw new Error('DMA request exceeds remaining DSP transfer');
    for(let i=0;i<read;i++)pcm[i]=this.readByte(s.page*65536+((s.currentAddress+i)&65535));
    if(count<available){s.currentAddress+=count;s.currentCount-=count;}
    else{
      s.terminalCount=1;s.currentAddress+=available;s.currentCount=65535;s.masked=1;
      // ReachedTC's callback is ignored by the DSP. The mask callback sees
      // lastCallback == now, so catch-up has zero samples to consume.
      if(s.mode===2)s.mode=4;
    }
    if(t.fade){
      const length=Math.min(read,t.fade);let factor=13-t.fade;t.fade-=length;
      for(let i=0;i<length;i++,factor++){
        const value=t.sign?(pcm[i]<<24)>>24:pcm[i]-128;
        pcm[i]=(Math.trunc(value*Math.max(0,factor)/13)+(t.sign?0:128))&255;
      }
    }
    this.channel.addPcm8Mono(pcm,!!t.sign);s.remaining-=read;
    if(!s.remaining){
      this.device.emit('remove-end-dma');
      if(!s.pending8){s.pending8=1;this.device.emit('irq-raise',{irq:s.irq});}
      if(!s.singleSize){s.mode=0;s.dmaMode=0;}
      else{s.remaining=s.singleSize;s.singleSize=0;}
    }
    return pcm;
  }
}
