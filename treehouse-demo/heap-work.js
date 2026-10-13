"use strict";
// Instruction paths for the recovered closed-arena heap preparation. This
// counts actual block decisions, never elapsed durations from a recording.
class OriginalHeapWork extends OriginalHeap {
  constructor(state){super(state);this.entries={};this.stringIterations=0;this.repeats=[];}
  run(first,last=first){
    if(!OriginalHeapInstructionAddresses.includes(first)||!OriginalHeapInstructionAddresses.includes(last))throw new Error("Unknown heap instruction boundary");
    for(const address of OriginalHeapInstructionAddresses)if(address>=first&&address<=last)this.entries[address]=(this.entries[address]||0)+1;
  }
  coalesce(block){
    let index=this.blocks.indexOf(block);
    for(let j=index+1;;j++){
      this.run(0x6fd8,0x6fe9);
      const following=this.blocks[j];
      if(following.flags&0x8000)break;
      this.run(0x6feb);
      if(following.flags===0x4000)break;
      this.run(0x6fed,0x700e);
    }
    this.run(0x7010);return super.coalesce(block);
  }
  lastFit(payload){
    this.run(0x6ea3,0x6ec1);this.run(0x6ec7,0x6ee2);
    let block=this.at(this.search),found=null,needed=this.required(payload);
    for(;;){
      this.run(0x6ee4,0x6eed);
      if(block.flags&0x8000){this.run(0x6eef,0x6f07);block=this.next(block);continue;}
      this.run(0x6f09);
      if(block.flags===0x4000)break;
      this.run(0x6f0b);this.coalesce(block);this.run(0x6f0e,0x6f15);
      const a=block.size>>>4,b=needed>>>4;
      if(a<=b){this.run(0x6f17);if(a===b)this.run(0x6f19,0x6f1b);}
      if(block.size>=needed){found=block;this.run(0x6f1d,0x6f23);}
      this.run(0x6ef2,0x6f07);block=this.next(block);
    }
    this.run(0x6f25,0x6f28);
    if(!found){this.run(0x6f9f,0x6fa8);return null;}
    this.run(0x6f2a,0x6f3d);
    if((found.size&15)<(needed&15))this.run(0x6f3f,0x6f42);
    this.run(0x6f43,0x6f45);
    const remainder=found.size-needed;
    if(remainder<16)this.run(0x6f47,0x6f4a);
    if(remainder<6)this.run(0x6f4c,0x6f51);
    else this.run(0x6f53,0x6f72);
    this.run(0x6f75,0x6fa8);
    return this.reserve(found,payload,true);
  }
  firstFit(payload){
    const needed=this.required(payload);
    this.run(0x6d47,0x6d61);this.run(0x6d66,0x6d89);
    for(const start of [this.search,this.start]){
      this.run(0x6d8c);let block=this.at(start);
      for(;;){
        this.run(0x6d8e,0x6d97);
        if(block.flags&0x8000){
          this.scans++;this.run(0x6d99,0x6db1);block=this.next(block);continue;
        }
        this.run(0x6db3);
        if(block.flags===0x4000){this.run(0x6ddf,0x6de2);break;}
        this.scans++;this.run(0x6db5);this.coalesce(block);this.run(0x6db8,0x6dbf);
        if((block.size>>>4)<=(needed>>>4)){
          this.run(0x6dc1);if((block.size>>>4)===(needed>>>4))this.run(0x6dc3,0x6dc5);
        }
        if(block.size<needed){this.run(0x6d9c,0x6db1);block=this.next(block);continue;}
        this.run(0x6dc7,0x6dc9);
        if((block.size&15)<(needed&15))this.run(0x6dcb,0x6dce);
        this.run(0x6dcf,0x6dd1);const remainder=block.size-needed;
        if(remainder<16)this.run(0x6dd3,0x6dd6);
        if(remainder<6)this.run(0x6dd8,0x6ddd);else this.run(0x6ded,0x6dfb);
        this.run(0x6dfe,0x6e31);return this.reserve(block,payload,false);
      }
      if(start===this.search)this.run(0x6de4,0x6deb);
    }
    throw new Error("Original first-fit growth/eviction work is not reconstructed");
  }
  copyWork(from,to,bytes){
    const work=OriginalMemoryCopyWork.copy({from,to,bytes});
    for(const [address,count] of Object.entries(work.entries))this.entries[address]=(this.entries[address]||0)+count;
    this.stringIterations+=work.stringIterations;this.repeats.push(...work.repeats);
  }

  relocate(block){
    this.run(0x7011,0x701b);
    if(this.handles.get(block.handle).state&0x8000){this.run(0x7077,0x7078);return false;}
    this.run(0x701d,0x7025);this.run(0x6fa9,0x6fd7);this.run(0x7028,0x7035);
    const moved=super.relocate(block);
    this.run(0x7038);this.run(0x703d,0x7073);
    const move=this.moves.at(-1);this.copyWork(move.from+6,move.to+6,move.bytes);
    this.run(0x7076,0x7078);return moved;
  }
  prepare(payload){
    const needed=this.required(payload);let best=6,block=this.at(this.start);
    this.run(0x6b06,0x6b21);this.run(0x6b29,0x6b4d);
    const advance=()=>{this.run(0x6b5c,0x6b71);block=this.next(block);};
    const finish=()=>{this.run(0x6b82,0x6bb2);this.search=block.address;return best-6;};
    for(let budget=0;budget<100000;budget++){
      this.run(0x6b4f,0x6b58);
      if(block.flags&0x8000){
        this.run(0x6b5a);
        if(block.flags===0x8000){advance();continue;}
        this.run(0x6bb5,0x6bba);const moved=this.relocate(block);this.run(0x6bbd,0x6bbf);
        if(!moved){advance();continue;}
      }else{
        this.run(0x6b73);
        if(block.flags===0x4000)throw new Error("Arena growth instruction path is not yet reconstructed");
      }
      // 6C13 loops directly to coalescing, without rereading the header.
      for(;;){
        this.run(0x6bc1);this.coalesce(block);this.run(0x6bc4,0x6bc9);
        const a=block.size>>>4,b=best>>>4;
        if(a<=b){this.run(0x6bcb);if(a===b)this.run(0x6bcd,0x6bd0);}
        if(block.size>best){
          best=block.size;this.run(0x6bd2,0x6bdb);
          const target=needed>>>4;
          if(a>target)return finish();
          this.run(0x6bdd);
          if(a===target){this.run(0x6bdf,0x6be2);if(block.size>=needed)return finish();}
        }
        this.run(0x6be4,0x6be6);const following=this.next(block);
        if(following.flags===0x4000)throw new Error("Arena growth instruction path is not yet reconstructed");
        this.run(0x6be8);
        if(following.flags===0xc000){
          this.run(0x6bea,0x6c05);block.flags=0x8000;
          const moved=this.relocate(following);block.flags=0;this.run(0x6c08,0x6c13);
          if(moved)continue;
        }
        this.run(0x6c15);advance();break;
      }
    }
    throw new Error("Heap instruction model failed to terminate");
  }
  work(){const instructions=Object.values(this.entries).reduce((a,b)=>a+b,0);return {entries:this.entries,instructions,stringIterations:this.stringIterations,cycles:instructions+this.stringIterations,repeats:this.repeats};}
}
