"use strict";
// Resident ED3E. Mutates a supplied memory model and counts intrinsic work;
// address, block resize, allocation and copy callees retain separate costs.
class OriginalHandleResizeWork {
  static resize(memory,handle,bytes){
    const entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0xed3e,0xed3f,0xed41,0xed42,0xed43,0xed44,0xed47,0xed48,0xed49,0xed4c,0xed4e]);
    const pointer=memory.address(handle);let result,action,copy=null;
    if(!pointer){
      add([0xedc4,0xedc5,0xedc8,0xedc9,0xedca,0xedcb,0xedce]);
      result=memory.reallocate(handle,bytes);action='reallocate';
    }else{
      add([0xed50,0xed53,0xed56,0xed59,0xed5b,0xed5e]);
      result=!!memory.resize(memory.heap.at(pointer-6),bytes);action='in-place';
      if(!result){
        add([0xed60,0xed65]);const h=memory.handle(handle);action='locked';
        if(!(h.state&0x8000)){
          add([0xed67,0xed6c,0xed6d,0xed6e,0xed71,0xed73,0xed76,0xed78,0xed7a,0xed7b,0xed7c,0xed7d,0xed7e,0xed83]);
          h.state|=0x8000;let destination;
          try{destination=memory.heap.firstFit(bytes);}finally{h.state&=0x7fff;}
          const source=memory.heap.at(pointer-6);
          copy={from:pointer,to:destination.address+6,bytes:source.size-6-source.padding};
          memory.moveHandleTo(handle,destination);result=true;action='moved';
          add([0xed85,0xed87,0xed8b,0xed8e,0xed92,0xed95,0xed99,0xed9d,0xeda0,0xeda4,0xeda7,0xeda8,0xeda9,0xedac,0xedaf,0xedb0,0xedb1,0xedb2,0xedb3,0xedb4,0xedb7]);
        }
      }
      add([0xedb8,0xedb9,0xedbb]);
    }
    add([0xedbd,0xedbe,0xedbf,0xedc0,0xedc1]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,result,ax:result?0:1,action,copy};
  }
}
