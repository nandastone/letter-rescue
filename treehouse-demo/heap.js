"use strict";
// Recovered conventional-memory block/handle operations (resident 6B06, 6EA3,
// 6D47, 6FD8 and 7011). The browser's resource lifetime layer must drive these
// operations before this model can supply allocation work to its game clock.
class OriginalHeap {
  constructor({blocks,handles,search,closedArena,grow=null}) {
    if(closedArena!==true&&typeof grow!=='function')throw new Error("Original arena growth requires an explicit platform provider");
    if(grow!==null&&typeof grow!=='function')throw new Error("Invalid original arena growth provider");
    this.grow=grow;
    this.blocks=blocks.map(b=>({...b}));this.handles=new Map(handles.map(h=>[h.id,{...h}]));
    this.start=this.blocks[0]?.address;this.search=search;this.moves=[];this.scans=0;this.merges=0;
    for(let i=0;i<this.blocks.length;i++){
      const b=this.blocks[i];
      if(!Number.isInteger(b.address)||!Number.isInteger(b.size)||b.size<6||b.size%2||
        (i&&this.blocks[i-1].address+this.blocks[i-1].size!==b.address))throw new Error("Invalid original heap block chain");
      if(![0,0x4000,0x8000,0xc000].includes(b.flags))throw new Error("Unsupported original heap block flags");
      if(b.flags===0xc000&&!this.handles.has(b.handle))throw new Error("Missing original heap handle");
    }
    if(this.blocks.at(-1)?.flags!==0x4000||this.blocks.slice(0,-1).some(b=>b.flags===0x4000))throw new Error("Invalid original heap terminator");
    this.at(search);
  }
  at(address){const block=this.blocks.find(b=>b.address===address);if(!block)throw new Error(`Heap cursor is not a block: ${address}`);return block;}
  next(block){return this.at(block.address+block.size);}
  required(payload){if(!Number.isInteger(payload)||payload<0||payload>0xffff8)throw new Error("Invalid original allocation size");return (payload+7)&~1;}
  searchSize(payload){
    if(!Number.isInteger(payload)||payload<0||payload>0xffffffff)throw new Error("Invalid original memory search size");
    return Math.min(0xfffff,Math.floor((payload+7)/2)*2);
  }
  coalesce(block){
    if(block.flags!==0)throw new Error("Only free blocks can coalesce");
    let index=this.blocks.indexOf(block);
    while(this.blocks[index+1].flags===0){block.size+=this.blocks[index+1].size;this.blocks.splice(index+1,1);this.merges++;}
    return block;
  }
  reserve(block,payload,tail){
    const needed=this.required(payload),remainder=block.size-needed;
    if(remainder<0||block.flags!==0)throw new Error("Heap allocation exceeds free block");
    if(remainder>=6){
      const index=this.blocks.indexOf(block);
      if(tail){
        block.size=remainder;block.padding=0; // 6F55 replaces the whole header word.
        block={address:block.address+remainder,size:needed,flags:0,padding:0};
        this.blocks.splice(index+1,0,block);
      }else{
        this.blocks.splice(index+1,0,{address:block.address+needed,size:remainder,flags:0,padding:0});block.size=needed;
      }
    }
    block.padding=block.size-payload-6;this.search=block.address;return block;
  }
  lastFit(payload){
    let block=this.at(this.search),found=null;
    while(block.flags!==0x4000){
      this.scans++;
      if(block.flags===0){this.coalesce(block);if(block.size>=this.required(payload))found=block;}
      block=this.next(block);
    }
    return found?this.reserve(found,payload,true):null;
  }
  firstFit(payload){
    // 6D47 tries from the remembered block, then wraps to the heap start.
    const find=()=>{
      for(const start of [this.search,this.start]){
        let block=this.at(start);
        while(block.flags!==0x4000){
          this.scans++;
          if(block.flags===0){this.coalesce(block);if(block.size>=this.required(payload))return this.reserve(block,payload,false);}
          block=this.next(block);
        }
      }
      return null;
    };
    const found=find();if(found)return found;
    // 6D47 first tries 6652 packing with the rounded allocation size.
    // Growth/cache eviction are reached only if this packing attempt fails.
    if(this.pack(this.required(payload))>=this.required(payload)){
      const packed=find();if(packed)return packed;
    }
    if(this.grow&&this.grow(this.required(payload))>=this.required(payload)){
      const grown=find();if(grown)return grown;
    }
    throw new Error("Original heap pressure requires the unimplemented growth/eviction path");
  }
  relocate(block){
    const handle=this.handles.get(block.handle);
    if(!handle)throw new Error("Cannot move a block without its handle");
    if(handle.state&0x8000)return false;
    const payload=block.size-6-block.padding,oldState=handle.state;
    handle.state|=0x8000;this.search=block.address;
    const destination=this.lastFit(payload)||this.firstFit(payload);
    handle.state=(oldState&0xfff0)|(destination.address&15);handle.segment=destination.address>>>4;
    destination.flags=block.flags;destination.handle=block.handle;destination.payload=block.payload;
    this.moves.push({handle:block.handle,from:block.address,to:destination.address,bytes:payload});
    block.flags=0;delete block.handle;delete block.payload;return true;
  }
  prepare(payload){
    const needed=this.searchSize(payload);let best=6,block=this.at(this.start);
    for(let budget=0;budget<100000;budget++){
      this.scans++;
      if(block.flags===0x4000){this.search=block.address;return best-6;}
      if(block.flags===0x8000){block=this.next(block);continue;}
      if(block.flags===0xc000&&!this.relocate(block)){block=this.next(block);continue;}
      this.coalesce(block);best=Math.max(best,block.size);
      if(block.size>=needed){this.search=block.address;return best-6;}
      const following=this.next(block);
      if(following.flags===0x4000){this.search=block.address;return best-6;}
      if(following.flags===0xc000){
        // Protect the current hole while moving its following handle. It
        // cannot become a destination until the temporary raw-block bit clears.
        block.flags=0x8000;const moved=this.relocate(following);block.flags=0;
        if(moved)continue;
      }
      block=this.next(block);
    }
    throw new Error("Original heap preparation failed to terminate");
  }
  pack(payload){
    // Resident 6652 packs unlocked handles into preceding holes. Unlike
    // 6B06's relocation strategy, overlapping moves preserve each block's
    // size/padding and move the hole forward. This is allocator state only.
    const needed=this.searchSize(payload);let best=6,block=this.at(this.start);
    for(let guard=0;guard<100000;guard++){
      this.scans++;
      if(block.flags===0x4000){this.search=block.address;return best-6;}
      if(block.flags!==0){block=this.next(block);continue;}
      this.coalesce(block);best=Math.max(best,block.size);
      if(block.size>=needed){this.search=block.address;return best-6;}
      const following=this.next(block);
      if(following.flags===0x4000){this.search=block.address;return best-6;}
      if(following.flags!==0xc000||this.handles.get(following.handle).state&0x8000){block=following;continue;}
      const index=this.blocks.indexOf(block),from=following.address,to=block.address;
      const hole={address:to+following.size,size:block.size,flags:0,padding:0};
      following.address=to;
      const handle=this.handles.get(following.handle);
      handle.state=(handle.state&0xfff0)|(to&15);handle.segment=to>>>4;
      this.blocks.splice(index,2,following,hole);
      this.moves.push({handle:following.handle,from,to,bytes:following.size});
      block=hole;
    }
    throw new Error("Original heap packing failed to terminate");
  }
  snapshot(){return {blocks:this.blocks.map(b=>({...b})),handles:[...this.handles.values()].sort((a,b)=>a.id-b.id),search:this.search};}
}
