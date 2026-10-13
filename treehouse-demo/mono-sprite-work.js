"use strict";
// Resident 9ED6: colourised masks used by glyphs and the two cursor planes.
class OriginalMonoSpriteWork {
  static singleStrings=new Set([0x9fc6,0xa000,0xa00d,0xa018].map(a=>'resident:'+a.toString(16)));
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  static *run({mode,color,x,y,shape,surface,rows,sourcePixels,beforePixels,destinationPixels=null}){
    const emit=this.instructions,s16=n=>(n<<16)>>16,d=surface.map(s16);
    if(destinationPixels!==null&&!(destinationPixels instanceof Uint8Array))throw new Error('Shared mask destination must be an indexed byte buffer');
    const out=destinationPixels??Uint8Array.from(beforePixels);let writes=0,strings=0;
    const read=i=>{if(i<0||i>=sourcePixels.length)throw new Error('Mask reads outside shape');return sourcePixels[i];};
    const write=(i,n)=>{if(i<0||i>=out.length)throw new Error('Mask writes outside surface');out[i]=n;writes++;};
    const exit=function*(){yield* emit(0x9f46,0x9f49,0x9f4b,0x9f4c,0x9f4d,0x9f4f,0x9f50);};
    yield* emit(0x9ed6,0x9ed7,0x9ed9,0x9edc,0x9edd,0x9ede,0x9ee2,0x9ee5,0x9ee8,0x9eeb,0x9eed,0x9eef,0x9ef2);
    let left=s16(x-d[3]),skipX=0;
    if(left<d[13]){yield* emit(0x9ef4,0x9ef7);skipX=s16(d[13]-left);left=d[13];}
    yield* emit(0x9ef9,0x9efc,0x9efe,0x9f02,0x9f04,0x9f07);
    let right=s16(left+shape[1]-skipX);if(right>d[15]){yield* emit(0x9f09);right=d[15];}
    yield* emit(0x9f0c,0x9f0f,0x9f11,0x9f14);const width=s16(right-left);
    let top=0,skipY=0,height=0;
    if(width>0){
      yield* emit(0x9f16,0x9f19,0x9f1c,0x9f1e,0x9f20,0x9f23);top=s16(y-d[2]);
      if(top<d[12]){yield* emit(0x9f25,0x9f28);skipY=s16(d[12]-top);top=d[12];}
      yield* emit(0x9f2a,0x9f2d,0x9f30,0x9f32,0x9f35,0x9f37,0x9f3a);
      let bottom=s16(top+shape[0]-skipY);if(bottom>d[14]){yield* emit(0x9f3c);bottom=d[14];}
      yield* emit(0x9f3f,0x9f42,0x9f44);height=s16(bottom-top);
    }
    if(width<=0||height<=0){yield* exit();return {drawn:false,pixels:out,strings,writes};}
    yield* emit(0x9f53,0x9f56,0x9f58);yield {call:'cursor-prepare',surface,rect:[top,left,top+height,right]};
    yield* emit(0x9f5b,0x9f5d,0x9f60,0x9f62,0x9f65,0x9f68,0x9f6b,0x9f6e,0x9f71,0x9f74,0x9f77,0x9f7a,0x9f7c,0x9f7f,0x9f81,0x9f83,0x9f85,0x9f87,0x9f89,0x9f8b,0x9f8d,0x9f8f,0x9f91,0x9f93,0x9f96,0x9f98,0x9f9a,0x9f9d,0x9f9f,0x9fa2,0x9fa5,0x9fa8,0x9fab,0x9fb0,0x9fb2,0x9fb4,0x9fb7,0x9fbc);
    const ink=(color&255)^(mode&4?255:0),op=mode&3;
    let sourceAt=skipY*shape[2]+skipX,destAt=rows[top]+left;
    for(let row=0;row<height;row++){
      yield* emit(0x9fd6,0x9fd9,0x9fdc,0x9fdf,0x9fe2,0x9fe5,0x9fe8,0x9fea,0x9fed,0x9ff0,0x9ff2,0x9ff4,0x9ff6,0x9ff8,0x9ffb,0x9ffe);
      let si=sourceAt,di=destAt;
      for(let col=0;col<width;col++){
        if(!op){
          yield* emit(0x9fc6);const pixel=read(si++);strings++;yield* emit(0x9fc7,0x9fc9);
          if(pixel){yield* emit(0x9fcb);write(di,ink);}yield* emit(0x9fce);di++;yield* emit(0x9fcf);
        }else{
          const at=op===1?0xa000:op===2?0xa00d:0xa018;
          yield* emit(at);const masked=read(si++)&ink;strings++;yield* emit(at+1);
          if(op===1)yield* emit(0xa003);
          yield* emit(op===1?0xa005:at+3);write(di,op===1?out[di]&(~masked&255):op===2?out[di]|masked:out[di]^masked);
          yield* emit(op===1?0xa008:at+6);di++;yield* emit(op===1?0xa009:at+7);
        }
      }
      if(op)yield* emit(op===1?0xa00b:op===2?0xa016:0xa021);
      yield* emit(0x9fd1,0x9fd4);sourceAt+=shape[2];destAt+=surface[6];
    }
    yield* emit(0x9fbe,0x9fbf,0x9fc0,0x9fc1);yield {call:'cursor-restore'};yield* emit(0x9fc4);yield* exit();
    return {drawn:true,width,height,pixels:out,strings,writes};
  }
}
