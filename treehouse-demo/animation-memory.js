"use strict";
// Main C39D/BD14 object ownership and resident 7C96 VGA surface storage.
// Rendering/composition remains the caller's responsibility.
class OriginalAnimationMemory {
  static prepare(memory,{script,first=1,last,paletteHandle,saveBackground=true,loadShape,releaseTemporarySurface=()=>{},composeInitial=()=>{}}){
    if(first!==1)throw new Error("Only original whole-palette animation preparation is reconstructed");
    // C449..C567 scans the whole script before any display. C5AC then loads
    // each referenced shape once, in ascending relative order. Neither the
    // caller nor a captured allocation stream specifies those requests.
    const marked=new Set();
    for(const [code,operand] of script.code){
      if(code===0)break;
      if((code&0xf0)!==0xc0)continue;
      const begin=operand[0]|operand[1]<<8,end=operand[2]|operand[3]<<8;
      if(!begin)continue;
      for(let relative=begin;relative<=end;relative++){
        if(relative<first||relative>last)throw new Error("Animation shape outside owned range");
        marked.add(relative);
      }
    }
    const saved=memory.handle(paletteHandle).state;
    const scene=new OriginalAnimationMemory(memory,{first,last,bounds:script.bounds,saveBackground});
    memory.lock(paletteHandle);
    for(const relative of [...marked].sort((a,b)=>a-b))scene.own(relative,loadShape(relative));
    memory.unlock(paletteHandle);memory.retain(paletteHandle);
    releaseTemporarySurface();scene.createSurface();
    if(saveBackground)scene.createBackup();
    // C74F composes the initial background before restoring palette flags.
    // Room callers may draw their child/objects into that composition.
    composeInitial(scene);
    memory.flags(paletteHandle,saved);return scene;
  }
  constructor(memory,{first,last,bounds,saveBackground=true}){
    if(!Number.isInteger(first)||!Number.isInteger(last)||first<1||last<first||last>255)throw new Error("Invalid animation shape range");
    if(bounds.length!==4||bounds.some(v=>!Number.isInteger(v)))throw new Error("Invalid original surface rectangle");
    const [top,left,bottom,right]=bounds;
    if(bottom<=top||right<=left)throw new Error("Empty original animation surface");
    this.memory=memory;this.first=first;this.last=last;this.bounds=[...bounds];this.saveBackground=saveBackground;
    this.objectBytes=2*(0x14e+last-first+1);this.object=memory.near.allocate(this.objectBytes);
    this.width=right-left;this.height=bottom-top;this.rowTable=0;this.surface=0;this.backup=0;
    this.images=new Map();this.disposed=false;
  }
  own(relative,handle){
    if(this.disposed||relative<this.first||relative>this.last||this.images.has(relative))throw new Error("Invalid animation image ownership");
    this.images.set(relative,handle);return handle;
  }
  createSurface(){
    if(this.disposed||this.surface)throw new Error("Animation surface already allocated or disposed");
    // VGA's alignment is one byte. The row table has one near word per row.
    this.rowTable=this.memory.near.allocate(2*this.height);
    this.surface=this.memory.allocateRaw(this.width*this.height);return this.surface;
  }
  createBackup(){
    if(this.disposed||!this.surface||!this.saveBackground||this.backup)throw new Error("Invalid background surface allocation");
    this.backup=this.memory.allocateRaw(this.width*this.height);return this.backup;
  }
  dispose(){
    if(this.disposed)throw new Error("Original animation was already disposed");
    for(const [relative,handle] of [...this.images].sort((a,b)=>a[0]-b[0]))this.memory.freeHandle(handle);
    this.memory.freeRaw(this.surface);if(this.rowTable)this.memory.near.free(this.rowTable);
    this.memory.freeRaw(this.backup);this.memory.near.free(this.object);this.disposed=true;
  }
}
