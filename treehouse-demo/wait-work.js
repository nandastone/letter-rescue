"use strict";
// Original wait callers. A scheduler executes instruction yields, supplies call
// results, and changes shared countdown/sound state at interrupt boundaries.
class OriginalWaitWork {
  static *instructions(...addresses){for(const address of addresses)yield 'resident:'+address.toString(16).padStart(4,'0');}
  static *timer({index,readCountdown,interruptible=true}){
    if(!Number.isInteger(index)||index<0||index>3||typeof readCountdown!=='function')throw new Error("Invalid timer wait");
    const emit=this.instructions;
    yield* emit(...(interruptible?[0x5697,0x5698]:[0x56c2,0x56c3]));
    for(;;){
      yield* emit(interruptible?0x569a:0x56c5);
      const input=yield {call:'input-poll'};
      if(interruptible){
        yield* emit(0x569e,0x56a0);
        if(input){
          yield* emit(0x56a2,0x56a4,0x56a5,0x56a6);yield {call:'clear-input',value:0};
          yield* emit(0x56a9,0x56ac,0x56bc,0x56be,0x56bf);return 1;
        }
        yield* emit(0x56ae,0x56b1,0x56b3);const remaining=readCountdown(index);yield* emit(0x56b8);
        if(!remaining){yield* emit(0x56ba,0x56bc,0x56be,0x56bf);return 0;}
      }else{
        yield* emit(0x56c9,0x56cc,0x56ce);const remaining=readCountdown(index);yield* emit(0x56d3);
        if(!remaining){yield* emit(0x56d5,0x56d7,0x56d8);return input;}
      }
    }
  }
  static *setTimer({index,ticks,timer,interruptible=true}){
    const emit=this.instructions;
    yield* emit(...(interruptible?[0x56db,0x56dc,0x56de,0x56e1,0x56e4,0x56e6]:[0x56f7,0x56f8,0x56fa,0x56fd,0x5700,0x5702]));
    timer.setCountdown(index,ticks);
    yield* emit(...(interruptible?[0x56ea,0x56ed,0x56ee]:[0x5706,0x5709,0x570a]));
    const result=yield* this.timer({index,readCountdown:i=>timer.countdowns[i],interruptible});
    yield* emit(...(interruptible?[0x56f1,0x56f3,0x56f4]:[0x570d,0x570f,0x5710]));return result;
  }
  static *channelStatus({pointer,readChannels}){
    const emit=this.instructions;yield* emit(0xc505,0xc506,0xc508,0xc50b,0xc50d,0xc50f);
    let result=0;
    if(pointer.segment||pointer.offset){
      yield* emit(0xc511);
      const branches=[[0xc513,0xc517,0xc519,0xc51d,0xc51f,0xc522],[0xc524,0xc528,0xc52a,0xc52e,0xc530,0xc533],[0xc535,0xc539,0xc53b,0xc53f,0xc541,0xc544]];
      let found=false;
      for(let i=0;i<3;i++){
        const b=branches[i];yield* emit(b[0]);const sameOffset=pointer.offset===readChannels()[i].offset;yield* emit(b[1]);
        if(!sameOffset)continue;
        yield* emit(b[2]);const sameSegment=pointer.segment===readChannels()[i].segment;yield* emit(b[3]);
        if(!sameSegment)continue;
        yield* emit(b[4]);result=readChannels()[i].active;yield* emit(b[5]);found=true;break;
      }
      if(!found)yield* emit(0xc546,0xc548);
    }else{
      yield* emit(0xc54a);result=readChannels()[0].active;
      yield* emit(0xc54d);result|=readChannels()[1].active;
      yield* emit(0xc551);result|=readChannels()[2].active;
    }
    yield* emit(0xc555,0xc556);return result&65535;
  }
  static *soundStatus({id,readChannels}){
    const emit=this.instructions;yield* emit(0xe5a2,0xe5a3,0xe5a5,0xe5a8,0xe5a9,0xe5ac,0xe5ae,0xe5af,0xe5b1,0xe5b4,0xe5b6);
    let pointer={segment:0,offset:0},result=0,valid=true;
    if(id){
      yield* emit(0xe5b8,0xe5b9,0xe5ba,0xe5bb);const handle=yield {call:'sound-load',id};
      yield* emit(0xe5be,0xe5bf,0xe5c0,0xe5c1);pointer=yield {call:'memory-handle-address',handle};
      yield* emit(0xe5c4,0xe5c6,0xe5c9,0xe5cb);valid=!!(pointer.offset||pointer.segment);
      if(!valid)yield* emit(0xe5cd,0xe5cf);
    }
    if(valid){yield* emit(0xe5d2,0xe5d5,0xe5d6,0xe5d7,0xe5d8);result=yield* this.channelStatus({pointer,readChannels});}
    yield* emit(0xe5db,0xe5dc,0xe5de,0xe5df);return result;
  }
  static *sound({id,readChannels}){
    const emit=this.instructions;yield* emit(0x577e,0x577f,0x5781);
    for(;;){
      yield* emit(0x5797,0x579a,0x579b,0x579c);const active=yield* this.soundStatus({id,readChannels});
      yield* emit(0x579f,0x57a1);if(!active){yield* emit(0x57a3,0x57a5,0x57a6);return 0;}
      yield* emit(0x5783);const input=yield {call:'input-poll'};yield* emit(0x5787,0x5789);
      if(input){yield* emit(0x578b,0x578d,0x578e,0x578f);yield {call:'clear-input',value:0};yield* emit(0x5792,0x5795,0x57a3,0x57a5,0x57a6);return 1;}
    }
  }
}
