"use strict";
// Resident A112: indexed VGA sprites with clipping and original draw modes.
class OriginalSpriteWork {
  static singleStrings=new Set([0xa20d,0xa256,0xa259,0xa25f,0xa262,0xa265,0xa272,0xa27d,0xa288,0xa29a,0xa2a5,0xa2b4].map(a=>'resident:'+a.toString(16)));
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  static *run({mode,x,y,shape,surface,rows,sourcePixels,beforePixels,destinationPixels=null}){
    const emit=this.instructions,s16=n=>(n<<16)>>16,d=surface.map(s16);
    if(destinationPixels!==null&&!(destinationPixels instanceof Uint8Array))throw new Error('Shared sprite destination must be an indexed byte buffer');
    const out=destinationPixels??Uint8Array.from(beforePixels);let strings=0,writes=0;
    const read=i=>{if(i<0||i>=sourcePixels.length)throw new Error('Sprite reads outside shape');return sourcePixels[i];};
    const write=(i,value)=>{if(i<0||i>=out.length)throw new Error('Sprite writes outside surface');out[i]=value;writes++;};
    const exit=function*(){yield* emit(0xa182,0xa185,0xa187,0xa188,0xa189,0xa18b,0xa18c);};
    yield* emit(0xa112,0xa113,0xa115,0xa118,0xa119,0xa11a,0xa11e,0xa121,0xa124,0xa127,0xa129,0xa12b,0xa12e);
    let left=s16(x-d[3]),skipX=0;
    if(left<d[13]){yield* emit(0xa130,0xa133);skipX=s16(d[13]-left);left=d[13];}
    yield* emit(0xa135,0xa138,0xa13a,0xa13e,0xa140,0xa143);
    let right=s16(left+shape[1]-skipX);if(right>d[15]){yield* emit(0xa145);right=d[15];}
    yield* emit(0xa148,0xa14b,0xa14d,0xa150);const width=s16(right-left);
    let top=0,skipY=0,height=0;
    if(width>0){
      yield* emit(0xa152,0xa155,0xa158,0xa15a,0xa15c,0xa15f);top=s16(y-d[2]);
      if(top<d[12]){yield* emit(0xa161,0xa164);skipY=s16(d[12]-top);top=d[12];}
      yield* emit(0xa166,0xa169,0xa16c,0xa16e,0xa171,0xa173,0xa176);
      let bottom=s16(top+shape[0]-skipY);if(bottom>d[14]){yield* emit(0xa178);bottom=d[14];}
      yield* emit(0xa17b,0xa17e,0xa180);height=s16(bottom-top);
    }
    if(width<=0||height<=0){yield* exit();return {drawn:false,pixels:out,strings,writes};}
    yield* emit(0xa18f,0xa192,0xa194);yield {call:'cursor-prepare',surface,rect:[top,left,top+height,right]};
    yield* emit(0xa197,0xa19a,0xa19c,0xa19f,0xa1a1,0xa1a4,0xa1a7,0xa1aa,0xa1ad,0xa1b0,0xa1b3,0xa1b6,0xa1b8,0xa1bb,0xa1bd,0xa1bf,0xa1c1,0xa1c3,0xa1c5,0xa1c7,0xa1c9,0xa1cb,0xa1cd,0xa1cf,0xa1d1,0xa1d3,0xa1d6,0xa1d8,0xa1db,0xa1de,0xa1e1);
    const op=mode&3,xor=mode&4?255:0;
    if(mode===8)yield* emit(0xa245,0xa248,0xa24a);
    else{
      yield* emit(0xa1e3,0xa1e6);
      if(mode===10)yield* emit(0xa24c,0xa24f);
      else{
        yield* emit(0xa1e8,0xa1eb,0xa1f0,0xa1f2,0xa1f4,0xa1f7,0xa1fc);
        if(!op){yield* emit(0xa1fe,0xa200);if(!xor)yield* emit(0xa202,0xa205);}
      }
    }
    let sourceAt=skipY*shape[2]+skipX,destAt=rows[top]+left;
    for(let row=0;row<height;row++){
      yield* emit(0xa231,0xa234,0xa237,0xa23a);let si=sourceAt,di=destAt;
      if(mode===8){
        for(let col=0;col<width;col++){
          yield* emit(0xa288);const value=read(si++);strings++;yield* emit(0xa289,0xa28b);
          if(value){yield* emit(0xa28d);write(di,0);}yield* emit(0xa290);di++;yield* emit(0xa291);
        }yield* emit(0xa293);
      }else if(mode===10){
        yield* emit(0xa296,0xa298);let pairs=width>>>1;
        if(width&1){
          yield* emit(0xa29a);const value=read(si++);strings++;yield* emit(0xa29b,0xa29d);
          if(value){yield* emit(0xa29f);write(di,value);}yield* emit(0xa2a2);di++;yield* emit(0xa2a3);
        }
        let lastSecond=false;
        for(let col=0;col<pairs;col++){
          yield* emit(0xa2a5);const first=read(si++),second=read(si++);strings++;
          yield* emit(0xa2a6,0xa2a8,0xa2aa);if(first){yield* emit(0xa2ac);write(di,first);}
          yield* emit(0xa2af);di++;yield* emit(0xa2b0,0xa2b2);lastSecond=!!second;
          if(second){yield* emit(0xa2b4);write(di++,second);strings++;yield* emit(0xa2b5);}
          else{yield* emit(0xa2ba);di++;yield* emit(0xa2bb);}
        }
        yield* emit(pairs&&lastSecond?0xa2b7:0xa2bd);
      }else if(!op&&!xor){
        yield* emit(0xa207);let remaining=width>>>1;
        do{
          yield* emit(0xa209);const completed=yield {call:'rep-move-words',address:0xa209,remaining};
          if(!Number.isInteger(completed)||completed<0||completed>remaining||(remaining&&completed===0))throw new Error('Invalid sprite REP progress');
          for(let i=0;i<completed;i++){const low=read(si++),high=read(si++);write(di++,low);write(di++,high);}strings+=completed;remaining-=completed;
        }while(remaining);
        yield* emit(0xa20b);if(width&1){yield* emit(0xa20d);write(di,read(si));strings++;}
      }else if(!op){
        yield* emit(0xa251,0xa253);const pairs=width>>>1;
        if(pairs){
          yield* emit(0xa255);
          for(let i=0;i<pairs;i++){
            yield* emit(0xa256);const low=read(si++)^xor,high=read(si++)^xor;strings++;
            yield* emit(0xa257,0xa259);write(di++,low);write(di++,high);strings++;yield* emit(0xa25a);
          }yield* emit(0xa25c);
        }
        yield* emit(0xa25d);
        if(width&1){yield* emit(0xa25f);const value=read(si)^xor;strings++;yield* emit(0xa260,0xa262);write(di,value);strings++;yield* emit(0xa263);}
      }else{
        const at=op===1?0xa265:op===2?0xa272:0xa27d;
        for(let col=0;col<width;col++){
          yield* emit(at);const value=read(si++)^xor;strings++;yield* emit(at+1);
          if(op===1)yield* emit(0xa268);
          yield* emit(op===1?0xa26a:at+3);const old=out[di];write(di,op===1?old&value:op===2?old|value:old^value);
          yield* emit(op===1?0xa26d:at+6);di++;yield* emit(op===1?0xa26e:at+7);
        }yield* emit(op===1?0xa270:op===2?0xa27b:0xa286);
      }
      yield* emit(0xa20e,0xa211);
      if(row+1<height){
        yield* emit(0xa213,0xa216,0xa219,0xa21b,0xa21e,0xa221,0xa223,0xa225,0xa227,0xa229,0xa22b,0xa22e);
        sourceAt+=shape[2];destAt+=surface[6];
      }
    }
    yield* emit(0xa23c,0xa23d,0xa23e,0xa23f);yield {call:'cursor-restore'};yield* emit(0xa242);yield* exit();
    return {drawn:true,width,height,pixels:out,strings,writes};
  }
}
