"use strict";
// Conventional heap allocation on shared RAM. Arena growth, EMS and relocating
// resize remain explicit unsupported branches; none is charged as a free call.
class OriginalResidentHeapWork extends OriginalResidentResourceWork {
  constructor(input){super(input);this.near=new OriginalResidentNearWork(input);}
  static *range(first,last=first){
    if(!OriginalHeapInstructionAddresses.includes(first)||!OriginalHeapInstructionAddresses.includes(last))throw new Error('Unknown heap code boundary');
    for(const a of OriginalHeapInstructionAddresses)if(a>=first&&a<=last)yield 'resident:'+a.toString(16);
  }
  size(at){return 16*this.word(at+2)+2*(this.word(at)&7);}
  putFar(at,address){this.put(at,address&15);this.put(at+2,address>>>4);}
  *coalesce(block){
    const range=OriginalResidentHeapWork.range;
    for(let guard=0;guard<65536;guard++){
      yield* range(0x6fd8,0x6fe9);const next=block+this.size(block),flags=this.word(next)&0xc000;
      if(flags&0x8000)break;yield* range(0x6feb);if(flags===0x4000)break;
      const size=this.size(block)+this.size(next);yield* range(0x6fed,0x7004);this.put(block,this.word(block)&0xfff8);
      yield* range(0x7007);this.put(block,this.word(block)|((size&15)>>>1));yield* range(0x7009);this.put(block+2,size>>>4);yield* range(0x700c,0x700e);
    }yield* range(0x7010);
  }
  *firstFit(payload){
    const range=OriginalResidentHeapWork.range,needed=(payload+7)&~1,heap=this.far(this.base+0x203a);
    if(payload<0||payload>0xffff8)throw new Error('Far allocation size outside conventional arena');
    yield* range(0x6d47,0x6d61);yield* range(0x6d66,0x6d89);let block=this.far(heap+4);
    for(let pass=0;pass<2;pass++){
      yield* range(0x6d8c);
      for(let guard=0;guard<65536;guard++){
        yield* range(0x6d8e,0x6d97);let size=this.size(block),flags=this.word(block)&0xc000;
        if(flags&0x8000){yield* range(0x6d99,0x6db1);block+=size;continue;}
        yield* range(0x6db3);if(flags===0x4000){yield* range(0x6ddf,0x6de2);break;}
        yield* range(0x6db5);yield* this.coalesce(block);size=this.size(block);yield* range(0x6db8,0x6dbf);
        if((size>>>4)<=(needed>>>4)){yield* range(0x6dc1);if((size>>>4)===(needed>>>4))yield* range(0x6dc3,0x6dc5);}
        if(size<needed){yield* range(0x6d9c,0x6db1);block+=size;continue;}
        yield* range(0x6dc7,0x6dc9);if((size&15)<(needed&15))yield* range(0x6dcb,0x6dce);
        yield* range(0x6dcf,0x6dd1);const remainder=size-needed;if(remainder<16)yield* range(0x6dd3,0x6dd6);
        if(remainder<6)yield* range(0x6dd8,0x6ddd);
        else{
          yield* range(0x6ded,0x6df3);this.put(block+needed,(remainder&15)>>>1);
          yield* range(0x6df6);this.put(block+needed+2,remainder>>>4);yield* range(0x6dfa,0x6dfb);this.put(block+2,needed>>>4);size=needed;
        }
        yield* range(0x6dfe,0x6e18);this.put(block,((size&15)>>>1)|((size-payload-6)<<3));
        yield* range(0x6e1a,0x6e1f);this.put(heap+4,block&15);yield* range(0x6e23);this.put(heap+6,block>>>4);
        yield* range(0x6e27,0x6e31);return block;
      }
      if(pass===0){yield* range(0x6de4,0x6deb);block=this.far(heap);}
    }throw new Error('Far heap growth/reclamation requires composition');
  }
  *allocate(payload){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x652a,0x652b,0x652d,0x652e,0x652f,0x6566,0x6567,0x6568,0x6569,0x656c);
    this.put(this.base+0x1778,this.word(this.base+0x1776));yield* emit(0x656f,0x6572,0x6573,0x6574,0x6575);const handle=yield* this.near.allocate(4);
    yield* emit(0x6578,0x657b,0x657d,0x657f,0x6581,0x6583);this.put(this.base+handle,0);yield* emit(0x6585);this.put(this.base+handle+2,0);
    yield* emit(0x6588,0x6589,0x6532,0x6535,0x6536,0x6538,0x653a,0x6e8d,0x6e92);const heap=this.far(this.base+0x203a);this.put(heap+0xe,this.word(heap+0xe)+1);
    yield* emit(0x6e96);const block=yield* this.firstFit(payload);yield* emit(0x6e99,0x6e9e);this.put(heap+0xe,this.word(heap+0xe)-1);
    yield* emit(0x6ea2,0x653d,0x653f);this.put(block,this.word(block)|0xc000);yield* emit(0x6543);this.put(block+4,handle);
    yield* emit(0x6546,0x654a);this.put(this.base+handle,(block&15)|0x1f0);yield* emit(0x654d);this.put(this.base+handle+2,block>>>4);
    yield* emit(0x6550,0x6551,0x6552,0x6553,0x6554);return handle;
  }
  *unlock(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x65d0,0x65d1,0x65d3,0x65d6,0x65d8);
    if(handle){yield* emit(0x65da);this.put(this.base+handle,this.word(this.base+handle)&0x7fff);}yield* emit(0x65df,0x65e0,0x65e1);return handle;
  }
  *resize(handle,bytes){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0xed3e,0xed3f,0xed41,0xed42,0xed43,0xed44,0xed47,0xed48,0xed49);const address=yield* this.address(handle);
    yield* emit(0xed4c,0xed4e);if(!address)throw new Error('Absent handle resize requires composition');
    yield* emit(0xed50,0xed53,0xed56,0xed59,0xed5b,0x70e8,0x70e9,0x70eb,0x70ee,0x70ef,0x70f2,0x70f5,0x70f8,0x70fb,0x70fd,0x70ff,0x7102);
    if(bytes<0||bytes>0xffff8)throw new Error('Invalid conventional resize');
    yield* emit(0x7107,0x7109,0x710c,0x710e,0x7110,0x7112,0x7114,0x7115,0x7118,0x711b,0x711d,0x7120,0x7122,0x7124,0x7126);
    const block=address-6,size=this.size(block),needed=(bytes+7)&~1;
    if((size>>>4)<=(needed>>>4)){
      yield* emit(0x7128);if((size>>>4)===(needed>>>4))yield* emit(0x712a,0x712c,0x712e);
    }
    if(size!==needed)throw new Error('Size-changing far resize requires composition');
    yield* emit(0x717f,0x7180,0x7185);const heap=this.far(this.base+0x203a);this.put(heap+4,block&15);yield* emit(0x7189);this.put(heap+6,block>>>4);
    yield* emit(0x718d,0x7190,0x7192,0x7193,0x7195,0x7196,0xed5e,0xedb8,0xedb9,0xedbb,0xedbd,0xedbe,0xedbf,0xedc0,0xedc1);return true;
  }
  *releaseBlock(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x756e,0x756f,0x7571,0x7572,0x7574,0x7577,0x7579);
    if(handle){
      yield* emit(0x757b,0x757e,0x7582);const flags=this.word(this.base+handle),segment=this.word(this.base+handle+2);
      if(!(flags&0x8000)){
        yield* emit(0x7584);this.put(this.base+handle,flags&0xdc00);yield* emit(0x7589);this.put(this.base+handle+2,0);yield* emit(0x758c,0x7590);
        if(flags&0x200)throw new Error('EMS release requires composition');
        yield* emit(0x7592,0x7594,0x7597,0x7599);const block=16*segment+(flags&15);
        if(block){yield* emit(0x759b);this.put(block,this.word(block)&0x3fff);}yield* emit(0x75a0);
      }
    }yield* emit(0x75a1,0x75a2,0x75a4,0x75a6,0x75a7,0x75a8);
  }
  *free(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x64ce,0x64cf,0x64d1,0x64d2,0x64d5,0x64d7);
    if(handle){
      yield* emit(0x64d9,0x64da,0x64db,0x64dc,0x64dd);this.put(this.base+handle,this.word(this.base+handle)&0x7fff);yield* emit(0x64e1,0x64e5);
      if(this.word(this.base+handle)&0x1000)throw new Error('Extended handle free requires composition');
      yield* emit(0x64ec,0x64ed);yield* this.releaseBlock(handle);yield* emit(0x64f0,0x64f1,0x64f2);yield* this.near.free(handle);yield* emit(0x64f5);
    }yield* emit(0x64f8,0x64f9,0x64fa);
  }
}
