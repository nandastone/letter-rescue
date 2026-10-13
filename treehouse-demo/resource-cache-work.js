"use strict";
// Compose resident instruction work for cache hits and successful cold loads.
// CPU/PIC scheduling and DOS/BIOS execution are separate components.
class OriginalResourceCacheWork {
  static combine(parts){
    const entries={};let cycles=0;
    for(const part of parts){
      for(const [at,n] of Object.entries(part.entries))entries[at]=(entries[at]||0)+n;
      cycles+=part.cycles;
    }
    return {entries,instructions:Object.values(entries).reduce((a,b)=>a+b,0),cycles};
  }
  static cold(input,{allocation,nearWork,farWork,resource,catalogs,selected,catalogStates}){
    const cache=OriginalResourceWork.cache(input);
    if(cache.action!=='load'||cache.promote)throw new Error("Cold composition requires a new source without promotion");
    if(resource.directoryFlags&0x10)throw new Error("Memory-backed resource copy composition is not reconstructed");
    const allocated=OriginalMemoryWrapperWork.allocateHandle(allocation),lock=OriginalMemoryWrapperWork.lock(allocated);
    const read=OriginalResourceWork.read(resource),open=OriginalResourceWork.open({catalogs,selected});
    const parts=[cache,allocated,nearWork,farWork,OriginalMemoryWrapperWork.farAllocation(),lock,lock.addressWork,read,open];
    if(selected!==0x2055)for(const file of catalogs){
      const state=catalogStates.find(h=>h.handle===file.handle);
      if(!state)throw new Error("Missing source catalog handle state");
      parts.push(OriginalResourceWork.handleAddress(state));
    }
    if(cache.discardable)parts.push(OriginalMemoryWrapperWork.discardable({handle:allocated.handle,state:allocated.state|0x1000}));
    return {...this.combine(parts),handle:allocated.handle,reads:read.reads,catalogs:open.catalogs};
  }
  static resident(input){
    const cache=OriginalResourceWork.cache(input);
    if(cache.action!=='cached')throw new Error("Cold resource execution needs allocation and I/O composition");
    const query=OriginalResourceWork.entryMemory(input),entries={...cache.entries};
    // cache() already includes the intrinsic 7A30 body. Add its callees once.
    for(const [address,count] of Object.entries(query.entries)){
      const at=Number(address);if(at<0x7a30||at>=0x7a66)entries[address]=(entries[address]||0)+count;
    }
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,handle:input.cachedHandle,address:query.address,bytes:query.bytes};
  }
}
