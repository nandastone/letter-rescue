"use strict";
// Resident 82E2 retains a screen rectangle with a near descriptor/row table
// and an independently owned raw pixel allocation.
class OriginalSavedSurface {
  constructor(memory,{bounds,pixelsPerByte=1,originLeft=0}){
    if(!Array.isArray(bounds)||bounds.length!==4||bounds.some(v=>!Number.isInteger(v))||![1,2,4,8].includes(pixelsPerByte)||!Number.isInteger(originLeft))throw new Error("Invalid original saved surface");
    const [top,left,bottom,right]=bounds,height=bottom-top,width=right-left;
    if(height<0||width<0)throw new Error("Invalid original surface extent");
    const alignment=(left-originLeft)&(pixelsPerByte-1);
    this.stride=Math.floor((alignment+width+pixelsPerByte-1)/pixelsPerByte);
    this.bounds=[top,left-alignment,bottom,right];this.memory=memory;
    this.descriptor=memory.near.allocate(24+2*height);
    this.pixels=memory.allocateRaw(this.stride*height);
  }
  dispose(){
    if(!this.descriptor)throw new Error("Original saved surface already released");
    this.memory.freeRaw(this.pixels);this.memory.near.free(this.descriptor);
    this.pixels=0;this.descriptor=0;
  }
}
