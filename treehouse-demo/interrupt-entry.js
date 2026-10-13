"use strict";
// Real-mode hardware entry/16-bit IRET at the pinned CPU boundary. The caller
// materializes lazy arithmetic flags before entry and charges the IRET opcode.
// Entry and these stack/register operations do not debit additional CPU work.
class OriginalInterruptEntry {
  constructor({memory,state}){
    this.memory=memory;this.state=state;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);
  }
  word(address){return this.view.getUint16(address,true);}
  put(address,value){this.view.setUint16(address,value&65535,true);}
  stackAdvance(bytes){
    const s=this.state,esp=s.registers[4];return ((esp&s.stack_notmask)|((esp+bytes)&s.stack_mask))>>>0;
  }
  push(value){const s=this.state,next=this.stackAdvance(-2);this.put(s.ss_base+((next&s.stack_mask)>>>0),value);s.registers[4]=next;}
  pop(){const s=this.state,value=this.word(s.ss_base+((s.registers[4]&s.stack_mask)>>>0));s.registers[4]=this.stackAdvance(2);return value;}
  enter(vector,{tableBase=0,returnIp=this.state.eip}={}){
    if(!Number.isInteger(vector)||vector<0||vector>255)throw new Error('Invalid real-mode interrupt vector');
    const s=this.state;this.push(s.flags);this.push(s.segments[1]);this.push(returnIp);
    s.flags=(s.flags&~0x300)>>>0;s.eip=this.word(tableBase+4*vector);s.segments[1]=this.word(tableBase+4*vector+2);s.cs_base=16*s.segments[1];s.code_big=0;
  }
  iret(){
    const s=this.state;s.eip=this.pop();s.segments[1]=this.pop();s.cs_base=16*s.segments[1];const flags=this.pop(),mask=(0x7fd5|s.extflags_toggle)>>>0;
    s.flags=((s.flags&~mask)|(flags&mask)|2)>>>0;s.direction=1-((s.flags&0x400)>>>9);s.code_big=0;
  }
}
