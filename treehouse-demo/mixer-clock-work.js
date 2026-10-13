"use strict";
// Pinned mixer cadence for the ordinary, unthrottled capture frontend. The
// emulation host calls tick at TIMER_AddTick and frame at generated VGA handoff.
class OriginalMixerClockWork {
  constructor({state,frontend,channel,generate}){
    this.state={...state};this.frontend={...frontend};this.channel=channel;this.generate=generate;this.frames=0;
    if(state.noSound||state.minimum!==0||frontend.mode!==0||frontend.rate<=0)throw new Error('Mixer frontend mode requires composition');
  }
  tick(){
    const s=this.state;this.channel.mix(s.needed,this.generate);s.done=s.needed;
    s.tickCounter=(s.tickCounter+s.tickAdd)>>>0;s.needed+=s.tickCounter>>>24;s.tickCounter&=16777215;
  }
  fill(index){
    const s=this.state,c=this.channel.state;if(!c.enabled||c.done<s.done)return;
    this.channel.mix(Math.trunc(Math.fround(Math.fround(index)*Math.fround(s.needed))),this.generate);
  }
  frame(){
    const s=this.state,f=this.frontend,wanted=f.sampleRate/f.rate+f.remaining;
    this.frames++;
    if(!wanted||!s.done||f.remaining===-1)return 0;
    const samples=wanted>s.done?s.done:Math.trunc(wanted);
    f.remaining=wanted<=samples||wanted>s.done?0:wanted-samples;
    // With min_needed zero the ordinary callback consumes the requested
    // samples, except an overflow drains the accumulated mixer buffer.
    const reduce=s.done<s.maximum?samples:s.done;
    this.channel.state.done=Math.max(0,this.channel.state.done-reduce);
    s.done-=reduce;s.needed-=reduce;s.position=(s.position+reduce)&16383;
    s.tickAdd=Math.floor(s.frequency*16777216/1000)>>>0;return samples;
  }
}
