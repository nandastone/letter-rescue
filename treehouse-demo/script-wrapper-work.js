"use strict";
// Main 485D..48BD continuation after one interpreter invocation.
class OriginalScriptWrapperWork {
  static *run({result,firstFrame,displayCount,baseId,suppressCallback,callbackFrame}){
    const emit=function*(...addresses){for(const address of addresses)yield 'main:'+address.toString(16).padStart(4,'0');};
    yield* emit(0x485d,0x4860);
    if(result){yield* emit(0x4865);return {done:true,reason:'script'};}
    yield* emit(0x4862,0x4868,0x486c);
    if(firstFrame){
      yield* emit(0x4871,0x4876);
      if(displayCount===1){yield* emit(0x487b);return {done:true,reason:'first-frame'};}
      yield* emit(0x4878);
    }else yield* emit(0x486e);
    yield* emit(0x487e,0x4882);
    if(baseId===70){
      yield* emit(0x4887);const input=yield {call:'input-poll'};yield* emit(0x488c,0x488f);
      if(input){yield* emit(0x4894,0x4899,0x489b,0x489c,0x489d);yield {call:'clear-animation-callback'};yield* emit(0x48a2);return {done:true,reason:'input'};}
      yield* emit(0x4891);
    }else yield* emit(0x4884);
    yield* emit(0x48a5,0x48aa);
    if(suppressCallback)yield* emit(0x48ac);
    else{
      yield* emit(0x48af,0x48b2,0x48b5,0x48b8,0x48b9,0x48ba,0x4e9e,0x4e9f,0x4ea1,0x4ea5,0x4ea6,0x4ea7,0x4eac);
      if(((callbackFrame<<16)>>16)<0)yield* emit(0x4eae);
      else{
        yield* emit(0x4eb1,0x4eb4,0x4eb8);
        if(callbackFrame===displayCount){yield* emit(0x4ebd,0x4ec0,0x4ec3,0x4ec6,0x4ec7,0x4ec8);yield {call:'activity-overlay'};}
        else yield* emit(0x4eba);
      }
      yield* emit(0x4ecb,0x4ecc,0x4ecd,0x4ecf,0x4ed0);
    }
    yield* emit(0x48bd,0x4855,0x4858,0x4859,0x485a);return {done:false};
  }
}
