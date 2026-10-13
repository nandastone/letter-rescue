"use strict";
// Resident 7A66 source-cache ownership shared by shape and sound loading.
class OriginalResourceLoading {
  constructor(memory,catalogHandle,{observeWork=true,embeddedCatalog=false}={}){
    if(embeddedCatalog&&catalogHandle)throw new Error("Embedded catalog cannot own a heap handle");
    this.memory=memory;this.catalogHandle=catalogHandle;this.observeWork=observeWork;
    // Built-in FONT/CURS entries use a static catalog lock, not an allocation.
    this.embeddedCatalog=embeddedCatalog?{state:0}:null;
    this.sources=new Map();this.payloads=memory.resourcePayloads||(memory.resourcePayloads=new Map());this.operations=[];this.sourceWork=[];
    memory.resourceOwners??=new Map();
  }
  source(key,payload,directoryFlags){
    if(directoryFlags&~0xf0)throw new Error("Unreconstructed resource directory flags");
    if(this.embeddedCatalog&&!(directoryFlags&0x10))throw new Error("Static catalog requires embedded source bytes");
    const m=this.memory,catalog=this.embeddedCatalog||m.handle(this.catalogHandle),saved=catalog.state;catalog.state|=0x8000;
    let id=this.sources.get(key);const h=id?m.handle(id):{state:0,segment:0};
    const input={cachedHandle:id||0,state:h.state,segment:h.segment,directoryFlags};
    if(id&&!(h.state&0x200)&&((h.state&15)||h.segment)){
      const block=m.heap.at(16*h.segment+(h.state&15));input.blockSize=block.size;input.padding=block.padding;
    }
    if([input.cachedHandle,h.state,h.segment].some(v=>!Number.isInteger(v)||v<0||v>65535)||!Number.isInteger(directoryFlags)||directoryFlags<0||directoryFlags>255)throw new Error("Invalid original cache state");
    if(id&&(h.state&0x200))throw new Error("EMS cache entry is not reconstructed");
    const resident=!!(id&&((h.state&15)||h.segment));
    const action=resident?'cached':id?'reload':'load',promote=!id&&!!(directoryFlags&0x80),discardable=!id&&!!(directoryFlags&0x40);
    // Instruction accounting is an optional observer, never the source of
    // cache decisions. The semantic loader can run without any work modules.
    if(this.observeWork){const work=OriginalResourceWork.cache(input);this.sourceWork.push({key,input,...work,memoryWork:OriginalResourceWork.entryMemory(input)});}
    if(id)m.address(id);
    if(action==='cached'){catalog.state=saved;return id;}
    if(action==='reload'){if(!m.reallocate(id,payload.length))throw new Error("Cannot restore original source resource");this.operations.push({kind:'handle.reallocate',bytes:payload.length});}
    else{id=m.allocateHandle(payload.length);this.operations.push({kind:'handle.allocate',bytes:payload.length});}
    const state=m.handle(id).state;m.lock(id);
    // Resident 7AEF copies embedded bytes directly; file-backed sources read
    // the archive. Both paths retain an independent source allocation.
    this.payloads.set(id,Uint8Array.from(payload));
    this.operations.push({kind:directoryFlags&0x10?'resource.copy':'resource.read',bytes:payload.length});m.handle(id).state=state;
    m.handle(id).state|=0x1000;this.sources.set(key,id);
    m.resourceOwners.set(id,{cache:this.sources,key});
    // 7AC2 skips both directory-flag actions when reloading the same handle.
    // A newly promoted source is locked again by 7AD1 after EC54 restores flags.
    if(promote){m.promote(id);m.lock(id);}
    if(discardable)m.discardable(id);
    catalog.state=saved;return id;
  }
}
