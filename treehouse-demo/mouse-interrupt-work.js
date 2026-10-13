"use strict";
// IRQ12 BIOS stubs and resident 88CA movement callback. Current mouse input
// state selects the path; the callback composes the existing indexed renderer.
class OriginalMouseInterruptWork {
  constructor({memory,ds,ss=ds,residentSegment,graphics,state,entry}){
    this.memory=memory;this.ds=ds;this.ss=ss;this.base=16*ds;this.residentBase=16*residentSegment;
    this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);this.graphics=graphics;this.state=state;this.entry=entry;
  }
  word(at){return this.view.getUint16(at,true);}
  put(at,value){this.view.setUint16(at,value&65535,true);}
  static *resident(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  static *physical(base,...offsets){for(const a of offsets)yield 'physical:'+(base+a).toString(16);}
  *movement({type,x,y}){
    const emit=OriginalMouseInterruptWork.resident,guard=this.residentBase+0x894c;
    yield* emit(0x88ca,0x88cb,0x88cc,0x88cd,0x88d3);
    if(!this.memory[guard]){
      yield* emit(0x88d5);this.memory[guard]=1;yield* emit(0x88db,0x88dd);
      if(type&1){
        yield* emit(0x88df,0x88e2,0x88e4,0x88ea);
        if(this.word(this.base+0x206c)===320){yield* emit(0x88ec);x=((x<<16)>>17)&65535;}
        yield* emit(0x88ee,0x88f2);let changed=x!==this.word(this.base+0x2066);
        if(!changed){yield* emit(0x88f4,0x88f8);changed=y!==this.word(this.base+0x2064);}
        if(changed){
          yield* emit(0x88fa);this.put(this.base+0x2066,x);yield* emit(0x88fe);this.put(this.base+0x2064,y);
          yield* emit(0x8902,0x8907);const count=this.view.getInt16(this.base+0x2062,true);
          if(count>=0){
            yield* emit(0x8909);
            if(count>0){yield* emit(0x894d);this.put(this.base+0x2100,1);yield* emit(0x8953);}
            else{
              yield* emit(0x890b);this.put(this.base+0x2102,this.word(this.base+0x2102)+1);yield* emit(0x890f);
              if(!this.word(this.base+0x2102)){
                yield* emit(0x8911,0x8912,0x8913,0x8914,0x8915,0x8916,0x8918,0x891a,0x891c);
                if(this.ss!==this.ds)throw new Error('Mouse callback alternate stack requires composition');
                yield* emit(0x8923,0x8924,0x8929,0x892b,0x892c,0x892d);yield* this.graphics.cursor('hide');
                yield* emit(0x8930,0x8931);yield* this.graphics.cursor('restore');
                yield* emit(0x8934,0x8935);yield {call:'stack-segment-credit'};yield* emit(0x8937,0x8939,0x893a,0x893b,0x893c,0x893d);
              }
              yield* emit(0x893e);this.put(this.base+0x2102,this.word(this.base+0x2102)-1);
            }
          }
        }
      }
    }
    yield* emit(0x8942);this.memory[guard]=0;yield* emit(0x8948,0x8949,0x894a,0x894b);
  }
  *run(){
    const emit=OriginalMouseInterruptWork.physical,s=this.state;
    yield* emit(this.entry,0);yield {call:'interrupt-flags',enabled:true};yield* emit(this.entry,1,2,3,5);
    yield {call:'mouse-irq'};let event=null;
    if(s.events.length&&!s.inUser){
      event=s.events.pop();
      if(s.allowRealMode&&!s.hidden&&!s.inhibitDraw)throw new Error('Visible BIOS cursor requires composition');
      if(!(s.mask&event.type)||!s.allowRealMode)event=null;
      if(!event&&s.ps2)throw new Error('PS/2 mouse callback requires composition');
    }
    if(event){
      s.inUser=true;
      yield* emit(this.entry,9,10,12);yield {call:'port-write',port:0xa0,value:32};
      yield* emit(this.entry,14);yield {call:'port-write',port:0x20,value:32};yield* emit(this.entry,16,17,18);
      if(s.callback!==this.residentBase+0x88ca)throw new Error('Unsupported mouse user callback');
      yield* this.movement({type:event.type,x:s.x,y:s.y});
      yield* emit(s.userReturn,0);yield {call:'interrupt-flags',enabled:false};yield* emit(s.userReturn,1);s.inUser=false;yield {call:'mouse-user-return'};yield* emit(s.userReturn,5);
    }else{
      yield* emit(s.returnAddress,0);yield {call:'interrupt-flags',enabled:false};yield* emit(s.returnAddress,1,3);yield {call:'port-write',port:0xa0,value:32};
      yield* emit(s.returnAddress,5);yield {call:'port-write',port:0x20,value:32};
    }
    yield* emit(s.returnAddress,7);yield {call:'mouse-return'};
    if(s.events.length&&!s.timerInProgress){s.timerInProgress=true;yield {call:'mouse-limit-event'};}
    yield* emit(s.returnAddress,11,13,14,15);
  }
}
