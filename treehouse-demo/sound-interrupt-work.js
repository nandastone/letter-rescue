"use strict";
// Sound driver's IRQ handler 4D3C. Port operations are explicit device actions;
// DMA/DSP state and PIC event delivery belong to the hardware execution host.
class OriginalSoundInterruptWork {
  constructor({memory,ds,ss=ds,residentSegment,soundSegment}){this.memory=memory;this.ds=ds;this.ss=ss;this.residentSegment=residentSegment;this.soundSegment=soundSegment;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);}
  static *instructions(...addresses){for(const a of addresses)yield 'sound:'+a.toString(16);}
  word(at){return this.view.getUint16(at,true);}
  put(at,n){this.view.setUint16(at,n&65535,true);}
  far(at){return this.word(at)+16*this.word(at+2);}
  static *resident(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  *installVector(irq){
    const emit=OriginalSoundInterruptWork.instructions;if(irq>=8)throw new Error('Unsupported sound IRQ vector');
    yield* emit(0x4cc2);const saved=yield {call:'read-interrupt-flag'};
    yield* emit(0x4cc3,0x4cc4,0x4cc5,0x4cc6);yield {call:'interrupt-flags',enabled:false};
    yield* emit(0x4cc7,0x4cc9,0x4cca,0x4ccc,0x4cce,0x4cd0,0x4cd1,0x4cd3,0x4cd5,0x4cd8);
    const at=4*(irq+8);this.put(this.base+0x21ed,this.word(at));yield* emit(0x4cda);this.put(at,0x4d3c);
    yield* emit(0x4cdd,0x4ce1);this.put(this.base+0x21ef,this.word(at+2));yield* emit(0x4ce4);this.put(at+2,this.soundSegment);
    yield* emit(0x4ce8,0x4ce9,0x4cea,0x4ceb,0x4cec);yield {call:'interrupt-flags',enabled:saved};yield* emit(0x4ced);
  }
  *play({segment,offset,length,rate}){
    const emit=OriginalSoundInterruptWork.instructions;
    yield* emit(0x4e9f,0x4ea0,0x4ea2,0x4ea3,0x4ea4,0x4ea5,0x4ea6,0x4ea9,0x4eab,0x4ead,0x4eb2);
    if(this.word(this.base+0x21eb)){yield* emit(0x4eb4,0x4eb7);}
    else{
      yield* emit(0x4eba);this.put(this.base+0x21eb,1);
      yield* emit(0x4ec0,0x4ec4,0x4ec7,0x4eca,0x4ecd,0x4ed0);
      if(!rate||Math.floor(1000000/rate)>65535)throw new Error('Sound rate divide error');
      const constant=(-Math.floor(1000000/rate))&255;
      yield* emit(0x4ed2,0x4ed4,0x4ed6,0x4eda,0x4edd,0x4edf);yield* this.writeDsp(0x40,this.port(12));
      yield* emit(0x4ee2,0x4ee4);yield* this.writeDsp(constant,this.port(12));
      yield* emit(0x4ee7,0x4eea,0x4eed,0x4ef0);const irq=this.memory[this.base+0x21ea];yield* this.installVector(irq);
      yield* emit(0x4ef3,0x4ef7,0x4ef9,0x4efb,0x4efd);const mask=yield {call:'port-read',port:0x21};
      yield* emit(0x4eff,0x4f01);yield {call:'port-write',port:0x21,value:mask&~(1<<irq)};
      yield* emit(0x4f03,0x4f06,0x4f09,0x4cae,0x4caf,0x4cb1,0x4cb3,0x4cb5,0x4cb8,0x4cbb,0x4cbd,0x4cc0,0x4cc1);
      const address=16*segment+offset,last=address+length-1;
      yield* emit(0x4f0c);this.memory[this.base+0x21fd]=address>>>16;yield* emit(0x4f10);this.put(this.base+0x21fe,address);
      yield* emit(0x4f13,0x4f16);this.put(this.base+0x2203,length);yield* emit(0x4f1a);this.put(this.base+0x2205,0);
      yield* emit(0x4f20,0x4f23,0x4f26,0x4f29,0x4f2c);this.put(this.base+0x2207,last);
      yield* emit(0x4f2f,0x4f33);this.memory[this.base+0x2202]=(last>>>16)-(address>>>16);
      yield* emit(0x4f37);yield* this.nextBlock();yield* emit(0x4f3a);
    }yield* emit(0x4f3c,0x4f3d,0x4f3e,0x4f3f,0x4f40,0x4f41);
  }
  *dispatch(command,args){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4334,0x4335,0x4337);
    if(command<=7){yield* emit(0x433b,0x433d,0x4341,0x4343);
      if(command===5||command===6)yield* emit(0x43dd);
      else if(command===3){
        yield* emit(0x43be,0x43bf,0x43c0,0x4f42,0x4f43,0x4f44,0x4f45,0x4f46,0x4f49,0x4f4b,0x4f4d,0x4f50,0x4f55);
        if(this.word(this.base+0x21eb)){
          yield* emit(0x4f57);yield* this.pause();yield* emit(0x4f5a);yield* this.stop();yield* emit(0x4f5d);
        }
        yield* emit(0x4f5f,0x4f60,0x4f61,0x4f62,0x4f63,0x43c3);
      }
      else if(command===7){
        yield* emit(0x43e0);this.put(this.base+0x48f8,0xc559);yield* emit(0x43e4);this.put(this.base+0x48fa,this.residentSegment);
        yield* emit(0x43e8,0x43e9,0x43ea,0x43eb,0x43ec,0x43ed,0x43ee);yield* this.play(args);yield* emit(0x43f1,0x43f4);
      }else throw new Error('Sound dispatcher command requires composition');
    }yield* emit(0x4339,0x433a);
  }
  *notifyCompletion(){
    const emit=OriginalSoundInterruptWork.resident;
    yield* emit(0xc66f,0xc670,0xc671,0xc672,0xc675,0xc677,0xc67a,0xc67d);
    const callback=this.far(this.base+0x2124);
    if(callback){
      if(callback!==16*this.residentSegment+0xe54c)throw new Error('Unsupported sound completion callback');
      yield* emit(0xc67f,0xc681,0xc683,0xc685);
      if(this.ss!==this.ds)throw new Error('Sound callback alternate stack requires composition');
      yield* emit(0xc68c,0xc68f,0xc690,0xc691,0xc692,0xe54c,0xe54d,0xe54f,0xe552,0xe555,0xe556,0xe557,0xedd0,0xedd1,0xedd3,0xedd6,0xedd8,0xedda);
      const source=this.far(this.base+0x2120);let handle=0;
      if(source){yield* emit(0xeddc,0xedde,0xede4);if(this.word(source-6)>=0xc000){yield* emit(0xede6);handle=this.word(source-2);}}
      yield* emit(0xedea,0xedeb,0xe55a,0xe55b,0xe55c,0xe55d,0x65d0,0x65d1,0x65d3,0x65d6,0x65d8);
      if(handle){yield* emit(0x65da);this.put(this.base+handle,this.word(this.base+handle)&0x7fff);}
      yield* emit(0x65df,0x65e0,0x65e1,0xe560,0xe562,0xe563,0xc695);yield {call:'stack-segment-credit'};
      yield* emit(0xc697);
    }yield* emit(0xc699,0xc69a,0xc69b,0xc69c);
  }
  *completion(){
    const emit=OriginalSoundInterruptWork.resident;
    yield* emit(0xc559,0xc55a,0xc55b,0xc55c,0xc55d,0xc55e,0xc55f,0xc560,0xc561,0xc562,0xc565,0xc567,0xc569,0xc56b,0xc56d);
    if(this.ss!==this.ds)throw new Error('Sound IRQ alternate stack requires composition');
    yield* emit(0xc574,0xc575,0xc576,0xc57a,0xc57c);
    const segment=this.word(this.base+0x2122),offset=this.word(this.base+0x2120),source=16*segment+offset;
    this.put(this.base+0x21db,segment);yield* emit(0xc57f);this.put(this.base+0x21dd,offset);
    yield* emit(0xc583,0xc585,0xc589);let loop=false,start=0,length=0;
    if(this.memory[source]&128){yield* emit(0xc58b,0xc58f);
      if(this.word(this.base+0x212c)){yield* emit(0xc591,0xc595);const state=this.view.getInt16(this.base+0x211e,true);
        if(!state){
          yield* emit(0xc5ad,0xc5b1);const end=this.word(source+8);this.put(this.base+0x21d9,end);yield* emit(0xc5b4);length=end;
          if(!end){yield* emit(0xc5b6,0xc5ba);length=this.word(source+4);this.put(this.base+0x21d5,length);}
          yield* emit(0xc5bd,0xc5be,0xc5c2);start=this.word(source+6);this.put(this.base+0x21d7,start);yield* emit(0xc5c5);length=(length-start)&65535;loop=true;
        }else{
          yield* emit(0xc597);
          if(state<0){yield* emit(0xc599,0xc59d);start=this.word(source+8);
            if(start){yield* emit(0xc59f,0xc5a3,0xc5a5);length=(this.word(source+4)-start)&65535;
              if(length){yield* emit(0xc5a7);this.put(this.base+0x211e,-state);yield* emit(0xc5ab);loop=true;}
            }
          }
        }
      }
    }
    if(this.far(this.base+0x2128)!==16*this.soundSegment+0x4334)throw new Error('Unsupported sound driver dispatcher');
    if(loop){
      yield* emit(0xc5c7,0xc5cb,0xc5cd,0xc5d0,0xc5d3,0xc5d6,0xc5d8);const at=(offset+start+10)&65535,rate=this.word(source+1);this.put(this.base+0x21df,at);
      yield* emit(0xc5dc);this.put(this.base+0x21e1,rate);yield* emit(0xc5e0);this.put(this.base+0x21e3,1);
      yield* emit(0xc5e6);yield* this.dispatch(7,{segment,offset:at,length,rate});yield* emit(0xc5ea);
    }else{
      yield* emit(0xc5ec,0xc5f0,0xc5f4,0xc5f6);yield* this.dispatch(6);yield* emit(0xc5fa,0xc5fc,0xc5ff);this.put(this.base+0x211c,0);
      yield* emit(0xc601);yield* this.notifyCompletion();
    }
    yield* emit(0xc604,0xc605);yield {call:'stack-segment-credit'};yield* emit(0xc606,0xc608,0xc609,0xc60a,0xc60b,0xc60c,0xc60d,0xc60e,0xc60f,0xc610);
  }
  *devicePost(){
    const emit=OriginalSoundInterruptWork.instructions;
    if(this.far(0x15*4)!==16*this.soundSegment+0x4415)throw new Error('Unsupported INT15 hook');
    yield* emit(0x4415,0x4416,0x4417,0x441a,0x441c,0x441f,0x4421,0x4422,0x4423);
    if(this.far(this.base+0x48f8)!==16*this.residentSegment+0xc559)throw new Error('Unsupported sound IRQ callback');
    yield* this.completion();yield* emit(0x4427,0x4428,0x4429);
    const bios=this.far(this.base+0x48fc);if(bios!==0xf11a0)throw new Error('Unsupported BIOS INT15 stub');
    yield 'physical:'+bios.toString(16);yield {call:'bios-device-post',ax:0x91f0};yield 'physical:'+(bios+4).toString(16);
    yield* emit(0x442d,0x442e,0x442f);
  }
  port(offset){const base=this.word(this.base+0x21e8);return (base&0xff00)|((base+offset)&255);}
  *pause(){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4c62);const saved=yield {call:'read-interrupt-flag'};
    yield* emit(0x4c63,0x4c65,0x4c67,0x4c6b);const port=this.port(12);
    let finished=false;
    for(let guard=0;guard<65536;guard++){
      yield* emit(0x4c6e);yield {call:'interrupt-flags',enabled:true};yield* emit(0x4c6f,0x4c73);
      if(!this.word(this.base+0x21eb)){finished=true;break;}
      yield* emit(0x4c75);yield {call:'interrupt-flags',enabled:false};
      yield* emit(0x4c76);const status=yield {call:'port-read',port};yield* emit(0x4c77,0x4c79);if(!(status&128))continue;
      for(let poll=0;;poll++){
        if(poll>=65536)throw new Error('DSP pause status never became ready');
        yield* emit(0x4c7b);const ready=yield {call:'port-read',port};yield* emit(0x4c7c,0x4c7e);if(!(ready&128))break;
      }
      yield* emit(0x4c80,0x4c82);yield {call:'port-write',port,value:0xd0};finished=true;break;
    }
    if(!finished)throw new Error('DSP pause never reached busy status');
    yield* emit(0x4c83);yield {call:'interrupt-flags',enabled:saved};yield* emit(0x4c84);
  }
  *writeDsp(value,port){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4b40,0x4b42);
    for(let guard=0;guard<65536;guard++){
      yield* emit(0x4b44);const status=yield {call:'port-read',port};yield* emit(0x4b45,0x4b47);
      if(!(status&0x80)){yield* emit(0x4b49,0x4b4b);yield {call:'port-write',port,value:value&255};yield* emit(0x4b4c);return;}
    }throw new Error('DSP write status never became ready');
  }
  *programDma({address,page,count}){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4c85,0x4c86,0x4c88,0x4c8a);yield {call:'port-write',port:0xa,value:5};
    yield* emit(0x4c8c,0x4c8e);yield {call:'port-write',port:0xc,value:0};
    yield* emit(0x4c90,0x4c92);yield {call:'port-write',port:0xb,value:0x49};
    for(const [load,out,port,value] of [[0x4c94,0x4c96,2,address&255],[0x4c98,0x4c9a,2,address>>>8],[0x4c9c,0x4c9e,3,count&255],[0x4ca0,0x4ca2,3,count>>>8],[0x4ca4,0x4ca6,0x83,page],[0x4ca8,0x4caa,0xa,1]]){
      yield* emit(load,out);yield {call:'port-write',port,value};
    }yield* emit(0x4cac,0x4cad);
  }
  *nextBlock(){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4d77,0x4d7a,0x4d7f);let count=65535;
    if(!this.memory[this.base+0x2202]){yield* emit(0x4d81);this.memory[this.base+0x2202]++;yield* emit(0x4d85);count=this.word(this.base+0x2207);}
    yield* emit(0x4d89);count=(count-this.word(this.base+0x21fe))&65535;yield* emit(0x4d8d);this.put(this.base+0x2200,count);
    yield* emit(0x4d91,0x4d92);const bytes=(count+1)&65535;
    if(bytes){
      const old=this.word(this.base+0x2203);yield* emit(0x4d94);this.put(this.base+0x2203,old-bytes);
      yield* emit(0x4d98);this.put(this.base+0x2205,this.word(this.base+0x2205)-Number(old<bytes));yield* emit(0x4d9d);
    }else{yield* emit(0x4d9f);this.put(this.base+0x2205,this.word(this.base+0x2205)-1);}
    yield* emit(0x4da3,0x4da5,0x4da9,0x4dac,0x4db0);yield* this.programDma({address:this.word(this.base+0x21fe),page:this.memory[this.base+0x21fd],count:this.word(this.base+0x2200)});
    yield* emit(0x4db3);this.memory[this.base+0x2202]--;yield* emit(0x4db7);this.memory[this.base+0x21fd]++;
    yield* emit(0x4dbb);this.put(this.base+0x21fe,0);
    yield* emit(0x4dc1,0x4dc5,0x4dc9,0x4dcc,0x4dce);const port=this.port(0xc);yield* this.writeDsp(0x14,port);
    yield* emit(0x4dd1,0x4dd3);yield* this.writeDsp(count&255,port);yield* emit(0x4dd6,0x4dd8);yield* this.writeDsp(count>>>8,port);yield* emit(0x4ddb);
  }
  *restoreVector(irq){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4cee);const saved=yield {call:'read-interrupt-flag'};
    yield* emit(0x4cef);yield {call:'interrupt-flags',enabled:false};
    yield* emit(0x4cf0,0x4cf2,0x4cf4,0x4cf5,0x4cf7,0x4cf9,0x4cfb,0x4cfc,0x4cfe,0x4d00,0x4d02);
    const vector=4*(irq+8);this.put(vector,this.word(this.base+0x21ed));yield* emit(0x4d05,0x4d08);this.put(vector+2,this.word(this.base+0x21ef));
    yield* emit(0x4d0c,0x4d0d);yield {call:'interrupt-flags',enabled:saved};yield* emit(0x4d0e);
  }
  *stop(){
    const emit=OriginalSoundInterruptWork.instructions;yield* emit(0x4ddc,0x4dde);yield {call:'port-write',port:0xa,value:5};
    yield* emit(0x4de0,0x4de4,0x4de6,0x4de8);const irq=this.memory[this.base+0x21ea],mask=yield {call:'port-read',port:0x21};
    yield* emit(0x4dea,0x4dec);yield {call:'port-write',port:0x21,value:(mask|(1<<irq))&255};
    yield* emit(0x4dee,0x4df1,0x4df4);yield* this.restoreVector(irq);
    yield* emit(0x4df7);this.put(this.base+0x21eb,0);yield* emit(0x4dfd,0x4e01,0x4e04);yield {call:'port-read',port:this.port(0xe)};yield* emit(0x4e05);
  }
  *run(){
    const emit=OriginalSoundInterruptWork.instructions;
    yield* emit(0x4d3c,0x4d3d,0x4d3e,0x4d3f,0x4d40,0x4d41,0x4d42,0x4d43,0x4d44,0x4d45,0x4d46,0x4d49,0x4d4b,0x4d4d,0x4d51,0x4d54);
    yield {call:'port-read',port:this.port(0xe)};yield* emit(0x4d55,0x4d58,0x4d5a);
    if(this.word(this.base+0x2203)){yield* emit(0x4d66);yield* this.nextBlock();}
    else{
      yield* emit(0x4d5c);yield* this.stop();yield* emit(0x4d5f,0x4d62);yield* this.devicePost();yield* emit(0x4d64);
    }
    yield* emit(0x4d69,0x4d6b);yield {call:'port-write',port:0x20,value:0x20};
    yield* emit(0x4d6d,0x4d6e,0x4d6f,0x4d70,0x4d71,0x4d72,0x4d73,0x4d74,0x4d75,0x4d76);
  }
}
