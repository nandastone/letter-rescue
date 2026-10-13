"use strict";
// Pinned dual 8259 controller behavior for the VGA reference machine.
// CPU interrupt entry itself (register/stack writes) remains a caller operation.
class OriginalInterruptController {
  constructor(state){
    if(!Array.isArray(state.controllers)||state.controllers.length!==2)throw new Error("Invalid PIC pair");
    this.controllers=state.controllers.map(c=>({...c}));this.check=state.check;this.setCpu(state);
  }
  setCpu({cycles,left,interrupt_enabled,trap}){
    if([cycles,left].some(v=>!Number.isInteger(v)||v<-2147483648||v>2147483647)||![0,1].includes(interrupt_enabled)||![0,1].includes(trap))throw new Error("Invalid PIC CPU state");
    this.cycles=cycles;this.left=left;this.interrupt_enabled=interrupt_enabled;this.trap=trap;
  }
  activate(index){
    if(index===0){this.check=1;this.left+=this.cycles;this.cycles=0;}
    else this.raise(0,2);
  }
  deactivate(index){if(index===0)this.check=0;else this.lower(0,2);}
  checkPending(index){
    const c=this.controllers[index],pending=c.irr&c.imrr&c.isrr,limit=c.special?8:c.active;
    for(let i=0;i<limit;i++)if(pending&(1<<i)){this.activate(index);return;}
    this.deactivate(index);
  }
  raise(index,irq){
    const c=this.controllers[index],bit=1<<irq;
    if(!(c.irr&bit)){c.irr|=bit;if((bit&c.imrr&c.isrr)&&(c.special||irq<c.active))this.activate(index);}
  }
  lower(index,irq){
    const c=this.controllers[index],bit=1<<irq;
    if(c.irr&bit){c.irr&=~bit;if((bit&c.imrr&c.isrr)&&(c.special||irq<c.active))this.checkPending(index);}
  }
  start(index,irq){
    const c=this.controllers[index];c.irr&=~(1<<irq);
    if(!c.auto_eoi){c.active=irq;c.isr|=1<<irq;c.isrr=(~c.isr)&255;}
    else if(c.rotate)throw new Error("Original rotating auto EOI is unsupported");
  }
  mask(index,value){
    const c=this.controllers[index],change=c.imr^value;c.imr=value;c.imrr=(~value)&255;
    if(c.irr&change&c.isrr)this.checkPending(index);
  }
  afterEoi(index){
    const c=this.controllers[index];c.active=8;
    for(let i=0;i<8;i++)if(c.isr&(1<<i)){c.active=i;break;}
    if(c.irr&c.imrr&c.isrr)this.checkPending(index);
  }
  command(index,value){
    const c=this.controllers[index];
    if(value&0x10){
      if(value&0xec)throw new Error("Unsupported PIC initialization mode");
      this.mask(index,0);c.single=Number(!!(value&2));c.icw_index=1;c.icw_words=2+(value&1);
    }else if(value&8){
      if(value&4)throw new Error("Original PIC poll command is unsupported");
      if(value&2)c.request_isr=value&1;
      if(value&0x40){c.special=Number(!!(value&0x20));this.checkPending(index);}
    }else if(value&0x20){
      if(value&0x80)throw new Error("Original rotating EOI is unsupported");
      if(value&0x40){
        if(value<0x60||value>0x67)throw new Error("Invalid specific EOI");
        c.isr&=~(1<<(value-0x60));c.isrr=(~c.isr)&255;this.afterEoi(index);
      }else if(c.active!==8){c.isr&=~(1<<c.active);c.isrr=(~c.isr)&255;this.afterEoi(index);}
    }else if(!(value&0x40))c.rotate=Number(!!(value&0x80));
    // The pinned core logs and ignores OCW2 set-priority requests.
  }
  data(index,value){
    const c=this.controllers[index];
    if(c.icw_index===0){this.mask(index,value);return;}
    if(c.icw_index===1){c.vector=value&0xf8;if(c.icw_index++>=c.icw_words)c.icw_index=0;else if(c.single)c.icw_index=3;}
    else if(c.icw_index===2){if(c.icw_index++>=c.icw_words)c.icw_index=0;}
    else if(c.icw_index===3){
      if(!(value&1))throw new Error("Original 8085 PIC mode is unsupported");
      c.auto_eoi=Number(!!(value&2));if(c.icw_index++>=c.icw_words)c.icw_index=0;
    }else throw new Error("Invalid PIC initialization state");
  }
  run(){
    if(!this.interrupt_enabled||!this.check||this.trap)return -1;
    const master=this.controllers[0],pending=master.irr&master.imrr&master.isrr,limit=master.special?8:master.active;let vector=-1;
    for(let i=0;i<limit;i++)if(pending&(1<<i)){
      if(i===2){
        const slave=this.controllers[1],pendingSlave=slave.irr&slave.imrr&slave.isrr,slaveLimit=slave.special?8:slave.active;let irq=8;
        for(let j=0;j<slaveLimit;j++)if(pendingSlave&(1<<j)){irq=j;break;}
        if(irq===8)throw new Error("Cascade request has no eligible slave IRQ");
        this.start(1,irq);this.start(0,2);vector=slave.vector+irq;
      }else{this.start(0,i);vector=master.vector+i;}
      break;
    }
    this.check=0;if(vector>=0)this.interrupt_enabled=0;return vector;
  }
  apply(kind,arg=0,value=0){
    if(!Number.isInteger(arg)||!Number.isInteger(value)||value<0||value>255)throw new Error("Invalid PIC operation");
    if(kind<=3){
      if(arg<0||arg>15)throw new Error("Invalid IRQ number");
      const index=arg>7?1:0,irq=arg&7;
      if(kind===1){const before=this.cycles;this.raise(index,irq);if(before!==this.cycles){this.left-=2;this.cycles=2;}}
      else if(kind===2)this.lower(index,irq);
      else if(kind===3){const c=this.controllers[index],bit=1<<irq;this.mask(index,(c.imr&~bit)|(value?bit:0));}
      else throw new Error("Unknown PIC operation");
    }else if(kind===4){if(![0x20,0xa0].includes(arg))throw new Error("Invalid PIC command port");this.command(arg===0x20?0:1,value);}
    else if(kind===5){if(![0x21,0xa1].includes(arg))throw new Error("Invalid PIC data port");this.data(arg===0x21?0:1,value);}
    else if(kind===6)return this.run();
    else throw new Error("Unknown PIC operation");
    return -1;
  }
  snapshot(){return {cycles:this.cycles,left:this.left,check:this.check,interrupt_enabled:this.interrupt_enabled,trap:this.trap,controllers:this.controllers.map(c=>({...c}))};}
}
