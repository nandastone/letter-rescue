"use strict";
// Resident IRQ0 handler 6447. Timer delivery and chained BIOS execution are
// separate scheduling components; this model changes only original game state.
class OriginalTimerWork {
  constructor({ticks,countdowns,biosStep,biosPhase}){
    if(!Number.isInteger(ticks)||ticks<0||ticks>0xffffffff||!Number.isInteger(biosStep)||biosStep<0||biosStep>0xffffffff||!Number.isInteger(biosPhase)||biosPhase<0||biosPhase>65535||!Array.isArray(countdowns)||countdowns.length!==4||countdowns.some(v=>!Number.isInteger(v)||v<0||v>65535))throw new Error("Invalid original timer state");
    this.ticks=ticks;this.countdowns=countdowns.slice();this.biosStep=biosStep;this.biosPhase=biosPhase;
  }
  setCountdown(index,value){
    if(!Number.isInteger(index)||index<0||index>3||!Number.isInteger(value)||value<0||value>65535)throw new Error("Invalid countdown write");
    this.countdowns[index]=value;
  }
  tick(){
    const entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x6447,0x6448,0x6449,0x644a,0x644d,0x644f,0x6452,0x6456]);
    if((this.ticks&65535)===65535)add([0x6458]);this.ticks=(this.ticks+1)>>>0;
    for(let i=3;i>=0;i--){
      add([0x645c,0x6461]);if(this.countdowns[i]){add([0x6463]);this.countdowns[i]--;}
      add([0x6467,0x646a]);
    }
    add([0x646c,0x646f,0x6473,0x6477]);
    const total=this.biosPhase+(this.biosStep&65535),chainBios=!!(((this.biosStep>>>16)+(total>>>16))&65535);
    this.biosPhase=total&65535;
    if(chainBios)add([0x647f,0x6480]);else add([0x6479,0x647b,0x647d]);
    add([0x6484,0x6485,0x6486,0x6487]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,chainBios,acknowledgePic:!chainBios};
  }
  snapshot(){return {ticks:this.ticks,countdowns:this.countdowns.slice(),biosStep:this.biosStep,biosPhase:this.biosPhase};}
}
