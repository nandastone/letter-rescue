"use strict";
// Conventional-memory compaction used by raw graphics surface allocation.
// Selection, handle movement and copies are derived from the current arena.
class OriginalResidentCompactionWork extends OriginalResidentHeapWork {
  static get singleStrings(){return new Set(['resident:6c94']);}
  *moveBytes(source,destination,bytes){
    const r=OriginalResidentHeapWork.range;
    yield* r(0x6c18,0x6c4a);
    const ss=source>>>4,ds=destination>>>4;
    let backwards=ds>ss;
    if(!backwards){yield* r(0x6c4c);if(ds===ss){yield* r(0x6c4e,0x6c50);backwards=(destination&15)>(source&15);}}
    if(backwards){
      yield* r(0x6ca4,0x6cbd);
      if(ds<=((source+bytes)>>>4))throw new Error('Overlapping backward heap copy requires composition');
    }
    yield* r(0x6c52);
    for(let remaining=bytes;;){
      yield* r(0x6c54,0x6c5f);const chunk=Math.min(remaining,0xfff0);
      if(remaining<0xfff0){yield* r(0x6c61,0x6c64);if(!chunk)break;yield* r(0x6c66,0x6c69);}
      yield* r(0x6c6c,0x6c8e);let words=chunk>>>1;
      do{
        yield 'resident:6c90';const done=yield {call:'rep-move-words',address:0x6c90,remaining:words};
        if(!Number.isInteger(done)||done<0||done>words||(words&&!done))throw new Error('Invalid heap copy REP progress');
        for(let i=0;i<done;i++){this.put(destination,this.word(source));source+=2;destination+=2;}words-=done;
      }while(words);
      yield* r(0x6c92);
      if(chunk&1){yield* r(0x6c94);this.memory[destination++]=this.memory[source++];yield* r(0x6c95);}
      remaining-=chunk;
    }
    yield* r(0x6c97,0x6ca1);return destination-bytes;
  }
  *lastFit(payload){
    const r=OriginalResidentHeapWork.range,needed=(payload+7)&~1,heap=this.far(this.base+0x203a);
    if(payload<0||payload>0xffff8)throw new Error('Invalid relocating allocation size');
    yield* r(0x6ea3,0x6ec1);yield* r(0x6ec7,0x6ee2);
    let block=this.far(heap+4),candidate=0;
    for(let guard=0;guard<65536;guard++){
      yield* r(0x6ee4,0x6eed);const flags=this.word(block)&0xc000;
      if(flags&0x8000)yield* r(0x6eef);
      else{
        yield* r(0x6f09);if(flags===0x4000)break;
        yield* r(0x6f0b);yield* this.coalesce(block);yield* r(0x6f0e,0x6f15);
        const size=this.size(block);
        if((size>>>4)<=(needed>>>4)){
          yield* r(0x6f17);
          if((size>>>4)===(needed>>>4))yield* r(0x6f19,0x6f1b);
        }
        if(size>=needed){yield* r(0x6f1d,0x6f23);candidate=block;}
      }
      yield* r(0x6ef2,0x6f07);block+=this.size(block);
      if(block+6>this.memory.length)throw new Error('Compaction search outside arena');
    }
    yield* r(0x6f25,0x6f28);
    if(candidate){
      block=candidate;const size=this.size(block),remainder=size-needed;
      yield* r(0x6f2a,0x6f3d);if((size&15)<(needed&15))yield* r(0x6f3f,0x6f42);
      yield* r(0x6f43,0x6f45);if(remainder<16)yield* r(0x6f47,0x6f4a);
      let allocated=size;
      if(remainder<6)yield* r(0x6f4c,0x6f51);
      else{
        yield* r(0x6f53,0x6f55);this.put(block,(remainder&15)>>>1);
        yield* r(0x6f57);this.put(block+2,remainder>>>4);
        yield* r(0x6f5a,0x6f72);block+=remainder;allocated=needed;this.put(block+2,needed>>>4);
      }
      yield* r(0x6f75,0x6f8f);this.put(block,((allocated&15)>>>1)|(((allocated-payload-6)<<3)&0x38));
      yield* r(0x6f91,0x6f96);this.put(heap+4,block&15);yield* r(0x6f9a);this.put(heap+6,block>>>4);yield* r(0x6f9e);
    }
    yield* r(0x6f9f,0x6fa8);return candidate?block:0;
  }
  *relocate(block){
    const r=OriginalResidentHeapWork.range,handle=this.word(block+4);
    yield* r(0x7011,0x701b);const flags=this.word(this.base+handle);let moved=false;
    if(!(flags&0x8000)){
      yield* r(0x701d,0x701e);this.put(this.base+handle,flags|0x8000);
      yield* r(0x7023,0x7025);const header=this.word(block),bytes=this.size(block)-6-((header>>>3)&7);
      yield* r(0x6fa9,0x6fd7);yield* r(0x7028,0x702d);const heap=this.far(this.base+0x203a);this.put(heap+4,block&15);
      yield* r(0x7031);this.put(heap+6,block>>>4);yield* r(0x7035);const destination=yield* this.lastFit(bytes);
      yield* r(0x7038);if(!destination)throw new Error('Compaction relocation allocation failure requires composition');
      yield* r(0x703d,0x7043);this.put(this.base+handle,flags);yield* r(0x7046,0x7048);const old=this.word(block);
      yield* r(0x704a);this.put(block,old&0x3fff);yield* r(0x704e,0x7051);this.put(destination,this.word(destination)&0x3f);
      yield* r(0x7055);this.put(destination,this.word(destination)|(old&0xffc0));yield* r(0x7058);this.put(destination+4,handle);
      yield* r(0x705c);this.put(this.base+handle,this.word(this.base+handle)&0xfff0);yield* r(0x7060);this.put(this.base+handle,this.word(this.base+handle)|(destination&15));
      yield* r(0x7063);this.put(this.base+handle+2,destination>>>4);yield* r(0x7066,0x7073);yield* this.moveBytes(block+6,destination+6,bytes);yield* r(0x7076);moved=true;
    }
    yield* r(0x7077,0x7078);return moved;
  }
  *compact(payload){
    const r=OriginalResidentHeapWork.range,heap=this.far(this.base+0x203a),needed=(payload+7)&~1;
    if(payload<0||payload>0xffff8)throw new Error('Invalid compaction request');
    yield* r(0x6b06,0x6b21);yield* r(0x6b29,0x6b4d);let block=this.far(heap),largest=6;
    for(let guard=0;guard<65536;guard++){
      yield* r(0x6b4f,0x6b58);let flags=this.word(block)&0xc000,available=false;
      if(flags&0x8000){
        yield* r(0x6b5a);
        if(flags===0xc000){yield* r(0x6bb5,0x6bba);available=yield* this.relocate(block);yield* r(0x6bbd,0x6bbf);}
      }else{
        yield* r(0x6b73);if(flags===0x4000)throw new Error('Compaction arena growth requires composition');available=true;
      }
      if(available){
        for(;;){
          yield* r(0x6bc1);yield* this.coalesce(block);const size=this.size(block);
          yield* r(0x6bc4,0x6bc9);
          if((size>>>4)<=(largest>>>4)){yield* r(0x6bcb);if((size>>>4)===(largest>>>4))yield* r(0x6bcd,0x6bd0);}
          if(size>largest){
            yield* r(0x6bd2,0x6bdb);largest=size;
            if((size>>>4)<=(needed>>>4)){yield* r(0x6bdd);if((size>>>4)===(needed>>>4))yield* r(0x6bdf,0x6be2);}
            if(size>=needed){
              yield* r(0x6b82,0x6b87);this.put(heap+4,block&15);yield* r(0x6b8b);this.put(heap+6,block>>>4);
              yield* r(0x6b8f,0x6bb2);return largest-6;
            }
          }
          const next=block+size,nextFlags=this.word(next)&0xc000;
          yield* r(0x6be4,0x6be6);if(!(nextFlags&0x8000))throw new Error('Compaction expansion requires composition');yield* r(0x6be8);
          if(nextFlags===0x8000){yield* r(0x6c15);break;}
          yield* r(0x6bea);this.put(block,this.word(block)|0x8000);yield* r(0x6bee,0x6c05);
          const moved=yield* this.relocate(next);yield* r(0x6c08,0x6c0f);this.put(block,this.word(block)&0x3fff);yield* r(0x6c13);
          if(!moved){yield* r(0x6c15);break;}
        }
      }
      yield* r(0x6b5c,0x6b71);block+=this.size(block);
    }
    throw new Error('Compaction scan did not terminate');
  }
}
