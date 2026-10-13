"use strict";
// Intrinsic instruction work for resident memory query helpers. No host time.
class OriginalMemoryWork {
  static input({handle=0,state=0,segment=0}){
    if([handle,state,segment].some(v=>!Number.isInteger(v)||v<0||v>65535))throw new Error("Invalid original memory query");
    return {handle,state,segment,resident:!!(handle&&((state&15)||segment))};
  }
  static address(input){
    const h=this.input(input),entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    if(h.handle&&(h.state&0x200))throw new Error("EMS address materialization work is not reconstructed");
    add([0x75c6,0x75c7,0x75c9,0x75ca,0x75cb,0x75ce,0x75d0]);let address=0;
    if(h.handle){
      add([0x75d2,0x75d5,0x75d7,0x75da,0x75dc,0x75df,0x75e1]);
      if(h.resident){add([0x75e3,0x75e8,0x75eb]);h.state|=0x1f0;address=16*h.segment+(h.state&15)+6;}
    }else add([0x75f3,0x75f5,0x75f6]);
    add([0x75ed,0x75ee,0x75ef,0x75f0]);const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,state:h.state,address};
  }
  static length(input){
    const h=this.input(input),entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0xec14,0xec15,0xec17,0xec18,0xec19,0xec1c,0xec1e]);let bytes=0;
    if(h.handle){
      add([0xec20,0xec23,0xec27]);
      if(!(h.state&0x200)){
        add([0xec29,0xec2c,0xec2e,0xec30]);
        if(h.resident){
          const {blockSize,padding}=input;
          if(!Number.isInteger(blockSize)||blockSize<6||blockSize>0xffffe||blockSize%2||!Number.isInteger(padding)||padding<0||padding>7||blockSize<6+padding)throw new Error("Invalid original block header");
          add([0xec32,0x6fa9,0x6fab,0x6fad,0x6fb0,0x6fb2,0x6fb4,0x6fb6,0x6fb8,0x6fba,0x6fbc,0x6fbe,0x6fc1,0x6fc4,0x6fc6,0x6fc9,0x6fcb,0x6fcd,0x6fcf,0x6fd2,0x6fd4,0x6fd7]);
          bytes=blockSize-6-padding;
        }else add([0xec3b,0xec3d,0xec3e]);
      }else add([0xec3b,0xec3d,0xec3e]);
    }else add([0xec3b,0xec3d,0xec3e]);
    add([0xec35,0xec36,0xec37,0xec38]);const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,bytes,ax:bytes&65535,dx:bytes>>>16};
  }
}
