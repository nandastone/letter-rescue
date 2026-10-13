"use strict";
// Resident E03E column LZ and DE10 indexed expansion. Byte writes occur as the
// independently generated instructions run; traces never supply output bytes.
class OriginalShapeCodecWork {
  constructor({memory,ds}){this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);this.near=new OriginalResidentNearWork({memory,ds});}
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  static get singleStrings(){return new Set([...OriginalResidentNearWork.singleStrings,...[0xe095,0xe09f,0xe0d3,0xe0d6,0xe0ed,0xde1c,0xde1f,0xde25,0xde48,0xde59,0xde69,0xde6a].map(a=>'resident:'+a.toString(16))]);}
  word(at){return this.view.getUint16(at,true);}
  *columnLz({rows,stride,length,source,destination}){
    const emit=OriginalShapeCodecWork.instructions,m=this.memory;
    if(!rows||!length)throw new Error('Column LZ requires nonzero dimensions');
    yield* emit(0xe03e,0xe03f,0xe041,0xe044,0xe045,0xe046,0xe047,0xe04a,0xe04d,0xe04e,0xe04f,0xe050);
    const scratch=yield* this.near.allocate(1024);yield* emit(0xe053,0xe056,0xe058,0xe067,0xe06a,0xe06d,0xe06e,0xe070,0xe071);
    let clear=512,at=this.base+scratch;
    while(clear){yield* emit(0xe072);const n=yield {call:'rep-store-words',remaining:clear};if(!Number.isInteger(n)||n<1||n>clear)throw new Error('Invalid codec clear slice');m.fill(0,at,at+2*n);at+=2*n;clear-=n;}
    yield* emit(0xe074,0xe077,0xe07a,0xe07c,0xe07f,0xe082,0xe085,0xe088,0xe089);
    let ring=this.base+scratch+1024-66,ringEnd=this.base+scratch+1024,input=source,out=destination,column=rows,remaining=length,flags=0;
    for(;;){
      yield* emit(0xe08c,0xe08f,0xe091,0xe093);flags>>>=1;
      if(!(flags&0xff00)){yield* emit(0xe095);flags=m[input++];yield* emit(0xe096);flags|=0xff00;}
      yield* emit(0xe098,0xe09b,0xe09d);
      if(flags&1){
        yield* emit(0xe09f);const value=m[input++];yield* emit(0xe0a0);m[out]=value;yield* emit(0xe0a3);out+=stride;yield* emit(0xe0a6,0xe0a7);column--;
        if(!column){yield* emit(0xe0a9);out-=length-1;yield* emit(0xe0ac);column=rows;}
        yield* emit(0xe0af);m[ring]=value;yield* emit(0xe0b2,0xe0b3,0xe0b5);ring++;
        if(ring>=ringEnd){yield* emit(0xe0b7);ring=this.base+scratch;}
        yield* emit(0xe0ba,0xe0bd);if(!--remaining)break;
      }else{
        yield* emit(0xe0d3);const hi=m[input++];yield* emit(0xe0d4,0xe0d6);const lo=m[input++];
        yield* emit(0xe0d7,0xe0d8,0xe0d9,0xe0db,0xe0dd,0xe0df,0xe0e3,0xe0e6,0xe0e8,0xe0ea);
        let read=this.base+scratch+(((hi<<8)|lo)&1023),count=(hi>>>2)+3,done=false;
        for(;;){
          yield* emit(0xe0ed);const value=m[read++];yield* emit(0xe0ee,0xe0f0);
          if(read>=ringEnd){yield* emit(0xe0f2);read=this.base+scratch;}
          yield* emit(0xe0f5);m[out]=value;yield* emit(0xe0f8);out+=stride;yield* emit(0xe0fb,0xe0fc);column--;
          if(!column){yield* emit(0xe0fe);out-=length-1;yield* emit(0xe101);column=rows;}
          yield* emit(0xe104);m[ring]=value;yield* emit(0xe106,0xe107,0xe109);ring++;
          if(ring>=ringEnd){yield* emit(0xe10b);ring=this.base+scratch;}
          yield* emit(0xe10e,0xe111);if(!--remaining){yield* emit(0xe11c,0xe11d,0xe11e);done=true;break;}
          yield* emit(0xe113,0xe115);if(!--count){yield* emit(0xe117,0xe118,0xe119);break;}
        }if(done)break;
      }
    }
    yield* emit(0xe0bf,0xe0c0,0xe0c1,0xe0c4,0xe0c5,0xe0c6);yield* this.near.free(scratch);
    yield* emit(0xe0c9,0xe0cc,0xe0cf,0xe0d1,0xe05a,0xe05b,0xe05e,0xe05f,0xe060,0xe061,0xe063,0xe064);return input-source;
  }
  *expandNibbles({header,pixels,paletteShift}){
    const emit=OriginalShapeCodecWork.instructions,m=this.memory;
    yield* emit(0xde10,0xde11,0xde13,0xde16,0xde17,0xde18,0xde19,0xde1c);let rows=this.word(header);
    yield* emit(0xde1d,0xde1f);const width=this.word(header+2);yield* emit(0xde20,0xde22,0xde25);const stride=this.word(header+4);
    yield* emit(0xde26,0xde29,0xde2c,0xde2e);
    if(rows){
      yield* emit(0xde30,0xde32,0xde34,0xde35,0xde37,0xde39,0xde3b,0xde3c,0xde3f,0xde41,0xde43,0xde45,0xde47);
      let source=pixels+stride*rows-1,destination=pixels+width*rows-1,byte;const offset=(paletteShift<<4)&255;
      yield* emit(0xde48);byte=m[source--];
      do{
        yield* emit(0xde49,0xde4c,0xde4f);let left=width,first=true;
        do{
          if(!first||!(width&1)){
            yield* emit(0xde51,0xde53,0xde55);let value=byte&15;if(value){yield* emit(0xde57);value=(value+offset)&255;}
            yield* emit(0xde59);m[destination--]=value;yield* emit(0xde5a,0xde5b);left--;
          }
          first=false;yield* emit(0xde5d,0xde5f,0xde61,0xde63,0xde65);let value=byte>>>4;
          if(value){yield* emit(0xde67);value=(value+offset)&255;}yield* emit(0xde69);m[destination--]=value;
          yield* emit(0xde6a);byte=m[source--];yield* emit(0xde6b);left--;
        }while(left);
        yield* emit(0xde6d,0xde6e);
      }while(--rows);
    }
    yield* emit(0xde70,0xde71,0xde72,0xde73,0xde74,0xde76,0xde77);
  }
}
