"use strict";
// Resident public sound API, executing against the shared resource and driver
// state. Device ports and interrupt flags are handled by the execution host.
class OriginalResidentSoundWork {
  constructor({memory,ds,driver,resources}){
    this.memory=memory;this.base=16*ds;this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);this.driver=driver;this.resources=resources||new OriginalResidentResourceWork({memory,ds});
  }
  word(at){return this.view.getUint16(at,true);}
  put(at,n){this.view.setUint16(at,n&65535,true);}
  pointer(handle){return {offset:(this.word(this.base+handle)&15)+6,segment:this.word(this.base+handle+2)};}
  *prepare(handle){
    const e=OriginalResidentResourceWork.instructions;
    yield* e(0xe6e6,0xe6e7,0xe6e9,0xe6ec,0xe6ed,0xe6ee,0xe6f1,0xe6f2,0xe6f3,0xe6f4);
    const flags=yield* this.resources.savedFlags(handle);yield* e(0xe6f7,0xe6fa);let result=handle;
    if(flags&0x2000)yield* e(0xe6fc);
    else{
      yield* e(0xe6ff,0xe700,0xe701,0xe702);const address=yield* this.resources.address(handle);
      yield* e(0xe705,0xe707,0xe70a,0xe70c);
      if(!address){yield* e(0xe70e,0xe954,0xe956);result=0;}
      else{
        yield* e(0xe711,0xe714,0xe718);
        if(this.memory[address]&1)throw new Error('Unprepared digital sound requires ordered decoding/resampling');
        yield* e(0xe71a);
      }
    }
    if(result)yield* e(0xe958);yield* e(0xe95b,0xe95c,0xe95d,0xe95f,0xe960);return result;
  }
  *load(id){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xe4aa,0xe4ab,0xe4ad,0xe4ae,0xe4b1,0xe4b4,0xe4b5,0xe4b6,0xe4b9,0xe4ba,0xe4bb);
    let handle=yield* this.resources.resourceHandle(0x534e44,id);yield* e(0xe4be,0xe4c0,0xe4c2);
    if(handle){yield* e(0xe4c4,0xe4c5,0xe4c6,0xe4c7);const ready=yield* this.prepare(handle);yield* e(0xe4ca,0xe4cc);
      if(!ready){yield* e(0xe4ce,0xe4cf,0xe4d0,0xe4d1);yield {call:'free-sound',handle};yield* e(0xe4d4);handle=0;}
    }
    yield* e(0xe4d6,0xe4d8,0xe4d9,0xe4db,0xe4dc);return handle;
  }
  *status({offset,segment}){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xc505,0xc506,0xc508,0xc50b,0xc50d,0xc50f);let result;
    if(!(offset|segment)){yield* e(0xc54a,0xc54d,0xc551);result=this.word(this.base+0x211c)|this.word(this.base+0x2132)|this.word(this.base+0x2144);}
    else{
      yield* e(0xc511,0xc513,0xc517);let matched=offset===this.word(this.base+0x2120);
      if(matched){yield* e(0xc519,0xc51d);matched=segment===this.word(this.base+0x2122);}
      if(matched){yield* e(0xc51f,0xc522);result=this.word(this.base+0x211c);}
      else{
        yield* e(0xc524,0xc528);matched=offset===this.word(this.base+0x2136);
        if(matched){yield* e(0xc52a,0xc52e);matched=segment===this.word(this.base+0x2138);}
        if(matched){yield* e(0xc530,0xc533);result=this.word(this.base+0x2132);}
        else{
          yield* e(0xc535,0xc539);matched=offset===this.word(this.base+0x2148);
          if(matched){yield* e(0xc53b,0xc53f);matched=segment===this.word(this.base+0x214a);}
          if(matched){yield* e(0xc541,0xc544);result=this.word(this.base+0x2144);}
          else{yield* e(0xc546,0xc548);result=0;}
        }
      }
    }
    yield* e(0xc555,0xc556);return result;
  }
  *stopDigital({offset,segment}){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xc69d);const saved=yield {call:'read-interrupt-flag'};
    yield* e(0xc69e);yield {call:'interrupt-flags',enabled:false};yield* e(0xc69f,0xc6a1,0xc6a3);let matched=!(offset|segment);
    if(!matched){yield* e(0xc6a5,0xc6a9);matched=offset===this.word(this.base+0x2120);if(matched){yield* e(0xc6ab,0xc6ad,0xc6b1);matched=segment===this.word(this.base+0x2122);}}
    if(matched){yield* e(0xc6b3,0xc6b5);const active=this.word(this.base+0x211c);this.put(this.base+0x211c,0);yield* e(0xc6b9);
      if(active){yield* e(0xc6bb,0xc6bd);yield* this.driver.dispatch(3);yield* e(0xc6c1,0xc6c4,0xc6c7);yield* this.driver.notifyCompletion();}
    }
    yield* e(0xc6ca);yield {call:'interrupt-flags',enabled:saved};yield* e(0xc6cb);
  }
  *stopOther(pointer,kind){
    const e=OriginalResidentResourceWork.instructions,{offset,segment}=pointer,music=kind==='music';let saved;
    if(!music){yield* e(0xc6fb);saved=yield {call:'read-interrupt-flag'};yield* e(0xc6fc);yield {call:'interrupt-flags',enabled:false};}
    yield* e(...(music?[0xc6cc,0xc6ce,0xc6d0]:[0xc6fd,0xc6ff,0xc701]));let matched=!(offset|segment);
    if(!matched){yield* e(...(music?[0xc6d2,0xc6d6]:[0xc703,0xc707]));matched=offset===this.word(this.base+(music?0x2136:0x2148));
      if(matched){yield* e(...(music?[0xc6d8,0xc6da,0xc6de]:[0xc709,0xc70d]));matched=segment===this.word(this.base+(music?0x2138:0x214a));}
    }
    if(matched){yield* e(...(music?[0xc6e0,0xc6e2]:[0xc70f,0xc711]));const at=this.base+(music?0x2132:0x2144),active=this.word(at);this.put(at,0);yield* e(music?0xc6e6:0xc715);
      if(active)throw new Error('Active '+kind+' stop requires composition');
    }
    if(!music){yield* e(0xc734);yield {call:'interrupt-flags',enabled:saved};}yield* e(music?0xc6fa:0xc735);
  }
  *stopPointer(pointer){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xc461,0xc462,0xc464,0xc467);yield* this.stopDigital(pointer);
    yield* e(0xc46a,0xc46d);yield* this.stopOther(pointer,'music');yield* e(0xc470,0xc473);yield* this.stopOther(pointer,'speaker');yield* e(0xc476,0xc477);
  }
  *digital(pointer){
    const e=OriginalResidentResourceWork.instructions,{offset,segment}=pointer,source=16*segment+offset;
    yield* e(0xc736,0xc737,0xc739,0xc73a,0xc73b,0xc73e,0xc740);
    if(this.memory[this.base+0x2119]&1){
      yield* e(0xc742,0xc744,0xc746);yield* this.stopDigital({offset:0,segment:0});
      yield* e(0xc749);this.put(this.base+0x211c,1);yield* e(0xc74f);this.put(this.base+0x211e,0);
      yield* e(0xc755,0xc758);this.put(this.base+0x2124,0xe54c);yield* e(0xc75b);this.put(this.base+0x2126,this.driver.residentSegment);
      yield* e(0xc75f,0xc762);this.put(this.base+0x2120,offset);yield* e(0xc766);this.put(this.base+0x2122,segment);
      yield* e(0xc76a,0xc76e,0xc770);yield* this.driver.dispatch(5);
      yield* e(0xc774,0xc777,0xc77b);let length=0;
      if(this.memory[source]&128){yield* e(0xc77d,0xc781);if(this.word(this.base+0x212c)){yield* e(0xc783,0xc787,0xc789);length=this.word(source+8);}}
      if(!length){yield* e(0xc78b);length=this.word(source+4);}
      yield* e(0xc78f,0xc793,0xc796,0xc799,0xc79c,0xc79e);yield* this.driver.dispatch(7,{segment,offset:(offset+10)&65535,length,rate:this.word(source+1)});
      yield* e(0xc7a2,0xc7a7);
      if(!this.word(this.base+0x212c)){for(;;){yield* e(0xc7a9,0xc7ae);if(!this.word(this.base+0x211c))break;}}
    }
    yield* e(0xc7b0,0xc7b3,0xc7b4,0xc7b5,0xc7b6);return this.word(this.base+0x211c);
  }
  *playPointer(pointer){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xc47a,0xc47b,0xc47d,0xc480,0xc482,0xc484);let result=0;
    if(pointer.offset|pointer.segment){yield* e(0xc486,0xc489,0xc48b);
      if(!(this.memory[16*pointer.segment+pointer.offset]&1))throw new Error('Music/speaker start requires composition');
      yield* e(0xc49f,0xc4a0,0xc4a1,0xc4a4,0xc4a5,0xc4a6);result=yield* this.digital(pointer);yield* e(0xc4a9);
    }
    yield* e(0xc49b,0xc49c);return result;
  }
  *playHandle(handle){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xe4e0,0xe4e1,0xe4e3,0xe4e6,0xe4e7,0xe4e8,0xe4eb,0xe4ed);let result=0;
    if(handle){
      yield* e(0xe4ef,0xe4f0,0xe4f1,0xe4f2);yield* this.resources.unagedAddress(handle);const pointer=this.pointer(handle);
      yield* e(0xe4f5,0xe4f7,0xe4fa,0xe4fb,0xe4fc,0xe4fd,0xe4fe);const active=yield* this.status(pointer);yield* e(0xe501,0xe503);
      if(active){yield* e(0xe505,0xe508,0xe509,0xe50a,0xe50b,0xe50c);yield* this.stopPointer(pointer);}
      yield* e(0xe50f,0xe510,0xe511,0xe512);const flags=yield* this.resources.savedFlags(handle);
      yield* e(0xe515,0xe517,0xe518,0xe519,0xe51a);yield* this.resources.lock(handle);
      yield* e(0xe51d,0xe51e,0xe51f,0xe522,0xe525,0xe526,0xe527,0xe528,0xe529);result=yield* this.playPointer(this.pointer(handle));
      yield* e(0xe52c,0xe52f,0xe531);
      if(!result){yield* e(0xe533,0xe534,0xe535,0xe536,0xe537);yield* this.resources.setFlags(handle,flags);yield* e(0xe53a);}
    }else yield* e(0xe53c);
    yield* e(0xe541,0xe544,0xe545,0xe546,0xe548,0xe549);return result;
  }
  *start(id){
    const e=OriginalResidentResourceWork.instructions;yield* e(0xe5e2,0xe5e3,0xe5e5,0xe5e8,0xe5e9,0xe5ea);const handle=yield* this.load(id);
    yield* e(0xe5ed,0xe5ee,0xe5ef,0xe5f0);const result=yield* this.playHandle(handle);yield* e(0xe5f3,0xe5f5,0xe5f6);return result;
  }
}
