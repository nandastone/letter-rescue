"use strict";
// Resident A034 VGA rectangle fill. Coordinates clip against the active surface.
class OriginalRectFillWork {
  static singleStrings=new Set(['resident:a0dc']);
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  static *run({mode,color,rect,surface,rows,beforePixels,destinationPixels=null}){
    const emit=this.instructions,s16=n=>(n<<16)>>16,d=surface.map(s16),r=rect.map(s16);
    if(destinationPixels!==null&&!(destinationPixels instanceof Uint8Array))throw new Error('Shared fill destination must be an indexed byte buffer');
    const out=destinationPixels??Uint8Array.from(beforePixels);let writes=0,strings=0;
    const write=(i,n)=>{if(i<0||i>=out.length)throw new Error('Fill writes outside surface');out[i]=n;writes++;};
    const exit=function*(){yield* emit(0xa0c9,0xa0cc,0xa0ce,0xa0cf,0xa0d0,0xa0d2,0xa0d3);};
    yield* emit(0xa034,0xa035,0xa037,0xa03a,0xa03b,0xa03c,0xa040,0xa043,0xa047,0xa04a,0xa04d);
    let left=s16(r[1]-d[3]);if(left<d[13]){yield* emit(0xa04f);left=d[13];}
    yield* emit(0xa052,0xa055,0xa059,0xa05c,0xa05f);let right=s16(r[3]-d[3]);
    if(right>d[15]){yield* emit(0xa061);right=d[15];}
    yield* emit(0xa064,0xa067,0xa069);const width=s16(right-left);let top=0,bottom=0,height=0;
    if(width>0){
      yield* emit(0xa06b,0xa06e,0xa071,0xa074,0xa077);top=s16(r[0]-d[2]);
      if(top<d[12]){yield* emit(0xa079);top=d[12];}
      yield* emit(0xa07c,0xa07f,0xa083,0xa086,0xa089);bottom=s16(r[2]-d[2]);
      if(bottom>d[14]){yield* emit(0xa08b);bottom=d[14];}
      yield* emit(0xa08e,0xa091,0xa093);height=s16(bottom-top);
    }
    if(width<=0||height<=0){yield* exit();return {drawn:false,pixels:out,strings,writes};}
    yield* emit(0xa095,0xa098,0xa09b,0xa09d,0xa0a0,0xa0a2,0xa0a4,0xa0a6);
    yield {call:'cursor-prepare',surface,rect:[top,left,bottom,right]};
    yield* emit(0xa0a9,0xa0ac,0xa0af,0xa0b4,0xa0b7,0xa0b9,0xa0bb,0xa0be,0xa0c3);
    const ink=(color&255)^(mode&4?255:0),op=mode&3;let destAt=rows[top]+left;
    for(let row=0;row<height;row++){
      yield* emit(0xa0e3,0xa0e6,0xa0e8);let di=destAt;
      if(op===0){
        yield* emit(0xa0d6);let remaining=width>>>1;
        do{
          yield* emit(0xa0d8);const completed=yield {call:'rep-store-words',address:0xa0d8,remaining};
          if(!Number.isInteger(completed)||completed<0||completed>remaining||(remaining&&completed===0))throw new Error('Invalid fill REP progress');
          for(let i=0;i<completed;i++){write(di++,ink);write(di++,ink);}strings+=completed;remaining-=completed;
        }while(remaining);
        yield* emit(0xa0da);if(width&1){yield* emit(0xa0dc);write(di,ink);strings++;}
      }else{
        const at=op===1?0xa0fa:op===2?0xa0f2:0xa0ea;
        for(let col=0;col<width;col++){
          yield* emit(at);write(di,op===1?out[di]&ink:op===2?out[di]|ink:out[di]^ink);yield* emit(at+3);di++;yield* emit(at+4);
        }
        yield* emit(at+6);
      }
      yield* emit(0xa0dd,0xa0de);if(row+1<height){yield* emit(0xa0e0);destAt+=surface[6];}
    }
    yield* emit(0xa0c5,0xa0c6);yield {call:'cursor-restore'};yield* exit();return {drawn:true,width,height,pixels:out,strings,writes};
  }
}
