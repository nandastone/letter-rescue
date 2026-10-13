"use strict";
// Normal-core work and the PIC event queue share the same mutable CPU budget.
// Hardware handlers and IRQ entry are explicit composition points.
class OriginalExecutionClock {
  constructor({queue,cpu,onEvent,onMillisecond=()=>{},onInterrupts=()=>{}}){
    this.queue=queue;this.cpu=cpu;this.onEvent=onEvent;this.onMillisecond=onMillisecond;this.onInterrupts=onInterrupts;
    this.refills=0;this.milliseconds=0;this.events=[];
  }
  state(){this.queue.setCpuBudget(this.cpu.snapshot());return this.queue.snapshot();}
  refill(){
    const q=this.queue,b=this.cpu;q.setCpuBudget(b.snapshot());
    while(!q.start()){
      q.millisecond();this.milliseconds++;this.onMillisecond(q);
    }
    q.servicing=true;
    while(q.queue.length&&Math.fround(q.queue[0].index*Math.fround(q.maximum))<=Math.fround(q.serviceIndexND)){
      const event={...q.queue[0]};q.service(event.handler,event.value,event.index);
      this.events.push({...event,ticks:q.ticks});this.onEvent(event,q);
    }
    q.servicing=false;q.finish();b.cycles=q.cycles;b.left=q.left;b.maximum=q.maximum;
    this.onInterrupts(b);this.refills++;
  }
  run(runner){
    for(;;){const result=runner.runSlice(this.cpu);if(result.kind!=='exhausted')return result;this.refill();}
  }
}

// Pinned M_VGA/PART event scheduling. The presenter receives each group of
// scanlines at event service, while generated drawing can be between writes.
class OriginalVgaEventWork {
  constructor({delays,partsTotal,partsLines,linesTotal,partsLeft,linesDone,onPart=()=>{},onFrame=()=>{},onLatch=()=>{}}){
    if(delays.length!==5||delays.some(d=>!Number.isFinite(d)||d<=0)||partsTotal<1||partsLines<1||linesTotal<partsLines)throw new Error('Invalid VGA event configuration');
    this.delays=delays.map(Math.fround);this.partsTotal=partsTotal;this.partsLines=partsLines;this.linesTotal=linesTotal;this.partsLeft=partsLeft;this.linesDone=linesDone;
    this.onPart=onPart;this.onFrame=onFrame;this.onLatch=onLatch;
  }
  service(event,q){
    const [vertical,start,panning,interrupt,part]=this.delays;
    if(event.handler===3){
      q.add(3,0,vertical);q.add(1,0,start);q.add(2,0,panning);q.add(6,0,interrupt);
      if(this.partsLeft)q.remove(7);
      this.linesDone=0;this.partsLeft=this.partsTotal;this.onFrame(q);
      q.add(7,this.partsLines,part);
    }else if(event.handler===7){
      if(this.partsLeft<=0||this.linesDone+event.value>this.linesTotal)throw new Error('Invalid VGA part progression');
      this.onPart({firstLine:this.linesDone,lines:event.value,queue:q});this.linesDone+=event.value;
      if(--this.partsLeft)q.add(7,this.partsLeft!==1?this.partsLines:this.linesTotal-this.linesDone,part);
    }else if(event.handler===1||event.handler===2)this.onLatch(event,q);
    else if(event.handler!==6)throw new Error('Non-VGA hardware event needs composition: '+event.handler);
  }
}
