"use strict";
// Conventional first-fit allocation semantics for the pinned DOSBox platform.
// This models ownership and extents only; it does not execute DOS instructions.
class OriginalDOSMemory {
  constructor(blocks,owner=8){
    this.blocks=blocks.map(b=>({...b}));this.owner=owner;
    if(!this.blocks.length||this.blocks.at(-1).type!==0x5a)throw new Error("Invalid conventional DOS memory chain");
    for(let i=0;i<this.blocks.length;i++){
      const b=this.blocks[i];
      if(!Number.isInteger(b.segment)||!Number.isInteger(b.paragraphs)||b.paragraphs<0||b.segment+b.paragraphs>=0xa000||
        ![0x4d,0x5a].includes(b.type)||(i<this.blocks.length-1&&(b.type!==0x4d||b.segment+b.paragraphs+1!==this.blocks[i+1].segment)))throw new Error("Invalid conventional DOS memory block");
    }
  }
  static platform(){
    // DOS_SetupMemory, VGA conventional memory, reliable-addresses build.
    const start=0x16f,low=start+2,locked=low+5,free=locked+16;
    return new OriginalDOSMemory([
      {segment:start,paragraphs:1,owner:8,type:0x4d},
      {segment:low,paragraphs:4,owner:0,type:0x4d},
      {segment:locked,paragraphs:15,owner:0x40,type:0x4d},
      {segment:free,paragraphs:0x9ffe-free,owner:0,type:0x5a}
    ]);
  }
  static treehouse({dataSegmentRelative,environmentBytes=256}){
    if(!Number.isInteger(dataSegmentRelative)||dataSegmentRelative<0||dataSegmentRelative>0xffff||!Number.isInteger(environmentBytes)||environmentBytes<256)throw new Error("Invalid original process layout");
    const dos=this.platform(),environment=dos.allocate(Math.ceil(environmentBytes/16));
    if(!environment.ok)throw new Error("Cannot allocate original process environment");
    const probe=dos.allocate(65535);
    if(probe.ok)throw new Error("Unexpected conventional memory extent");
    const program=dos.allocate(probe.paragraphs);
    if(!program.ok)throw new Error("Cannot allocate original executable");
    const processSegment=program.segment,dataSegment=processSegment+16+dataSegmentRelative;
    dos.owner=processSegment;dos.block(processSegment).owner=processSegment;dos.block(environment.segment).owner=processSegment;
    // Runtime startup retains at most one 64 KiB data/near segment.
    if(!dos.resize(processSegment,16+dataSegmentRelative+0x1000).ok)throw new Error("Original executable exceeds conventional memory");
    return {dos,processSegment,dataSegment,environmentSegment:environment.segment};
  }
  block(segment){const b=this.blocks.find(b=>b.segment+1===segment);if(!b)throw new Error("Unknown DOS allocation");return b;}
  compress(){
    for(let i=0;i<this.blocks.length-1;){
      const a=this.blocks[i],b=this.blocks[i+1];
      if(!a.owner&&!b.owner){a.paragraphs+=b.paragraphs+1;a.type=b.type;this.blocks.splice(i+1,1);}
      else i++;
    }
  }
  request(paragraphs){if(!Number.isInteger(paragraphs)||paragraphs<0||paragraphs>65535)throw new Error("Invalid DOS paragraph request");}
  allocate(paragraphs){
    this.request(paragraphs);this.compress();let largest=0;
    for(let i=0;i<this.blocks.length;i++){
      const b=this.blocks[i];if(b.owner)continue;
      largest=Math.max(largest,b.paragraphs);if(b.paragraphs<paragraphs)continue;
      if(b.paragraphs>paragraphs){
        this.blocks.splice(i+1,0,{segment:b.segment+paragraphs+1,paragraphs:b.paragraphs-paragraphs-1,owner:0,type:b.type});
        b.paragraphs=paragraphs;b.type=0x4d;
      }
      b.owner=this.owner;return {ok:true,segment:b.segment+1,paragraphs};
    }
    return {ok:false,paragraphs:largest,error:8};
  }
  free(segment){
    const b=this.blocks.find(b=>b.segment+1===segment);
    if(!b||segment<0x170)return {ok:false,error:9};
    b.owner=0;return {ok:true};
  }
  resize(segment,paragraphs){
    this.request(paragraphs);this.compress();const b=this.blocks.find(b=>b.segment+1===segment);
    if(!b)return {ok:false,error:7};
    const index=this.blocks.indexOf(b);let total=b.paragraphs,type=b.type;
    if(paragraphs>total&&b.type!==0x5a&&this.blocks[index+1].owner===0){
      const next=this.blocks[index+1];total+=next.paragraphs+1;type=next.type;this.blocks.splice(index+1,1);
    }
    const actual=Math.min(paragraphs,total);b.paragraphs=actual;b.owner=this.owner;b.type=type;
    if(actual<total){
      this.blocks.splice(index+1,0,{segment:b.segment+actual+1,paragraphs:total-actual-1,owner:0,type});
      b.type=0x4d;this.compress();
    }
    return actual===paragraphs?{ok:true,paragraphs:actual}:{ok:false,paragraphs:actual,error:8};
  }
  snapshot(){return this.blocks.map(b=>({...b}));}
}
