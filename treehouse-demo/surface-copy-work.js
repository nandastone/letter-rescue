"use strict";
// VGA surface copy, resident 9A68. All writes come from source pixels and
// clipping/overlap rules. REP progress is supplied by the shared CPU executor.
class OriginalSurfaceCopyWork {
  static singleStrings=new Set([0x9a7e,0x9a8b,0x9a98,0x9aa5,0x9abc,0x9acd,0x9ade,0x9aef,0x9bfc,0x9c05,0x9c30,0x9c33,0x9c38,0x9c3e,0x9c43,0x9c49,0x9c4e,0x9c54].map(a=>'resident:'+a.toString(16)));
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16).padStart(4,'0');}
  static *run({mode,context,source_id,destination_id,source,destination,source_rect,destination_rect,source_rows,destination_rows,sourcePixels,beforePixels,destinationPixels=null}){
    const emit=this.instructions,s16=n=>(n<<16)>>16,s=source.map(s16),d=destination.map(s16),sr=source_rect.map(s16),dr=destination_rect.map(s16);
    if(destinationPixels!==null&&!(destinationPixels instanceof Uint8Array))throw new Error('Shared copy destination must be an indexed byte buffer');
    const out=destinationPixels??Uint8Array.from(beforePixels),sourceBase=16*source[1]+source[0],destinationBase=16*destination[1]+destination[0];
    let strings=0,writes=0;
    const read=address=>{if(address>=destinationBase&&address<destinationBase+out.length)return out[address-destinationBase];const i=address-sourceBase;if(i<0||i>=sourcePixels.length)throw new Error('Copy reads outside its source surface');return sourcePixels[i];};
    const write=(at,value)=>{if(at<0||at>=out.length)throw new Error('Copy writes outside its destination surface');out[at]=value;writes++;};
    yield* emit(0x9a68,0x9a69,0x9a6b,0x9a6e,0x9a6f,0x9a70,0x9a73,0x9a76,0x9a79,0x9a7c,0x9a7e,0x9a80,0x9a83);strings++;
    let st=s16(sr[0]-s[2]),cutTop=0;
    if(sr[0]<s[2]){yield* emit(0x9a85);cutTop=st;st=0;}
    yield* emit(0x9a86,0x9a89,0x9a8b,0x9a8d,0x9a90);strings++;
    let sl=s16(sr[1]-s[3]),cutLeft=0;
    if(sr[1]<s[3]){yield* emit(0x9a92);cutLeft=sl;sl=0;}
    yield* emit(0x9a93,0x9a96,0x9a98,0x9a9a,0x9a9d);strings++;
    let cutBottom=0;if(sr[2]>s[4]){yield* emit(0x9a9f);cutBottom=s16(sr[2]-s[4]);}
    yield* emit(0x9aa0,0x9aa3,0x9aa5,0x9aa7,0x9aaa);strings++;
    let cutRight=0;if(sr[3]>s[5]){yield* emit(0x9aac);cutRight=s16(sr[3]-s[5]);}
    yield* emit(0x9aad,0x9ab0,0x9ab3,0x9ab6,0x9ab9,0x9abc,0x9abe,0x9ac0,0x9ac3);strings++;
    let dt=s16(dr[0]-cutTop-d[2]);
    if(s16(dr[0]-cutTop)<d[2]){yield* emit(0x9ac5,0x9ac8);st=s16(st-dt);dt=0;}
    yield* emit(0x9aca,0x9acd,0x9acf,0x9ad1,0x9ad4);strings++;
    let dl=s16(dr[1]-cutLeft-d[3]);
    if(s16(dr[1]-cutLeft)<d[3]){yield* emit(0x9ad6,0x9ad9);sl=s16(sl-dl);dl=0;}
    yield* emit(0x9adb,0x9ade,0x9ae0,0x9ae3,0x9ae6);strings++;
    let db=s16(dr[2]-cutBottom);if(db>d[4]){yield* emit(0x9ae8);db=d[4];}
    yield* emit(0x9aeb,0x9aee);db=s16(db-d[2]);
    yield* emit(0x9aef,0x9af1,0x9af4,0x9af7);strings++;
    let right=s16(dr[3]-cutRight);if(right>d[5]){yield* emit(0x9af9);right=d[5];}
    yield* emit(0x9afc,0x9aff,0x9b00,0x9b04);right=s16(right-d[3]);
    if(destination_id===context){
      yield* emit(0x9b06,0x9b09,0x9b0c);
      if(d[12]>dt){yield* emit(0x9b0e,0x9b11);st=s16(st+s16(d[12]-dt));dt=d[12];}
      yield* emit(0x9b14,0x9b17,0x9b1a);
      if(d[13]>dl){yield* emit(0x9b1c,0x9b1f);sl=s16(sl+s16(d[13]-dl));dl=d[13];}
      yield* emit(0x9b22,0x9b25);if(db>d[14]){yield* emit(0x9b27);db=d[14];}
      yield* emit(0x9b2a,0x9b2d);if(right>d[15]){yield* emit(0x9b2f);right=d[15];}
    }
    yield* emit(0x9b32,0x9b35,0x9b38,0x9b3b);const height=s16(db-dt);let width=0;
    if(height>0){yield* emit(0x9b3d,0x9b40);width=s16(right-dl);}
    const exit=function*(){yield* emit(0x9b42,0x9b43,0x9b44,0x9b46,0x9b47);};
    if(height<=0||width<=0){yield* exit();return {copied:false,pixels:out,strings,writes};}
    yield* emit(0x9b4a,0x9b4d,0x9b50,0x9b53,0x9b56,0x9b59,0x9b5c,0x9b5e,0x9b61,0x9b63,0x9b66);
    yield {call:'cursor-prepare',surface:source,rect:[st,sl,st+height,sl+width]};
    yield* emit(0x9b69,0x9b6b,0x9b6e);yield {call:'cursor-prepare',surface:destination,rect:[dt,dl,db,right]};
    yield* emit(0x9b71,0x9b73,0x9b76,0x9b79,0x9b7b,0x9b7e,0x9b81,0x9b83);
    let reverseRows=false,reverseColumns=false;
    if(source[0]===destination[0]){
      yield* emit(0x9b85,0x9b87,0x9b8a);
      if(source[1]===destination[1]){
        yield* emit(0x9b8c,0x9b8e);
        if(dt>st){yield* emit(0x9b90,0x9b93,0x9b94,0x9b96,0x9b98,0x9b9b);dt+=height-1;st+=height-1;reverseRows=true;}
        yield* emit(0x9b9e,0x9ba0);
        if(dl>sl){yield* emit(0x9ba2,0x9ba5,0x9ba6,0x9ba8,0x9baa);dl+=width-1;sl+=width-1;reverseColumns=true;}
      }
    }
    yield* emit(0x9bab,0x9bad,0x9baf,0x9bb1,0x9bb4,0x9bb6,0x9bb9,0x9bbc,0x9bbe,0x9bc0,0x9bc2,0x9bc6,0x9bc9,0x9bcc,0x9bcf,0x9bd2,0x9bd7,0x9bd9,0x9bdc,0x9be1);
    const op=mode&3,xor=mode&4?255:0,dx=reverseColumns?-1:1;
    let branch=[0x9c30,0x9c38,0x9c43,0x9c4e][op];
    if(!op){yield* emit(0x9be3,0x9be6,0x9be7,0x9be8,0x9beb);branch=0x9bff;if(reverseColumns){yield* emit(0x9bed,0x9bf0);branch=0x9bf2;}}
    let sourceAt=sl+source_rows[st],destAt=dl+destination_rows[dt];
    for(let row=0;row<height;row++){
      yield* emit(0x9c17,0x9c1a,0x9c1d,0x9c20);
      let si=sourceAt,di=destAt;
      if(!op){
        if(reverseColumns){yield* emit(0x9bf2,0x9bf3,0x9bf4);si--;di--;}
        else yield* emit(0x9bff);
        const at=reverseColumns?0x9bf6:0x9c01;let remaining=width>>>1;
        do{
          yield* emit(at);
          const completed=yield {call:'rep-move-words',address:at,remaining};
          if(!Number.isInteger(completed)||completed<0||completed>remaining||(remaining&&completed===0))throw new Error('Invalid REP progress');
          for(let i=0;i<completed;i++){
            const low=read(sourceBase+si),high=read(sourceBase+si+1);write(di,low);write(di+1,high);si+=2*dx;di+=2*dx;
          }
          strings+=completed;remaining-=completed;
        }while(remaining);
        yield* emit(reverseColumns?0x9bf8:0x9c03);
        if(width&1){
          if(reverseColumns){yield* emit(0x9bfa,0x9bfb,0x9bfc);di++;si++;}else yield* emit(0x9c05);
          write(di,read(sourceBase+si));strings++;
          if(reverseColumns)yield* emit(0x9bfd);
        }
      }else{
        for(let col=0;col<width;col++){
          yield* emit(branch,branch+1);const value=read(sourceBase+si)^xor;si+=dx;strings++;
          yield* emit(branch+3);const old=out[di];const pixel=op===1?value&old:op===2?value|old:value^old;
          yield* emit(branch+6);write(di,pixel);di+=dx;strings++;
          yield* emit(branch+7);
        }
        yield* emit(op===1?0x9c41:op===2?0x9c4c:0x9c57);
      }
      yield* emit(0x9c06,0x9c09);
      if(row+1<height){
        yield* emit(0x9c0b,0x9c0e,0x9c11,0x9c14);
        destAt+=destination[6]*(reverseRows?-1:1);sourceAt+=source[6]*(reverseRows?-1:1);
      }
    }
    yield* emit(0x9c22,0x9c23,0x9c24,0x9c25,0x9c26);yield {call:'cursor-restore'};
    yield* emit(0x9c29,0x9c2a);yield {call:'cursor-restore'};yield* emit(0x9c2d);yield* exit();
    return {copied:true,width,height,pixels:out,strings,writes};
  }
}
