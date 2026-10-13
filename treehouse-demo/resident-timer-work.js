"use strict";
// Ordered resident IRQ0 plus the pinned BIOS timer stubs. Hardware delivery and
// interrupt stack entry belong to the execution scheduler. Memory writes happen
// at their original instructions; I/O and interrupt flag changes are explicit.
class OriginalResidentTimerWork {
  constructor({memory,ds}){this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);}
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  word(at){return this.view.getUint16(at,true);}
  put(at,n){this.view.setUint16(at,n&65535,true);}
  far(at){return this.word(at)+16*this.word(at+2);}
  biosTick(){
    let ticks=(this.view.getUint32(0x46c,true)+1)>>>0;
    if(ticks>=0x1800b0){ticks=0;this.memory[0x470]++;}
    this.view.setUint32(0x46c,ticks,true);
    const timeout=this.memory[0x440];if(timeout)this.memory[0x440]--;
    if(timeout===1)this.memory[0x43f]&=0xf0;
  }
  *bios(){
    const address=this.far(this.base+0x202a),user=this.far(0x70),physical=function*(a){yield 'physical:'+a.toString(16);};
    yield* physical(address);yield {call:'interrupt-flags',enabled:true};
    yield* physical(address+1);yield {call:'bios-clock'};this.biosTick();
    for(const offset of [5,6,7,8])yield* physical(address+offset);
    yield {call:'interrupt-flags',enabled:false};
    yield* physical(user);yield {call:'bios-user-timer'};
    yield* physical(user+4);yield {call:'interrupt-flags',enabled:true};
    yield* physical(address+10);yield {call:'interrupt-flags',enabled:false};
    yield* physical(address+11);yield* physical(address+13);yield {call:'port-write',port:0x20,value:0x20};
    for(const offset of [15,16,17,18])yield* physical(address+offset);
    yield {call:'interrupt-flags',enabled:false};
  }
  *run(){
    const emit=OriginalResidentTimerWork.instructions;
    yield* emit(0x6447,0x6448,0x6449,0x644a,0x644d,0x644f,0x6452);const low=(this.word(this.base+0x201e)+1)&65535;this.put(this.base+0x201e,low);
    yield* emit(0x6456);if(!low){yield* emit(0x6458);this.put(this.base+0x2020,this.word(this.base+0x2020)+1);}
    for(let offset=8;offset;offset-=2){
      yield* emit(0x645c,0x6461);const at=this.base+0x2014+offset;
      if(this.word(at)){yield* emit(0x6463);this.put(at,this.word(at)-1);}yield* emit(0x6467,0x646a);
    }
    yield* emit(0x646c,0x646f);const phase=this.word(this.base+0x2034)+this.word(this.base+0x2030);this.put(this.base+0x2034,phase);
    yield* emit(0x6473,0x6477);const chain=!!((this.word(this.base+0x2032)+(phase>>>16))&65535);
    if(chain){yield* emit(0x647f,0x6480);yield* this.bios();}
    else{yield* emit(0x6479,0x647b);yield {call:'port-write',port:0x20,value:0x20};yield* emit(0x647d);}
    yield* emit(0x6484,0x6485,0x6486,0x6487);return {chainBios:chain};
  }
}
