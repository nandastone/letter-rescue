"use strict";
// Resident 7688 owns an independent raw copy. Loading a script this way does
// not populate the source cache; the caller releases the raw allocation.
class OriginalDirectLoading {
  constructor(memory,{observeWork=true}={}){this.memory=memory;this.observeWork=observeWork;this.operations=[];this.work=[];}
  load({payload,catalogHandle,cachedHandle=0}){
    const m=this.memory,catalog=m.handle(catalogHandle),saved=catalog.state;
    catalog.state|=0x8000;
    const h=cachedHandle?m.handle(cachedHandle):{state:0,segment:0},input={cachedHandle,state:h.state,segment:h.segment};
    if(cachedHandle&&!(h.state&0x200)&&((h.state&15)||h.segment)){
      const block=m.heap.at(16*h.segment+(h.state&15));input.blockSize=block.size;input.padding=block.padding;
    }
    const entryMemory=this.observeWork?OriginalResourceWork.entryMemory(input):null;
    const source=cachedHandle?m.address(cachedHandle):0;
    const bytes=source?(()=>{const block=m.heap.at(source-6);return block.size-6-block.padding;})():payload.length;
    catalog.state=saved;
    // The catalog is pinned separately during entry inspection and allocation.
    catalog.state|=0x8000;const pointer=m.allocateRaw(bytes);catalog.state=saved;
    this.operations.push({kind:'raw.allocate',bytes},{kind:source?'resource.copy':'resource.read',bytes});
    if(this.observeWork)this.work.push({...OriginalResourceWork.direct({cached:!!source}),entryMemory});
    return pointer;
  }
  release(pointer){this.memory.freeRaw(pointer);this.operations.push({kind:'raw.free'});}
}
