"use strict";
// One original digital channel. Source bytes and loop bounds come from SND;
// interpolation and silence decay follow the pinned 48 kHz reference mixer.
class OriginalPcmMixer {
  constructor(){this.voice=null;this.previous=0;this.next=0;this.phase=16384;this.step=0;}
  start(voice){this.voice={...voice,position:0};this.step=Math.floor(voice.rate*16384/48000);}
  stop(id){if(this.voice?.id===id)this.voice=null;}
  release(id){if(this.voice?.id===id)this.voice.loop=false;}
  sample(){
    if(this.voice){
      while(this.phase>=16384){
        const v=this.voice,end=v.loop?v.loopEnd:v.pcm.length;
        if(v.position>=end){if(v.loop)v.position=v.loopStart;else{this.voice=null;break;}}
        this.phase-=16384;this.previous=this.next;this.next=(v.pcm[v.position++]-128)*256;
      }
      if(this.voice){const value=this.previous+((this.next-this.previous)*this.phase>>14);this.phase+=this.step;return value/32768;}
    }
    const value=this.previous;
    this.previous=Math.sign(value)*Math.max(0,Math.abs(value)-4);this.next=this.previous;this.phase=16384;
    return value/32768;
  }
}

function originalAudioWorkletSource(){return `${OriginalPcmMixer.toString()}
class TreehouseDigitalChannel extends AudioWorkletProcessor {
  constructor(){super();this.mixer=new OriginalPcmMixer();this.samples=new Map();this.events=[];
    this.port.onmessage=({data})=>{if(data.type==='barrier'){this.port.postMessage({barrier:data.token});return;}if(data.type==='sample'){this.samples.set(data.key,new Uint8Array(data.pcm));return;}
      this.events.push(data);this.events.sort((a,b)=>a.frame-b.frame||a.order-b.order);};}
  process(inputs,outputs){const out=outputs[0][0];
    for(let i=0;i<out.length;i++){
      while(this.events.length&&this.events[0].frame<=currentFrame+i){const e=this.events.shift();
        if(e.type==='start'){const prior=this.mixer.voice?.id;if(prior!==undefined)this.port.postMessage({ended:prior});this.mixer.start({...e,pcm:this.samples.get(e.key)});}
        else if(e.type==='stop')this.mixer.stop(e.id);else if(e.type==='release')this.mixer.release(e.id);}
      const prior=this.mixer.voice?.id;out[i]=this.mixer.sample();
      if(prior!==undefined&&!this.mixer.voice)this.port.postMessage({ended:prior});
    }return true;}
}
registerProcessor('treehouse-digital-channel',TreehouseDigitalChannel);`;}
