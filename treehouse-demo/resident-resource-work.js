"use strict";
// Resident handle and cached-resource execution on the shared guest data store.
// Missing disk/EMS/eviction paths remain explicit callees, never zero-cost hits.
class OriginalResidentResourceWork {
  constructor({memory,ds}){this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);}
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  word(at){return this.view.getUint16(at,true);}
  put(at,n){this.view.setUint16(at,n&65535,true);}
  far(at){return this.word(at)+16*this.word(at+2);}
  *savedFlags(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x64fe,0x64ff,0x6501,0x6504);let flags=this.word(this.base+handle);
    yield* emit(0x6507,0x6509);if(!handle){yield* emit(0x650b);flags=0;}yield* emit(0x650c,0x650d);return flags;
  }
  *setFlags(handle,flags){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x65b2,0x65b3,0x65b5,0x65b8,0x65bb,0x65bd);
    if(handle){yield* emit(0x65bf,0x65c2);this.put(this.base+handle,this.word(this.base+handle)&0x1fff);yield* emit(0x65c7);this.put(this.base+handle,this.word(this.base+handle)|(flags&0xe000));}
    yield* emit(0x65ca,0x65cb,0x65cc);return handle;
  }
  *address(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x75c6,0x75c7,0x75c9,0x75ca,0x75cb,0x75ce,0x75d0);let address=0;
    if(handle){
      yield* emit(0x75d2,0x75d5,0x75d7,0x75da);const flags=this.word(this.base+handle),segment=this.word(this.base+handle+2);
      if(flags&0x200)throw new Error('Resident resource EMS materialization requires composition');
      yield* emit(0x75dc,0x75df,0x75e1);address=16*segment+(flags&15);
      if(address){yield* emit(0x75e3);this.put(this.base+handle,flags|0x1f0);yield* emit(0x75e8,0x75eb);address+=6;}
    }else yield* emit(0x75f3,0x75f5,0x75f6);
    yield* emit(0x75ed,0x75ee,0x75ef,0x75f0);return address;
  }
  *unagedAddress(handle){return yield* OriginalGraphicsWork.handleAddress({handle,state:this.word(this.base+handle),segment:this.word(this.base+handle+2)});}
  *lock(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x6510,0x6511,0x6513,0x6516,0x6517,0x6518);const address=yield* this.address(handle);
    yield* emit(0x651b,0x651d,0x651f);if(address){yield* emit(0x6521);this.put(this.base+handle,this.word(this.base+handle)|0x81f0);}yield* emit(0x6526,0x6527);return address;
  }
  *length(handle){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0xec14,0xec15,0xec17,0xec18,0xec19,0xec1c,0xec1e);let bytes=0,resident=false;
    if(handle){
      yield* emit(0xec20,0xec23,0xec27);const flags=this.word(this.base+handle),segment=this.word(this.base+handle+2);
      if(!(flags&0x200)){
        yield* emit(0xec29,0xec2c,0xec2e,0xec30);const address=16*segment+(flags&15);resident=!!address;
        if(resident){
          yield* emit(0xec32,0x6fa9,0x6fab,0x6fad,0x6fb0,0x6fb2,0x6fb4,0x6fb6,0x6fb8,0x6fba,0x6fbc,0x6fbe,0x6fc1,0x6fc4,0x6fc6,0x6fc9,0x6fcb,0x6fcd,0x6fcf,0x6fd2,0x6fd4,0x6fd7);
          const header=this.word(address);bytes=16*this.word(address+2)+2*(header&7)-6-((header>>>3)&7);
        }
      }
    }
    if(!resident)yield* emit(0xec3b,0xec3d,0xec3e);yield* emit(0xec35,0xec36,0xec37,0xec38);return bytes;
  }
  *lookup(tag,id){
    const emit=OriginalResidentResourceWork.instructions,s16=n=>(n<<16)>>16;
    yield* emit(0x7bc9,0x7bca,0x7bcc,0x7bcf,0x7bd0,0x7bd1,0x7bd4,0x7bd7,0x7bda);let pointer=this.base+0x204e;
    const low=tag&65535,high=tag>>>16;
    for(let guard=0;guard<256;guard++){
      yield* emit(0x7bdd,0x7bdf);const handle=this.word(pointer);
      if(!handle)throw new Error('Static resource fallback requires composition');
      yield* emit(0x7be1,0x7be2,0x7be3);const catalog=yield* this.unagedAddress(handle);pointer=catalog;
      yield* emit(0x7be6,0x7be7,0x7be9,0x7bec);const types=this.word(catalog+0x50);if(!types)continue;
      yield* emit(0x7bee,0x7bef,0x7bf2,0x7bf4,0x7bf7);let a=0,b=types+1,group=0;
      for(;;){
        yield* emit(0x7bf9,0x7bfb,0x7bfe,0x7c00,0x7c02);const mid=(a+b)>>>1;if(mid===a)break;
        yield* emit(0x7c04,0x7c06,0x7c08,0x7c0a,0x7c0c,0x7c0f);const at=catalog+6*mid;
        if(s16(high)>s16(this.word(at+0x4e))){yield* emit(0x7c72,0x7c73);a=mid;continue;}
        yield* emit(0x7c11);if(s16(high)<s16(this.word(at+0x4e))){yield* emit(0x7c6d,0x7c70);b=mid;continue;}
        yield* emit(0x7c13,0x7c16);if(s16(low)<s16(this.word(at+0x4c))){yield* emit(0x7c6d,0x7c70);b=mid;continue;}
        yield* emit(0x7c18);if(s16(low)>s16(this.word(at+0x4c))){yield* emit(0x7c72,0x7c73);a=mid;continue;}
        yield* emit(0x7c1a,0x7c1d,0x7c20,0x7c22);group=catalog+0x50+this.word(at+0x50);break;
      }
      if(!group)continue;const count=this.word(group);if(!count)continue;
      yield* emit(0x7c24,0x7c25,0x7c28,0x7c2a);a=0;b=count+1;
      for(;;){
        yield* emit(0x7c2d,0x7c2f,0x7c32,0x7c34,0x7c36);const mid=(a+b)>>>1;if(mid===a)break;
        yield* emit(0x7c38,0x7c3a,0x7c3c,0x7c3e,0x7c40,0x7c42,0x7c44,0x7c47);const entry=group+11*mid-9,found=this.word(entry);
        if(s16(id)<s16(found)){yield* emit(0x7c65,0x7c68);b=mid;continue;}
        yield* emit(0x7c49);if(s16(id)>s16(found)){yield* emit(0x7c6a,0x7c6b);a=mid;continue;}
        yield* emit(0x7c4b,0x7c4e,0x7c4f,0x7c51,0x7c52);return {catalog,entry,handle};
      }
    }
    throw new Error('Resource catalog traversal did not terminate');
  }
  *entryMemory({catalog,entry}){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x7a30,0x7a31);const catalogHandle=this.word(catalog-2),saved=this.word(this.base+catalogHandle);
    yield* emit(0x7a34,0x7a37,0x7a38);this.put(this.base+catalogHandle,saved|0x8000);yield* emit(0x7a3d,0x7a40,0x7a42);
    let handle=this.word(entry+9),bytes=0,address=0;
    if(handle){
      yield* emit(0x7a44,0x7a45,0x7a46,0x7a47);address=yield* this.address(handle);yield* emit(0x7a4a,0x7a4c);
      if(address){yield* emit(0x7a4e,0x7a4f,0x7a50);bytes=yield* this.length(handle);yield* emit(0x7a53,0x7a54,0x7a55,0x7a56);}
    }
    if(!address){yield* emit(0x7a58,0x7a5b,0x7a5d);handle=0;bytes=this.view.getUint32(entry+6,true)&0xfffff;}
    yield* emit(0x7a60,0x7a61);this.put(this.base+catalogHandle,saved);yield* emit(0x7a64,0x7a65);return {handle,bytes,address};
  }
  *cachedResource(entry){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x7a66,0x7a67);const catalogHandle=this.word(entry.catalog-2),saved=this.word(this.base+catalogHandle);
    yield* emit(0x7a6a,0x7a6d,0x7a6e);this.put(this.base+catalogHandle,saved|0x8000);yield* emit(0x7a73,0x7a75);const result=yield* this.entryMemory(entry);
    yield* emit(0x7a78,0x7a7a);if(!result.handle)throw new Error('Cold resource loading requires composition');
    yield* emit(0x7adf,0x7ae0);this.put(this.base+catalogHandle,saved);yield* emit(0x7ae3,0x7ae4,0x7ae5);return result.handle;
  }
  *resourceHandle(tag,id){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0x7668,0x7669,0x766b,0x766c,0x766d,0x766e,0x7671,0x7673,0x7676);const entry=yield* this.lookup(tag,id);
    yield* emit(0x7679,0x767b,0x767d);const handle=yield* this.cachedResource(entry);yield* emit(0x7680,0x7681,0x7682,0x7683,0x7684);return handle;
  }
  *loadShape(paletteHandle,shape){
    const emit=OriginalResidentResourceWork.instructions;yield* emit(0xe33c,0xe33d,0xe33f,0xe342,0xe343,0xe344,0xe347,0xe34c);const heap=this.far(this.base+0x203a),callback=[this.word(heap+0x12),this.word(heap+0x14)];
    yield* emit(0xe350,0xe354,0xe358,0xe35b,0xe35e,0xe360);this.put(heap+0x14,0);yield* emit(0xe364);this.put(heap+0x12,0);
    yield* emit(0xe368,0xe369,0xe36a,0xe36b);const paletteFlags=yield* this.savedFlags(paletteHandle);
    yield* emit(0xe36e,0xe371,0xe372,0xe373,0xe374);const palette=yield* this.lock(paletteHandle);
    yield* emit(0xe377,0xe37a,0xe37d,0xe37f);if(!palette)throw new Error('Missing palette handle during shape loading');
    yield* emit(0xe384,0xe387,0xe38a,0xe38b,0xe38c,0xe38f,0xe392,0xe395,0xe396,0xe397,0xe398,0xe399);
    const sourceHandle=yield* this.resourceHandle(0x53484150,(this.word(palette)+shape-1)&65535);
    yield* emit(0xe39c,0xe39e,0xe3a0);if(!sourceHandle)throw new Error('Missing source shape');
    yield* emit(0xe3a2,0xe3a3,0xe3a4,0xe3a5);const sourceFlags=yield* this.savedFlags(sourceHandle);
    yield* emit(0xe3a8,0xe3ab,0xe3ac,0xe3ad,0xe3ae);const source=yield* this.lock(sourceHandle);
    yield* emit(0xe3b1,0xe3b2,0xe3b3,0xe3b6,0xe3b9,0xe3bc,0xe3bd,0xe3be,0xe3bf,0xe3c0);
    const converted=yield {call:'convert-shape',palette:palette+4,source,paletteHandle,sourceHandle};
    yield* emit(0xe3c3,0xe3c6,0xe3c8);if(!converted)throw new Error('Shape conversion retry requires composition');
    yield* emit(0xe3fe,0xe3ff,0xe402,0xe403,0xe404);yield* this.setFlags(sourceHandle,sourceFlags);
    yield* emit(0xe407,0xe408,0xe40b,0xe40c,0xe40d);yield* this.setFlags(paletteHandle,paletteFlags);
    yield* emit(0xe410,0xe413,0xe416,0xe41a);this.put(heap+0x12,callback[0]);yield* emit(0xe41e);this.put(heap+0x14,callback[1]);
    yield* emit(0xe422,0xe425,0xe426,0xe427,0xe429,0xe42a);return converted;
  }
  *caption({paletteHandle,shape,x,y,mode},graphics){
    const main=OriginalAnimationWork.instructions;yield* main(0x64a4,0x64a5,0x64a7,0x64ab,0x64ac,0x64ad,0x64b0,0x64b3);
    const handle=yield* this.loadShape(paletteHandle,shape);yield* main(0x64b8,0x64bb,0x64bc);yield* this.unagedAddress(handle);
    yield* main(0x64c1,0x64c4,0x64c7,0x64ca,0x64cd,0x64d0,0x64d3,0x64d6);yield 'resident:8272';yield* graphics.sprite({handle,mode,x,y});
    yield* main(0x64db,0x64de);yield {call:'free-shape',handle};yield* main(0x64e3,0x64e4,0x64e5,0x64e7,0x64e8);
  }
}
