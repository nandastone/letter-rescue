"use strict";
// Runs generated guest instructions against a shared OriginalCpuBudget. A
// suspended guest call is composed by the caller; it is not a CPU callback.
// Queue/IRQ admission belongs outside this normal-core execution slice.
class OriginalWorkRunner {
  constructor(generator,{first=null,singleStrings=new Set(),onInstruction=()=>{}}={}){
    this.generator=generator;this.pending=first??generator.next();this.singleStrings=singleStrings;this.onInstruction=onInstruction;
    this.instructions=0;this.strings=0;this.calls=0;
  }
  resume(value){
    if(this.pending.done||typeof this.pending.value==='string'||['rep-move-words','rep-store-words','rep-move-bytes','rep-store-bytes'].includes(this.pending.value.call))throw new Error('No suspended guest callee');
    this.pending=this.generator.next(value);
  }
  runSlice(cpu){
    for(;;){
      if(this.pending.done)return {kind:'complete',value:this.pending.value};
      const step=this.pending.value;
      if(typeof step==='string'){
        if(!cpu.dispatch())return {kind:'exhausted'};
        this.instructions++;this.onInstruction(step,cpu.snapshot());
        // A non-REP string executes once even at a zero post-dispatch budget.
        if(this.singleStrings.has(step)){cpu.stringIteration();this.strings++;}
        this.pending=this.generator.next();
      }else if(['rep-move-words','rep-store-words','rep-move-bytes','rep-store-bytes'].includes(step.call)){
        const completed=Math.min(step.remaining,Math.max(1,cpu.cycles));
        cpu.consume({instructions:0,strings:completed});this.strings+=completed;
        // Resume immediately: the model publishes these writes before queue
        // service or interrupt admission can observe the shared framebuffer.
        this.pending=this.generator.next(completed);
      }else{
        this.calls++;return {kind:'call',action:step};
      }
    }
  }
}
