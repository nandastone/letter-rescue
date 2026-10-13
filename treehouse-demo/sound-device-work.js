"use strict";
// Pinned DSP status/command and channel-1 DMA register behavior. Mixer work and
// event scheduling are explicit host effects, shared with the execution clock.
// This module does not synthesize PCM or silently consume active audio.
class OriginalSoundDeviceWork {
  constructor({state,effect}){
    this.state={...state};this.effect=effect;this.parameters=[];this.flipflop=null;
    if(state.command||state.commandPosition)throw new Error('Initial DSP parameters require composition');
    if(state.dmaChannel!==1)throw new Error('Sound DMA channel other than one requires composition');
  }
  emit(kind,fields={}){if(!this.effect)throw new Error('Sound device effect requires a host: '+kind);return this.effect({kind,...fields});}
  read(port){
    const s=this.state;
    if(port===s.base+14){if(s.pending8){s.pending8=0;this.emit('irq-lower',{irq:s.irq});}return s.outputUsed?255:127;}
    if(port===s.base+12){if(s.dspState!==2)return 255;s.writeBusy=(s.writeBusy+1)>>>0;return s.writeBusy&8?255:127;}
    throw new Error('Unsupported sound input port '+port);
  }
  checkEnd(){
    const s=this.state;if(!s.remaining)return;
    if(!s.speaker&&s.type!==6){const count=Math.min(s.remaining,s.minimum);this.emit('schedule-silent-dma',{count,delay:Math.fround(Math.fround(count*1000)/Math.fround(s.rate))});}
    else if(s.remaining<s.minimum)this.emit('schedule-end-dma',{count:s.remaining,delay:Math.fround(Math.fround(s.remaining*1000)/Math.fround(s.rate))});
  }
  changeMode(mode){
    const s=this.state;if(s.mode===mode)return;this.emit('mixer-fill',{mode:s.mode});s.mode=mode;
  }
  mask(masked){
    const s=this.state;s.masked=Number(masked);
    if(masked&&s.mode===2)throw new Error('Masking active DMA requires mixer catch-up composition');
    if(!masked&&s.mode===4&&s.dmaMode!==0){this.changeMode(2);this.checkEnd();}
  }
  write(port,value){
    if(!Number.isInteger(value)||value<0||value>255)throw new Error('Invalid sound port byte');
    const s=this.state;
    if(port===s.base+12){this.writeDsp(value);return;}
    if(port===10){if((value&3)!==1)throw new Error('Unsupported DMA mask channel');this.mask(!!(value&4));}
    else if(port===12)this.flipflop=false;
    else if(port===11){if((value&3)!==1)throw new Error('Unsupported DMA mode channel');s.autoInit=Number(!!(value&16));s.increment=Number(!!(value&32));}
    else if(port===0x83)s.page=value;
    else if(port===2||port===3){
      if(this.flipflop===null)throw new Error('Initial DMA flip-flop requires composition');this.flipflop=!this.flipflop;
      const fields=port===2?['baseAddress','currentAddress']:['baseCount','currentCount'];
      for(const name of fields)s[name]=this.flipflop?(s[name]&0xff00)|value:(s[name]&255)|(value<<8);
    }else throw new Error('Unsupported sound output port '+port);
  }
  writeDsp(value){
    const s=this.state;
    if(!s.command){
      if(value===0xd0){s.mode=3;this.emit('remove-end-dma');s.commandLength=s.commandPosition=0;return;}
      if(![0x14,0x40].includes(value))throw new Error('Unsupported DSP command '+value);
      s.command=value;s.commandLength=value===0x14?2:1;s.commandPosition=0;this.parameters=[];return;
    }
    this.parameters.push(value);s.commandPosition++;
    if(s.commandPosition<s.commandLength)return;
    if(s.command===0x40){
      const frequency=Math.floor(1000000/(256-this.parameters[0]));
      if(s.frequency!==frequency&&s.dmaMode!==0){
        this.emit('mixer-fill',{mode:s.mode});this.emit('mixer-frequency',{frequency:Math.floor(frequency/(s.stereo?2:1))});
        if(s.dmaMode!==4)throw new Error('Non-PCM DMA rate requires composition');s.rate=frequency*(s.stereo?2:1);s.minimum=Math.floor(s.rate*3/1000);
      }s.frequency=frequency;
    }else{
      // Old-format, single-cycle, unsigned eight-bit PCM (DSP command 14).
      if(s.mode>=2&&s.dspAutoInit!==0)throw new Error('Replacing active DMA requires known DSP auto-init ownership');
      s.singleSize=1+this.parameters[0]+256*this.parameters[1];this.emit('mixer-fill',{mode:s.mode});
      s.pending8=s.pending16=0;this.emit('irq-lower',{irq:s.irq});
      s.remaining=s.singleSize;s.singleSize=0;s.dmaMode=4;s.dspAutoInit=0;s.rate=s.frequency*(s.stereo?2:1);s.minimum=Math.floor(s.rate*3/1000);
      this.emit('mixer-frequency',{frequency:Math.floor(s.frequency/(s.stereo?2:1))});this.emit('remove-end-dma');
      s.mode=4;this.mask(s.masked);s.request=1;
    }
    s.command=s.commandLength=s.commandPosition=0;this.parameters=[];
  }
  snapshot(){return {...this.state};}
}
