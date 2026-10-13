"use strict";
// Original resource memory ownership. Physical addresses are model state, not
// host pointers. Native memory/call recordings are only offline test fixtures.
class OriginalMemory {
  constructor({heap,near,arena=null,maximumParagraphs=null,dos=null}){
    this.arena=arena?{...arena}:null;
    const grow=arena?bytes=>dos?OriginalResourceStartup.growWithDOS(this.arena,bytes,dos):OriginalResourceStartup.growArena(this.arena,bytes,maximumParagraphs):null;
    this.heap=new OriginalHeap({...heap,closedArena:arena?arena.closed:true,grow});
    if(this.arena)this.arena.heap=this.heap;
    this.near=new OriginalNearHeap(near);
  }
  handle(id){const h=this.heap.handles.get(id);if(!h)throw new Error(`Unknown original handle ${id}`);return h;}
  claimRaw(block){block.flags=0x8000;return block.address+6;}
  claimHandle(block,id){
    block.flags=0xc000;block.handle=id;
    this.heap.handles.set(id,{id,state:(block.address&15)|0x1f0,segment:block.address>>>4});return id;
  }
  moveHandleTo(id,destination){
    const h=this.handle(id),source=this.heap.at((h.state&15)+16*h.segment);
    destination.flags=source.flags;destination.handle=id;destination.payload=source.payload;
    h.state=(h.state&0xfff0)|(destination.address&15);h.segment=destination.address>>>4;
    source.flags&=0x3fff;delete source.handle;delete source.payload;
  }
  resize(block,payload){
    const needed=this.heap.required(payload),flags=block.flags,grew=block.size<needed;
    if(block.size<needed){
      const previousPayload=block.size-6-block.padding;
      for(let guard=0;guard<100000;guard++){
        block.flags=0;this.heap.coalesce(block);block.flags=flags;
        if(block.size>=needed)break;
        const following=this.heap.next(block);
        if(following.flags===0xc000){
          block.flags=0x8000;const moved=this.heap.relocate(following);block.flags=flags;
          if(moved)continue;
        }
        // The closed arena cannot grow. Restore the original payload size,
        // releasing any holes already absorbed, before reporting failure.
        this.resize(block,previousPayload);return null;
      }
      if(block.size<needed)throw new Error("In-place growth failed to terminate");
    }
    // 712E takes the exact rounded-size branch without changing padding.
    if(grew||block.size!==needed){
      block.flags=0;this.heap.reserve(block,payload,false);block.flags=flags;
    }else this.heap.search=block.address;
    return block;
  }
  allocateRaw(payload){this.heap.prepare(payload);return this.claimRaw(this.heap.firstFit(payload));}
  available(){
    // Resident 5C78 requests the full conventional extent, exhausts unlocked
    // discardable cache entries, then packs to report the largest free span.
    // The maximal request cannot be satisfied before every eligible entry has
    // aged out, so no partial eviction order affects this operation's result.
    if(this.heap.grow)this.heap.grow(0xffffff);
    for(const h of this.heap.handles.values())if((h.state&0xc000)===0x4000)this.discard(h.id);
    for(const block of [...this.heap.blocks])if(block.flags===0&&this.heap.blocks.includes(block))this.heap.coalesce(block);
    return this.heap.pack(0xffffff);
  }
  allocateHandle(payload){this.near.resetSearch();const id=this.near.allocate(4);return this.claimHandle(this.heap.firstFit(payload),id);}
  resizeHandle(id,payload){
    // ED3E: try in place, then move an unlocked resident allocation. Unlike
    // reallocate, this preserves the old data and its handle slot.
    const pointer=this.address(id);
    if(!pointer)return this.reallocate(id,payload);
    if(this.resize(this.heap.at(pointer-6),payload))return true;
    const h=this.handle(id);if(h.state&0x8000)return false;
    h.state|=0x8000;let destination;
    try{destination=this.heap.firstFit(payload);}finally{h.state&=0x7fff;}
    this.moveHandleTo(id,destination);return true;
  }
  promote(id){
    if(!id)return id;const h=this.handle(id),saved=h.state;
    const pointer=this.lock(id);
    if(pointer){
      const source=this.heap.at(pointer-6),payload=source.size-6-source.padding;
      const available=this.heap.prepare(payload),destination=this.heap.at(this.heap.search);
      if(available>=payload&&destination.address<=source.address&&this.resize(destination,payload))this.moveHandleTo(id,destination);
    }
    this.flags(id,saved);return id;
  }
  reallocate(id,payload){
    if(!id||!this.discard(id))return false;
    const saved=this.handle(id).state;this.claimHandle(this.heap.firstFit(payload),id);
    this.handle(id).state|=saved&0xfdf0;return true;
  }
  address(id){
    if(!id)return 0;const h=this.handle(id);
    if(h.state&0x200)throw new Error("EMS handle materialization is not yet reconstructed");
    const address=(h.state&15)+16*h.segment;
    if(address)h.state|=0x1f0;return address?address+6:0;
  }
  lock(id){const address=this.address(id);if(address)this.handle(id).state|=0x81f0;return address;}
  unlock(id){if(id)this.handle(id).state&=0x7fff;}
  retain(id){if(id)this.handle(id).state&=0xbfff;return id;}
  keepResident(id){if(id)this.handle(id).state|=0x2000;return id;}
  discardable(id){if(id)this.handle(id).state|=0x4000;return id;}
  flags(id,flags){if(id){const h=this.handle(id);h.state=(h.state&0x1fff)|(flags&0xe000);}return id;}
  freeRaw(pointer){if(pointer){const b=this.heap.at(pointer-6);b.flags&=0x3fff;delete b.payload;}}
  detachHandle(id){
    // EBE0 transfers the allocation to raw ownership, retaining its bytes.
    const pointer=this.address(id);if(!pointer)return 0;
    const h=this.handle(id),block=this.heap.at(pointer-6);
    block.flags=(block.flags&0x3fff)|0x8000;delete block.handle;
    h.state&=0xdc00;h.segment=0;return pointer;
  }
  attachHandle(id,pointer){
    // EBA8 first releases the handle's old allocation, then adopts the raw
    // block. Unlike a new allocation, it does not reset the age bits.
    if(!this.discard(id))return false;
    if(!pointer)return false;
    const block=this.heap.at(pointer-6),h=this.handle(id);
    if((block.flags&0xc000)!==0x8000)throw new Error("Original handle adoption requires a raw allocation");
    block.flags=(block.flags&0x3fff)|0xc000;block.handle=id;
    h.state|=block.address&15;h.segment=block.address>>>4;return true;
  }
  discard(id){
    if(!id)return false;const h=this.handle(id);
    if(h.state&0x8000)return false;
    if(h.state&0x200)throw new Error("EMS handle release is not yet reconstructed");
    const address=(h.state&15)+16*h.segment;h.state&=0xdc00;h.segment=0;
    if(address){const b=this.heap.at(address);b.flags&=0x3fff;delete b.handle;delete b.payload;}
    this.resourcePayloads?.delete(id);
    return true;
  }
  freeHandle(id){if(id){
    // Resident 64CE removes a source resource's directory backlink before
    // releasing its handle. Discard alone deliberately keeps that backlink.
    const owner=this.resourceOwners?.get(id);
    if(owner){
      if(owner.cache.get(owner.key)===id)owner.cache.delete(owner.key);
      if(owner.entry?.handle===id)owner.entry.handle=0;
      this.resourceOwners.delete(id);
    }
    this.unlock(id);this.discard(id);this.heap.handles.delete(id);this.near.free(id);
  }}
}
