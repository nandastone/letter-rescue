"use strict";
// DOS 1.1 VGA shape loading: E33C ownership, 7A66 source-resource caching,
// D5A7 converted storage and DF85/E03E scratch storage. No native event times.
class OriginalShapeLoading extends OriginalResourceLoading {
  static plan(payload){
    if(payload.length<6)throw new Error("Truncated original shape");
    const word=at=>payload[at]|payload[at+1]<<8;
    const height=word(0),width=word(2),flags=word(4),codec=(flags>>>8)&15;
    const bits=flags&0x8000?((flags>>>12)&7)+1:1;
    if(!width||!height||width*height>64000||![1,4,8].includes(bits)||codec>4)throw new Error("Unreconstructed original VGA shape layout");
    const stride=Math.ceil(width*bits/8),converted=width*height+6;
    return {width,height,flags,codec,bits,stride,sourceBytes:payload.length,convertedBytes:Math.max(converted,stride*height+6),finalBytes:converted,scratchBytes:codec===3||codec===4?1024:0};
  }
  load({key,payload,paletteHandle,directoryFlags}){
    const plan=OriginalShapeLoading.plan(payload),m=this.memory,paletteState=m.handle(paletteHandle).state;
    m.lock(paletteHandle);const source=this.source(key,payload,directoryFlags),sourceState=m.handle(source).state;m.lock(source);
    const converted=m.allocateHandle(plan.convertedBytes);this.operations.push({kind:'handle.allocate',bytes:plan.convertedBytes});m.lock(converted);
    if(plan.scratchBytes){const scratch=m.near.allocate(plan.scratchBytes);this.operations.push({kind:'near.allocate',bytes:plan.scratchBytes});m.near.free(scratch);this.operations.push({kind:'near.free'});}
    m.unlock(converted);
    if(!m.resizeHandle(converted,plan.finalBytes))throw new Error("Converted original shape did not fit its allocation");
    this.operations.push({kind:'resize',bytes:plan.finalBytes});
    m.flags(source,sourceState);m.flags(paletteHandle,paletteState);return converted;
  }
}
