"use strict";
// Resident D580/DA63/D5A7 conversion planning. Allocation remains an explicit
// guest callee until its ordered allocator is attached to this memory store.
class OriginalShapeConversionWork {
  constructor({memory,ds,heap=null}){this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);this.heap=heap;this.codec=heap?new OriginalShapeCodecWork({memory,ds}):null;}
  static get singleStrings(){return new Set([...OriginalShapeCodecWork.singleStrings,'resident:d718','resident:d719','resident:d71a']);}
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  word(at){return this.view.getUint16(at,true);}
  put(at,n){this.view.setUint16(at,n&65535,true);}
  *palette(pointer){
    const emit=OriginalShapeConversionWork.instructions;
    yield* emit(0xda63,0xda64,0xda66,0xda69,0xda6a,0xda6b,0xda6e,0xda71);let value;
    if(pointer){
      yield* emit(0xda76,0xda79,0xdb22,0xdb23,0xdb26);const mode=this.word(this.base+0x206a);
      if(mode>=1&&mode<=7){
        yield* emit(0xdb28,0xdb2a,0xdb2b);
        if(mode!==5&&mode!==7)throw new Error('Non-indexed palette conversion requires composition');
        yield* emit(0xdb15,0xdb18);value=this.word(pointer);yield* emit(0xdb1b,0xdb1e,0xdb20);
      }
    }else yield* emit(0xda73);
    yield* emit(0xdb3e,0xdb41,0xdb42,0xdb43,0xdb45,0xdb46);return value;
  }
  *sourceStride(source){
    const emit=OriginalShapeConversionWork.instructions;yield* emit(0xd06f,0xd070,0xd072,0xd075,0xd076,0xd079,0xd07d,0xd080,0xd083,0xd086,0xd08a);
    const flags=this.word(source+4),width=this.word(source+2);let stride;
    if(flags&0x8000){
      yield* emit(0xd0a3,0xd0a6,0xd0a9,0xd0ac,0xd0ae,0xd0b0,0xd0b1,0xd0b4,0xd0b8,0xd0bb,0xd0bd);stride=(((((flags>>>12)&7)+1)*width+7)&65535)>>>3;
    }else{
      yield* emit(0xd08c,0xd090,0xd093,0xd094,0xd096,0xd098,0xd09b,0xd09d,0xd09f,0xd0a1);const signed=((width+7)<<16)>>16;stride=(Math.trunc(signed/8))&65535;
    }
    yield* emit(0xd0bf,0xd0c0,0xd0c2,0xd0c3);return stride;
  }
  *destinationStride(width){
    const emit=OriginalShapeConversionWork.instructions,mode=this.word(this.base+0x206a);yield* emit(0xd366,0xd367,0xd369,0xd36e);let stride;
    if(mode!==5)yield* emit(0xd370,0xd375);
    if(mode===5||mode===7){yield* emit(0xd377,0xd37a);stride=width;}
    else{
      yield* emit(0xd37c,0xd37f,0xd384);const last=((width-1)<<16)>>16;if(mode!==4)yield* emit(0xd386,0xd38b);
      if(mode===4||mode===6){yield* emit(0xd38d,0xd390,0xd392,0xd394,0xd395);stride=(last>>3)+1;}
      else{
        yield* emit(0xd397,0xd39c);if(mode===3)yield* emit(0xd39e);else yield* emit(0xd3a5,0xd3a8,0xd3aa);
        yield* emit(0xd3a1,0xd3a3,0xd394,0xd395);stride=(last>>(mode===3?1:2))+1;
      }
    }yield* emit(0xd3ac,0xd3ae,0xd3af);return stride&65535;
  }
  *multiply(a,b){
    const emit=OriginalShapeConversionWork.instructions;yield* emit(0x10a8,0x10a9,0x10ab,0x10ae,0x10b1,0x10b3,0x10b6);
    if((a>>>16)||(b>>>16))yield* emit(0x10c1,0x10c2,0x10c4,0x10c6,0x10c9,0x10cc,0x10ce,0x10d1,0x10d3,0x10d5,0x10d6,0x10d7);
    else yield* emit(0x10b8,0x10bb,0x10bd,0x10be);return Math.imul(a,b)>>>0;
  }
  *convert({source,palette}){
    const emit=OriginalShapeConversionWork.instructions;yield* emit(0xd580,0xd581,0xd583,0xd587,0xd58a,0xd58d,0xd591,0xd592,0xd595,0xd598,0xd599);
    const table=yield* this.palette(palette);yield* emit(0xd59c,0xd59d,0xd59e);
    const result=yield* this.convertPrepared({source,table});yield* emit(0xd5a1,0xd5a3,0xd5a4);return result;
  }
  *convertPrepared({source,table}){
    const emit=OriginalShapeConversionWork.instructions,signed=n=>(n<<16)>>16;
    yield* emit(0xd5a7,0xd5a8,0xd5aa,0xd5ad,0xd5ae,0xd5af,0xd5b2,0xd5b6,0xd5b9,0xd5bc,0xd5bf,0xd5c2,0xd5c5,0xd5c8,0xd5ca,0xd5cc,0xd5cf,0xd5d1);
    const flags=this.word(source+4),planar=!(flags&0x8000);let mono=false;
    if(planar){yield* emit(0xd5d3,0xd5d7);mono=!(flags&0x7000);}
    if(mono)yield* emit(0xd5d9,0xd5de);else yield* emit(0xd5e0);
    yield* emit(0xd5e5,0xd5e6,0xd5e9,0xd5ea);const sourceStride=yield* this.sourceStride(source);
    yield* emit(0xd5ed,0xd5f0);this.put(source+4,sourceStride);yield* emit(0xd5f4,0xd5f7,0xd5fa,0xd5fd,0xd602);
    const mode=this.word(this.base+0x206a),height=this.word(source),width=this.word(source+2);let sourceBytes=Math.imul(signed(sourceStride),signed(height))>>>0;
    if(mode!==6)yield* emit(0xd604,0xd609);
    if(mode===4||mode===6){yield* emit(0xd60b,0xd60f);if(planar)throw new Error('Planar intermediate sizing requires composition');}
    yield* emit(0xd629,0xd62c,0xd62f,0xd633,0xd637,0xd63a,0xd63d,0xd640,0xd644,0xd645);
    const destinationStride=yield* this.destinationStride(width);yield* emit(0xd648,0xd64b,0xd650);if(mode!==4)yield* emit(0xd652,0xd657);
    const destinationPlanar=mode===4||mode===6;if(destinationPlanar)yield* emit(0xd659,0xd65e);else yield* emit(0xd660);
    yield* emit(0xd665,0xd667,0xd668,0xd669,0xd66c,0xd66f,0xd670,0xd671,0xd672,0xd674,0xd678,0xd67a,0xd67c,0xd67e,0xd681,0xd683,0xd685,0xd687,0xd688,0xd689,0xd68a,0xd68b,0xd68d,0xd68e,0xd68f);
    const expandedRows=yield* this.multiply(signed(height),1+3*(!mono&&destinationPlanar));
    yield* emit(0xd692,0xd693,0xd694,0xd695,0xd696);const destinationBytes=yield* this.multiply(expandedRows,destinationStride);
    yield* emit(0xd699,0xd69c,0xd69f,0xd6a2,0xd6a5,0xd6a6,0xd6a7,0xd6aa,0xd6ae,0xd6af,0xd6b0,0xd6b1,0xd6b2,0xd6b3);
    const pixels=yield* this.multiply(signed(width),signed(height));yield* emit(0xd6b6,0xd6b8);if(!(pixels>>>16))yield* emit(0xd6ba,0xd6bd);
    if(pixels>0xfa64){yield* emit(0xd6bf);this.put(this.base+0x2464,0xe380);yield* emit(0xd6c5);}else{yield* emit(0xd6c7);this.put(this.base+0x2464,0xfa64);}
    yield* emit(0xd6cd,0xd6d1,0xd6d5,0xd6d8,0xd6db,0xd6de);const destinationSize=(destinationBytes+6)>>>0,sourceSize=(sourceBytes+6)>>>0;
    let bytes=destinationSize;
    if((destinationSize>>>16)<=(sourceSize>>>16)){
      yield* emit(0xd6e0);if((destinationSize>>>16)===(sourceSize>>>16))yield* emit(0xd6e2,0xd6e5);
      if(destinationSize<sourceSize){yield* emit(0xd6e7,0xd6ea);bytes=sourceSize;}
    }
    yield* emit(0xd6ed,0xd6ee,0xd6ef,0xd6f0,0xd6f1);
    const handle=this.heap?yield* this.heap.allocate(bytes):yield {call:'allocate-shape',bytes};
    yield* emit(0xd6f4,0xd6f7,0xd6f9);if(!handle)throw new Error('Failed converted allocation requires composition');
    if(!this.heap||!this.codec)throw new Error('Converted allocation lifecycle requires composition');
    yield* emit(0xd6fe,0xd6ff,0xd700,0xd701);const destination=yield* this.heap.lock(handle);
    yield* emit(0xd704,0xd707,0xd70a,0xd70d,0xd710,0xd711,0xd713,0xd715);
    for(let i=0;i<3;i++){yield* emit(0xd718+i);this.put(destination+2*i,this.word(source+2*i));}
    yield* emit(0xd71b,0xd71c,0xd71e,0xd720,0xd723,0xd726,0xd728,0xd72c,0xd72e);
    let rows=Math.floor(this.word(this.base+0x2464)/width);if(rows>height){yield* emit(0xd730);rows=height;}
    yield* emit(0xd732,0xd735,0xd738,0xd73d);if(mode!==6)yield* emit(0xd73f,0xd744);
    if(mode===4||mode===6)throw new Error('Planar destination conversion requires composition');
    yield* emit(0xd75d,0xd760,0xd764,0xd767,0xd76a,0xd76f,0xd771,0xd776,0xd78f,0xd794,0xd796,0xd79b,0xd7a4,0xd7a9,0xd7ad,0xd7af,0xd7b1,0xd7b4,0xd7b6,0xd7b8,0xd7ba,0xd7bb,0xd7be,0xd7c1,0xd7c4,0xd7c7,0xd7ca,0xd7cd,0xd7d0,0xd7d3,0xd7d6,0xd7d9,0xd7dc,0xd7df,0xd7e2);
    let sourceChunk=(sourceStride*rows)&65535,destinationChunk=(destinationStride*rows)&65535,sourceLeft=sourceBytes,destinationLeft=destinationBytes,rowsLeft=height,read=source+6,write=destination+6;
    for(;;){
      yield* emit(0xda1e,0xda22);if(!rowsLeft)break;yield* emit(0xda24,0xd7e5,0xd7e8,0xd7ea,0xd7ed);
      if(!(destinationLeft>>>16)){yield* emit(0xd7ef,0xd7f1,0xd7f4);if(destinationChunk>destinationLeft){yield* emit(0xd7f6);destinationChunk=destinationLeft;}}
      yield* emit(0xd7f9,0xd7fc,0xd7ff,0xd802,0xd803,0xd804);yield* this.normalizePointer();
      yield* emit(0xd807,0xd80a,0xd80d,0xd810,0xd813,0xd814,0xd815);yield* this.normalizePointer();
      yield* emit(0xd818,0xd81b,0xd81e,0xd821,0xd824);if(rowsLeft>rows)yield* emit(0xd826);else rows=rowsLeft;
      yield* emit(0xd829,0xd82c,0xd82f);this.put(destination,rows);
      yield* emit(0xd832,0xd835,0xd838,0xd83b,0xd83e,0xd841,0xd843,0xd846);
      if(!(sourceLeft>>>16)){yield* emit(0xd848,0xd84a,0xd84d);if(sourceChunk>sourceLeft){yield* emit(0xd84f);sourceChunk=sourceLeft;}}
      yield* emit(0xd852,0xd855,0xd856,0xd859,0xd85d,0xd85e,0xd861,0xd864,0xd867,0xd868,0xd869);
      const consumed=yield* this.decode({codec:(flags>>>8)&15,rows,stride:sourceStride,length:sourceChunk,source:read,destination:write});
      yield* emit(0xd86c);read+=consumed;yield* emit(0xd86f,0xd873);
      if(planar)throw new Error('Planar source conversion requires composition');
      yield* emit(0xd875,0xd878,0xd87b,0xd87d,0xd87f);
      if((flags&0x7000)!==0x3000)throw new Error('Other indexed source depths require composition');
      yield* emit(0xd884,0xd889,0xd88b,0xd890,0xd892,0xd897,0xd8e3,0xd8e8);if(mode!==5)yield* emit(0xd8ea,0xd8ef);
      if(mode!==5&&mode!==7)throw new Error('Other destination video modes require composition');
      yield* emit(0xd8f1,0xd8f4,0xd8f7,0xd8fa,0xd8fd,0xd900,0xd902,0xd903);const paletteShift=yield* this.lowestBit(table);
      yield* emit(0xd906,0xd907,0xd908,0xd909);yield* this.codec.expandNibbles({header:destination,pixels:write,paletteShift});
      yield* emit(0xd90c,0xda01,0xda04);rowsLeft-=rows;
      yield* emit(0xda07,0xda0a,0xda0c,0xda0f);sourceLeft-=sourceChunk;
      yield* emit(0xda12,0xda15,0xda18,0xda1b);destinationLeft-=destinationChunk;write+=destinationChunk;
    }
    yield* emit(0xda27,0xda2a,0xda2d,0xda30);this.put(destination,this.word(source));yield* emit(0xda33,0xda36);this.put(destination+4,destinationStride);
    yield* emit(0xda3a,0xda3d,0xda3e,0xda3f);yield* this.heap.unlock(handle);
    yield* emit(0xda42,0xda43,0xda46,0xda49,0xda4a,0xda4b);yield* this.heap.resize(handle,destinationSize);
    yield* emit(0xda4e,0xda51,0xda54);this.put(source+4,flags);
    yield* emit(0xda58,0xda5b,0xda5c,0xda5d,0xda5f,0xda60);return handle;
  }
  *normalizePointer(){yield* OriginalShapeConversionWork.instructions(0xe256,0xe258,0xe25b,0xe25d,0xe260,0xe262,0xe264,0xe267);}
  *lowestBit(value){
    const emit=OriginalShapeConversionWork.instructions;yield* emit(0xd162,0xd163,0xd165,0xd168,0xd16d,0xd172);let index=0;
    for(;;){
      yield* emit(0xd17a,0xd17e);if(index>=16){yield* emit(0xd18d);index=0;break;}
      yield* emit(0xd180,0xd183,0xd186);if(value&(1<<index)){yield* emit(0xd188,0xd18b);break;}
      yield* emit(0xd174,0xd177);index++;
    }yield* emit(0xd18f,0xd191,0xd192);return index;
  }
  *decode(input){
    const emit=OriginalShapeConversionWork.instructions;yield* emit(0xd2cd,0xd2ce,0xd2d0,0xd2d3,0xd2d6,0xd2d7);
    if(input.codec===1)throw new Error('RLE codec execution requires composition');yield* emit(0xd2d9,0xd2da);
    if(input.codec===2)throw new Error('Column RLE codec execution requires composition');yield* emit(0xd2dc,0xd2dd);
    if(input.codec===3)throw new Error('Row LZ codec execution requires composition');yield* emit(0xd2df,0xd2e0);
    if(input.codec!==4)throw new Error('Raw codec copy execution requires composition');
    yield* emit(0xd330,0xd333,0xd336,0xd339,0xd33c,0xd33f,0xd342,0xd345,0xd346,0xd347);const consumed=yield* this.codec.columnLz(input);
    yield* emit(0xd34a,0xd360,0xd362,0xd363);return consumed;
  }
}
