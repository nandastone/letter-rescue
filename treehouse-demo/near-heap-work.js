"use strict";
// Resident 003D/0590: near allocation search and coalescing instruction work.
class OriginalNearHeapWork extends OriginalNearHeap {
  constructor(state){super(state);this.entries={};this.stringIterations=0;}
  add(list){for(const a of list)this.entries[a]=(this.entries[a]||0)+1;}
  allocate(payload){
    if(!Number.isInteger(payload)||payload<0||payload>0xffe8)throw new Error("Unsupported near allocation size");
    const needed=(payload+1)&0xfffe,previous=this.search;
    this.add([0x003d,0x003e,0x0040,0x0041,0x0042,0x0045,0x0048,0x004a,0x004d,
      0x0590,0x0591,0x0594,0x0595,0x0596,0x0599,0x059c,0x059e]);
    let address=previous,limit=this.end,second=false,alreadyRead=false,block;
    for(let guard=0;guard<65536;guard++){
      if(!alreadyRead){
        block=this.at(address);this.add([0x05c3,0x05c4,0x05c6]);this.stringIterations++;
      }
      alreadyRead=false;
      if(block.free){
        this.add([0x05c8]);
        for(;;){
          this.add([0x05ca,0x05cb,0x05cd]);
          if(block.size>=needed){
            this.add([0x05f2,0x05f3,0x05f6]);const index=this.blocks.indexOf(block);
            if(block.size!==needed){
              this.add([0x05f8,0x05fa,0x05fc,0x05fd,0x05ff]);
              this.blocks.splice(index+1,0,{address:block.address+needed+2,size:block.size-needed-2,free:true});
            }
            block.size=needed;block.free=false;this.search=block.address+2+needed;
            this.add([0x0601,0x0603,0x0606,0x0608,0x060a,0x060b,0x0050,0x0072,0x0073,0x0074,0x0075]);
            return block.address+2;
          }
          this.add([0x05cf,0x05d1,0x05d3,0x05d5,0x05d6,0x05d8]);this.stringIterations++;
          const index=this.blocks.indexOf(block),next=this.blocks[index+1];
          if(!next)throw new Error("Near allocation crosses its arena");
          if(!next.free){block=next;address=next.address;break;}
          this.add([0x05da,0x05dc,0x05df,0x05e1,0x05e4]);
          block.size+=next.size+2;this.blocks.splice(index+1,1);
        }
      }
      this.add([0x05b8,0x05bb,0x05bd]);
      if(block.address>=limit){
        this.add([0x05a0,0x05a2,0x05a3,0x05a5]);
        if(second)break;
        this.add([0x05a7,0x05a8,0x05ab,0x05ae,0x05b0]);
        if(previous===this.start)break;
        this.add([0x05b2,0x05b3,0x05b5]);address=this.start;limit=previous-1;second=true;
      }else{
        this.add([0x05bf,0x05c1]);address=block.address+block.size+2;
      }
    }
    this.search=this.start;throw new Error("Near allocation growth/reclamation work is not reconstructed");
  }
  work(){const instructions=Object.values(this.entries).reduce((a,b)=>a+b,0);return {entries:this.entries,instructions,stringIterations:this.stringIterations,cycles:instructions+this.stringIterations};}
}
