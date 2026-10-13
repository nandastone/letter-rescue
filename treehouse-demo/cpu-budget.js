"use strict";
// Pinned normal-core budget rules. Execution paths supply ordered instruction,
// string, stack-segment and I/O operations; this does not decode guest code.
class OriginalCpuBudget {
  constructor({cycles,left,maximum,io=0}){
    if([cycles,left,maximum].some(v=>!Number.isInteger(v)||v<-2147483648||v>2147483647)||maximum<=0||!Number.isSafeInteger(io))throw new Error("Invalid CPU budget state");
    this.cycles=cycles;this.left=left;this.maximum=maximum;this.io=io;
  }
  dispatch(){return this.cycles-->0;}
  stringIteration(){return --this.cycles>0;}
  stackSegmentCredit(){this.cycles++;}
  port(direction){
    if(direction!=='read'&&direction!=='write')throw new Error("Invalid I/O direction");
    const debit=Math.min(Math.trunc(this.maximum/(direction==='read'?1024:1365)),this.cycles);
    this.cycles-=debit;this.io+=debit;return debit;
  }
  snapshot(){return {cycles:this.cycles,left:this.left,maximum:this.maximum,io:this.io};}
  consume({instructions,strings=0,credits=0,ioDebit=0}){
    if([instructions,strings,credits].some(v=>!Number.isSafeInteger(v)||v<0)||!Number.isSafeInteger(ioDebit))throw new Error("Invalid normal CPU work");
    this.cycles-=instructions+strings+ioDebit-credits;this.io+=ioDebit;
  }
  interrupt(controller,{kind,arg=0,value=0,interrupt_enabled,trap}){
    controller.setCpu({cycles:this.cycles,left:this.left,interrupt_enabled,trap});
    const vector=controller.apply(kind,arg,value);
    this.cycles=controller.cycles;this.left=controller.left;return vector;
  }
  finish(exit){
    if(!['callback','exhausted','early'].includes(exit))throw new Error("Invalid normal CPU exit");
    if(exit==='exhausted')this.cycles--;
    return this.snapshot();
  }
  static normalRun(state,{instructions,strings=0,credits=0,ioDebit=0,exit}){
    const b=new OriginalCpuBudget(state);
    b.consume({instructions,strings,credits,ioDebit});return b.finish(exit);
  }
  static callback(kind,state,{bytes}={}){
    const b=new OriginalCpuBudget(state);
    if(kind==='file-read'){
      const result=OriginalResourceWork.dosTransfer(bytes,b.cycles,b.io);b.cycles=result.cycles;b.io=result.io;
    }else if(!['mouse-position','keyboard-poll','file-seek','bios-clock','bios-user-timer','bios-device-post','mouse-irq','mouse-return','mouse-user-return'].includes(kind))throw new Error("Unreconstructed callback budget");
    return b.snapshot();
  }
}
