"use strict";
// Resident 001C/003D/0590: the separate two-byte-header near heap supplies
// resource handles and C++ bookkeeping. Growth is explicit, never guessed.
class OriginalNearHeap {
  constructor({blocks,start,search,end,growth=null}){
    this.blocks=blocks.map(b=>({...b}));this.start=start;this.search=search;this.end=end;
    this.growth=growth;
    if(this.blocks[0]?.address!==start||this.blocks.at(-1)?.address!==end)throw new Error("Invalid near heap extent");
    for(let i=0;i<this.blocks.length-1;i++){
      const b=this.blocks[i];
      if(b.size<0||b.size%2||b.address+b.size+2!==this.blocks[i+1].address)throw new Error("Invalid near heap chain");
    }
    this.at(search);
  }
  at(address){const b=this.blocks.find(b=>b.address===address);if(!b)throw new Error(`Invalid near heap cursor ${address}`);return b;}
  resetSearch(){this.search=this.start;} // 6569..656C before allocating a handle slot.
  allocate(payload){
    if(!Number.isInteger(payload)||payload<0||payload>0xffe8)throw new Error("Unsupported near allocation size");
    const needed=(payload+1)&0xfffe,previous=this.search;
    for(const [start,limit] of [[previous,this.end],[this.start,previous-1]]){
      if(start>limit)continue;
      let block=this.at(start);
      for(let guard=0;guard<32768;guard++){
        if(block.free){
          const i=this.blocks.indexOf(block);
          while(block.size<needed&&this.blocks[i+1]?.free){
            block.size+=this.blocks[i+1].size+2;this.blocks.splice(i+1,1);
          }
          if(block.size>=needed){
            if(block.size!==needed)this.blocks.splice(i+1,0,{address:block.address+2+needed,size:block.size-needed-2,free:true});
            block.size=needed;block.free=false;this.search=block.address+2+needed;
            return block.address+2;
          }
        }
        if(block.address>=limit)break;
        block=this.at(block.address+block.size+2);
      }
    }
    this.search=this.start;
    if(this.growth&&this.grow(payload,this.growth))return this.allocate(payload);
    throw new Error("Near heap growth/reclamation is not yet reconstructed");
  }
  grow(payload,{limit,quantum}){
    if(!Number.isInteger(payload)||payload<0||payload>0xffe8||!Number.isInteger(limit)||limit<this.end+2||limit>65536||!Number.isInteger(quantum)||quantum<1||quantum>65535)throw new Error("Invalid near heap growth request");
    const needed=(payload+1)&0xfffe,last=this.blocks.at(-2),top=this.end+2;
    if(!last)throw new Error("Near heap has no block before its terminator");
    // Resident 060C grows from the last block. A free tail contributes its
    // payload; an allocated tail also needs a new two-byte allocation header.
    const minimum=top+needed-(last.free?last.size:-2);
    const unit=Math.max(16,2**Math.ceil(Math.log2(quantum)));
    let next=Math.ceil(minimum/unit)*unit;
    if(next>limit)next=Math.ceil(minimum/16)*16;
    if(next>limit||next<=top)return false;
    const terminal=this.blocks.at(-1);
    terminal.size=next-top-2;terminal.free=true;
    this.end=next-2;this.blocks.push({address:this.end,size:65534,free:false});
    this.search=last.address;return true;
  }
  free(pointer){
    if(pointer<=this.start)return;
    const block=this.at(pointer-2);
    if(block.address===this.end)throw new Error("Cannot free near heap terminator");
    block.free=true;this.search=Math.min(this.search,block.address);
  }
  snapshot(){return {blocks:this.blocks.map(b=>({...b})),start:this.start,search:this.search,end:this.end};}
}
