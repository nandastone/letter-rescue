"use strict";
// Cursor resource ownership. The original cursor covers 16 by 16 pixels;
// its saved background stride follows the active graphics descriptor.
class OriginalCursorLoading {
  constructor(loader,pixelsPerByte){
    if(!Number.isInteger(pixelsPerByte)||pixelsPerByte<=0||16%pixelsPerByte)throw new Error("Invalid original cursor pixel packing");
    this.loader=loader;this.stride=16/pixelsPerByte;
    this.background=loader.memory.allocateRaw(16*this.stride);
    this.source=0;this.image=0;this.mask=0;
  }
  loadSource(key,payload,directoryFlags){
    this.source=this.loader.source(key,payload,directoryFlags);return this.source;
  }
  activate(){
    if(this.stride!==16)throw new Error("Only original VGA cursor conversion is reconstructed");
    const loader=this.loader,m=loader.memory,payload=loader.payloads.get(this.source);
    if(!payload||payload.length!==68)throw new Error("Invalid original cursor resource");
    const saved=m.handle(this.source).state;m.lock(this.source);
    const convert=(base,invert)=>{
      const bytes=new Uint8Array(262);bytes.set([16,0,16,0,16,0]);
      for(let y=0;y<16;y++)for(let x=0;x<16;x++){
        const bit=(payload[base+2*y+1-(x>>>3)]>>>(7-(x&7)))&1;
        bytes[6+16*y+x]=(bit^(invert?1:0))?255:0;
      }
      const id=m.allocateHandle(bytes.length);m.lock(id);m.unlock(id);
      if(!m.resizeHandle(id,bytes.length))throw new Error("Original cursor image resize failed");
      loader.payloads.set(id,bytes);return id;
    };
    const image=convert(36,false),mask=convert(4,true);
    for(const id of [this.image,this.mask])if(id){m.freeHandle(id);loader.payloads.delete(id);}
    m.promote(mask);m.lock(mask);m.promote(image);m.lock(image);
    this.image=image;this.mask=mask;
    this.hotspotX=(payload[0]|payload[1]<<8)<<16>>16;
    this.hotspotY=(payload[2]|payload[3]<<8)<<16>>16;
    m.flags(this.source,saved);return this;
  }
}
