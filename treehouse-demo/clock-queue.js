"use strict";
// DOSBox Pure db325ff PIC queue arithmetic. Event handlers and CPU instruction
// execution supply operations; queue ordering and float rounding live here.
class OriginalClockQueue {
  constructor({state,entries}){
    this.queue=entries.map(e=>({...e,index:Math.fround(e.index)}));
    this.ticks=state.ticks;this.servicing=!!state.servicing;this.serviceIndex=Math.fround(state.service_index);
    this.setCpuBudget(state);this.serviceIndexND=this.indexND();
  }
  setCpuBudget({cycles,left,maximum}){
    if([cycles,left,maximum].some(v=>!Number.isInteger(v)||v<-2147483648||v>2147483647)||maximum<=0)throw new Error("Invalid original CPU budget");
    this.cycles=cycles;this.left=left;this.maximum=maximum;
  }
  indexND(){return this.maximum-this.left-this.cycles;}
  index(){return Math.fround(Math.fround(this.indexND())/Math.fround(this.maximum));}
  add(handler,value,delay){
    if(!Number.isInteger(handler)||handler<=0||!Number.isInteger(value)||value<0||value>0xffffffff||!Number.isFinite(delay))throw new Error("Invalid original event");
    if(this.queue.length>=512)throw new Error("Original event queue is full");
    const index=Math.fround(Math.fround(delay)+(this.servicing?this.serviceIndex:this.index()));
    let at=0;while(at<this.queue.length&&this.queue[at].index<=index)at++;
    this.queue.splice(at,0,{handler,value,index});
    const cycles=Math.trunc(this.maximum*Math.fround(this.queue[0].index-this.index()));
    if(cycles<this.cycles){this.left+=this.cycles;this.cycles=0;}
  }
  remove(handler,value=null){this.queue=this.queue.filter(e=>e.handler!==handler||(value!==null&&e.value!==value));}
  start(){this.left+=this.cycles;this.cycles=0;this.serviceIndexND=this.indexND();return this.left>0;}
  service(handler,value,index){
    const first=this.queue[0];
    if(!this.servicing||!first||first.handler!==handler||first.value!==value||first.index!==index||Math.fround(first.index*Math.fround(this.maximum))>Math.fround(this.serviceIndexND))throw new Error("Original queue event is not due");
    this.queue.shift();this.serviceIndex=first.index;
  }
  finish(){
    let cycles=this.left;
    if(this.queue.length){
      cycles=Math.trunc(Math.fround(Math.fround(this.queue[0].index*Math.fround(this.maximum))-Math.fround(this.serviceIndexND)));
      if(!cycles)cycles=1;if(cycles>=this.left)cycles=this.left;
    }
    this.cycles=cycles;this.left-=cycles;
  }
  millisecond(){this.left=this.maximum;this.cycles=0;this.ticks++;for(const e of this.queue)e.index=Math.fround(e.index-1);}
  snapshot(){
    let hash=2166136261;const bytes=new ArrayBuffer(4),view=new DataView(bytes);
    for(const e of this.queue){
      view.setFloat32(0,e.index,true);
      for(const word of [e.handler,e.value,view.getUint32(0,true)])for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((word>>>shift)&255),16777619)>>>0;
    }
    const first=this.queue[0],index=this.index();
    return {cycles:this.cycles,left:this.left,maximum:this.maximum,ticks:this.ticks,count:this.queue.length,head_handler:first?.handler||0,head_value:first?.value||0,hash,head_index:first?.index||0,tick_index:index,milliseconds:this.ticks+index,servicing:Number(this.servicing),service_index:this.serviceIndex};
  }
  static pitDelay(counter){
    if(!Number.isInteger(counter)||counter<1||counter>65536)throw new Error("Invalid PIT counter");
    return Math.fround(1000/Math.fround(1193182/Math.fround(counter)));
  }
}
