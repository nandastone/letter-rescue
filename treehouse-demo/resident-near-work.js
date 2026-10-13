"use strict";
// Ordered 003D/0590/001C work, operating directly on the current near arena.
class OriginalResidentNearWork {
  constructor({memory,ds}){this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);}
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  static get singleStrings(){return new Set(['resident:05c3','resident:05d5']);}
  word(at){return this.view.getUint16(this.base+(at&65535),true);}
  put(at,n){this.view.setUint16(this.base+(at&65535),n&65535,true);}
  *allocate(payload){
    const emit=OriginalResidentNearWork.instructions;
    yield* emit(0x003d,0x003e,0x0040,0x0041,0x0042,0x0045,0x0048);
    if(!Number.isInteger(payload)||payload<0||payload>0xffe8)throw new Error('Near allocation failure callback requires composition');
    yield* emit(0x004a,0x004d,0x0590,0x0591,0x0594,0x0595,0x0596,0x0599,0x059c,0x059e);
    const needed=(payload+1)&0xfffe,previous=this.word(0x1778);let address=previous,limit=this.word(0x177a),second=false,header;
    for(let guard=0;guard<65536;guard++){
      yield* emit(0x05c3);header=this.word(address);yield* emit(0x05c4,0x05c6);
      if(header&1){
        yield* emit(0x05c8);const start=address;
        for(;;){
          yield* emit(0x05ca,0x05cb,0x05cd);const size=header-1;
          if(size>=needed){
            yield* emit(0x05f2,0x05f3);this.put(start,needed);yield* emit(0x05f6);
            if(size!==needed){yield* emit(0x05f8,0x05fa,0x05fc,0x05fd);this.put(start+2+needed,size-needed-1);yield* emit(0x05ff);}
            yield* emit(0x0601,0x0603);this.put(0x1778,start+2+needed);
            yield* emit(0x0606,0x0608,0x060a,0x060b,0x0050,0x0072,0x0073,0x0074,0x0075);return start+2;
          }
          yield* emit(0x05cf,0x05d1);address+=size+2;if(address>65535)throw new Error('Near heap overflow requires composition');
          yield* emit(0x05d3,0x05d5);header=this.word(address);yield* emit(0x05d6,0x05d8);if(!(header&1))break;
          yield* emit(0x05da,0x05dc,0x05df,0x05e1);header=(header+size+2)&65535;this.put(start,header);address=start;yield* emit(0x05e4);
        }
      }
      yield* emit(0x05b8,0x05bb,0x05bd);
      if(address>=limit){
        yield* emit(0x05a0,0x05a2,0x05a3,0x05a5);if(second)throw new Error('Near arena growth requires composition');
        yield* emit(0x05a7,0x05a8,0x05ab,0x05ae,0x05b0);address=this.word(0x1776);if(previous===address)throw new Error('Near arena exhausted');
        yield* emit(0x05b2,0x05b3,0x05b5);limit=previous-1;second=true;
      }else{yield* emit(0x05bf,0x05c1);address+=header+2;if(address>65535)throw new Error('Near heap overflow requires composition');}
    }throw new Error('Near heap search did not terminate');
  }
  *free(pointer){
    const emit=OriginalResidentNearWork.instructions;yield* emit(0x001c,0x001d,0x001f,0x0020,0x0023,0x0026,0x0029);
    if(this.word(0x1776)<pointer){
      yield* emit(0x002b,0x002c,0x002d);const at=(pointer-2)&65535;this.put(at,this.word(at)|1);yield* emit(0x0030,0x0033);
      if(this.word(0x1778)>at){yield* emit(0x0035);this.put(0x1778,at);}
    }yield* emit(0x0038,0x0039,0x003b,0x003c);
  }
}
