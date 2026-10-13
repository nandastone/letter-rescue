"use strict";
// Integer mixer-channel state from the pinned reference: sample phase,
// interpolation, volume and silence decay. Output is signed-32-bit accumulation
// before final clipping/resampling by the host audio sink.
class OriginalMixerChannelWork {
  constructor({state,output=()=>{}}){this.state={...state};this.output=output;}
  sample(left,right){const s=this.state;this.output(Math.imul(left,s.volumeLeft),Math.imul(right,s.volumeRight));s.done++;}
  addPcm8Mono(data,signed=false){
    const s=this.state;if(!Number.isInteger(s.frequencyAdd)||s.frequencyAdd<=0)throw new Error('Invalid mixer frequency increment');
    s.lastStereo=0;let position=0;
    for(;;){
      while(s.frequencyCounter>=16384){
        if(position>=data.length){s.lastSilence=0;return;}
        s.frequencyCounter-=16384;s.previousLeft=s.nextLeft;
        const value=data[position++];s.nextLeft=(signed?((value<<24)>>24):value-128)*256;
      }
      const sample=s.interpolate?s.previousLeft+Math.floor((s.nextLeft-s.previousLeft)*(s.frequencyCounter&16383)/16384):s.previousLeft;
      this.sample(sample,sample);s.frequencyCounter+=s.frequencyAdd;
    }
  }
  silence(){
    const s=this.state;
    if(s.done<s.needed){
      if(!s.previousLeft&&!s.previousRight){
        while(s.done<s.needed)this.sample(0,0);
        s.nextLeft=s.nextRight=0;s.frequencyCounter=16384;
      }else{
        const decay=n=>n>4?n-4:n<-4?n+4:0;
        while(s.done<s.needed){
          s.nextLeft=decay(s.previousLeft);s.nextRight=decay(s.previousRight);
          this.sample(s.previousLeft,s.lastStereo?s.previousRight:s.previousLeft);
          s.previousLeft=s.nextLeft;s.previousRight=s.nextRight;s.frequencyCounter=16384;
        }
      }
    }
    s.lastSilence=1;s.offsetLeft=s.offsetRight=0;
  }
  setFrequency(frequency,outputRate){
    if(!Number.isInteger(frequency)||frequency<=0||!Number.isInteger(outputRate)||outputRate<=0)throw new Error('Invalid mixer sample rate');
    this.state.frequencyAdd=Math.floor(frequency*16384/outputRate);this.state.interpolate=Number(frequency!==outputRate);
  }
  mix(needed,generate){
    const s=this.state;s.needed=needed;
    let guard=0;
    while(s.enabled&&s.needed>s.done){
      if(++guard>1000000)throw new Error('Mixer source failed to satisfy its request');
      const count=Math.min(4096,Math.ceil((s.needed-s.done)*s.frequencyAdd/16384));generate(count);
    }
  }
  snapshot(){return {...this.state};}
}
