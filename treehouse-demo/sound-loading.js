"use strict";
// Original E4AA/E6E6 source ownership and compressed-sound preparation.
// PCM/cache ownership is independent of optional instruction-work observers.
class OriginalSoundLoading extends OriginalResourceLoading {
  constructor(memory,catalogHandle,options={}){super(memory,catalogHandle,options);this.preparations=[];}
  static decodedPayload(payload){
    if(payload.length<13||!(payload[0]&1)||payload[3]!==255)throw new Error("Invalid compressed digital sound");
    const count=payload[10]|payload[11]<<8;
    if(!count)throw new Error("Empty compressed digital sound");
    const result=new Uint8Array(count+10);result.set(payload.slice(0,10));
    // E915/E920 replace codec and declared count with the decoded stream count.
    result[3]=8;result[4]=count&255;result[5]=count>>>8;
    let value=payload[12],width=0,bit=104,written=1;result[10]=value;
    while(written<count){
      let code=0;
      for(let remaining=width||3;remaining;remaining--){
        if(bit>=payload.length*8)throw new Error("Truncated compressed digital sound");
        code=2*code+((payload[bit>>>3]>>>(7-(bit&7)))&1);bit++;
      }
      if(width){
        const marker=1<<(width-1);
        if(code===marker){width=0;continue;}
        value=(value+(code>marker?code-(1<<width):code))&255;
        result[10+written++]=value;
      }else if(code===7){value=(value+128)&255;result[10+written++]=value;}
      else width=code+2;
    }
    return result;
  }
  prepare(handle,payload,{minimumRate,maximumRate}){
    const m=this.memory;
    if(m.handle(handle).state&0x2000)return {action:'prepared'};
    const pointer=m.address(handle);if(!pointer)return {action:'missing'};
    if(!(payload[0]&1))return {action:'non-digital'};
    if(payload.length<10)throw new Error("Truncated original sound header");
    const word=at=>payload[at]|payload[at+1]<<8,rate=word(1),codec=payload[3];
    if(!Number.isInteger(minimumRate)||!Number.isInteger(maximumRate)||rate<minimumRate||rate>maximumRate)throw new Error("Sound resampling ownership is not yet reconstructed");
    if(codec===8)return {action:'uncompressed',bytes:m.heap.at(pointer-6).size-6-m.heap.at(pointer-6).padding};
    if(codec!==255||payload.length<13||!word(10))throw new Error("Unsupported original compressed sound");
    const count=word(10),block=m.heap.at(pointer-6),packedBytes=block.size-6-block.padding-10;
    const temporaryBytes=Math.max(count,packedBytes)+256+10,finalBytes=count+10;
    const decoded=OriginalSoundLoading.decodedPayload(payload);
    if(!m.resizeHandle(handle,temporaryBytes))throw new Error("Cannot expand original sound cache");
    this.operations.push({kind:'handle.resize',bytes:temporaryBytes});
    const expandedPointer=m.address(handle);
    const copy={from:expandedPointer+10,to:expandedPointer+temporaryBytes-packedBytes,bytes:packedBytes};
    this.payloads.set(handle,decoded);
    // E935 shrinks the same handle after decompression; EC40 marks it ready.
    if(!m.resizeHandle(handle,finalBytes))throw new Error("Cannot finish original sound cache");
    this.operations.push({kind:'handle.resize',bytes:finalBytes});m.keepResident(handle);
    return {action:'decoded',temporaryBytes,finalBytes,count,copy};
  }
  load({key,payload,directoryFlags,minimumRate,maximumRate}){
    const handle=this.source(key,payload,directoryFlags),preparation=this.prepare(handle,payload,{minimumRate,maximumRate});
    this.preparations.push(preparation);return preparation.action==='missing'?0:handle;
  }
}
