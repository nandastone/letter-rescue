"use strict";
// Periodic PIT0 event phase. IRQ admission and guest timer state are separate.
class OriginalPitClock {
  constructor({counter,index}){
    this.delay=OriginalClockQueue.pitDelay(counter);
    if(!Number.isFinite(index))throw new Error("Invalid PIT event phase");
    this.counter=counter;this.index=Math.fround(index);this.events=0;
  }
  millisecond(){this.index=Math.fround(this.index-1);}
  fire(){const scheduled=this.index;this.index=Math.fround(this.index+this.delay);this.events++;return scheduled;}
}
