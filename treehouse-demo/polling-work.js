"use strict";
// Resident 58E2 input poll. Instruction order is derived from the original code;
// host callback boundaries are yielded separately from their guest trampolines.
class OriginalPollingWork {
  static *run(input){
    const state={...input,edges:[...input.edges],bindings:[...input.bindings],keys:[...input.keys],latches:[...input.latches]};
    if(state.joystick)throw new Error("Joystick polling work is not reconstructed");
    if(state.keys.length!==96||state.bindings.length!==96||state.latches.length!==96||state.edges.length!==2)throw new Error("Invalid polling state");
    const resident=function*(...addresses){for(const address of addresses)yield 'resident:'+address.toString(16).padStart(4,'0');};
    const callback=function*(name,offsets){for(const offset of offsets)yield name+':'+offset.toString(16).padStart(2,'0');};
    const mouseButton=function*(button){
      yield* resident(0x54c5,0x54c6,0x54c8,0x54ca,0x54ce);
      let pressed=false;
      if(state.mouse_present){
        yield* resident(0x54d0,0x54d3);yield* callback('mouse',[0,9]);
        const buttons=yield {callback:'mouse-position',button};
        if(!Number.isInteger(buttons)||buttons<0||buttons>65535)throw new Error("Invalid mouse callback result");
        yield* callback('mouse',[13]);yield* resident(0x54d5,0x54d7,0x54d8,0x54db,0x54dd,0x54df);
        pressed=!!(buttons&(1<<(button-1)));if(pressed)yield* resident(0x54e1);
      }
      yield* resident(0x54e4,0x54e5);return pressed;
    };
    const mouseEdges=function*(){
      yield* resident(0x5bb0,0x5bb3,0x5bb4,0x5bb5,0x5bb6);
      const left=yield* mouseButton(1);yield* resident(0x5bb9,0x5bbb);
      if(left){
        yield* resident(0x5bbd,0x5bc1,0x5bc7);
        if(!state.edges[0]){yield* resident(0x5bc9,0x5bd0,0x5bd3);state.edges[0]=1;return 1;}
      }else{yield* resident(0x5bd4,0x5bd8);state.edges[0]=0;}
      yield* resident(0x5bdf,0x5be2,0x5be3,0x5be4,0x5be5);
      const right=yield* mouseButton(2);yield* resident(0x5be8,0x5bea);
      if(right){
        yield* resident(0x5bec,0x5bf0,0x5bf6);
        if(!state.edges[1]){yield* resident(0x5bf8,0x5bff,0x5bd0,0x5bd3);state.edges[1]=1;return 1;}
      }else{yield* resident(0x5c01,0x5c05);state.edges[1]=0;}
      yield* resident(0x5c0c,0x5c0e);return 0;
    };
    yield* resident(0x58e2,0x58e3,0x58e5,0x58e8,0x58e9,0x58ee,0x58ef,0x58f0);
    yield* resident(0x5466,0x5469,0x546b);yield* callback('dos',[0,1]);yield {callback:'keyboard-poll'};
    // DOS overhead advances IP past IRET/RETF into the 0140h LOOP delay.
    yield* callback('dos',[7,8]);for(let cx=0x140;cx;cx--)yield* callback('dos',[11]);yield* callback('dos',[13,14]);
    yield* resident(0x546d,0x58f3,0x58f4,0x57d3,0x57d4,0x57d6);
    for(const [key,cmp,branch] of [[72,0x57d9,0x57de],[80,0x57e0,0x57e5],[75,0x57e7,0x57ec],[77,0x57ee,0x57f3],[76,0x57f5,0x57fa]]){
      yield* resident(cmp,branch);if(state.keys[key])throw new Error("Keyboard cursor movement work is not reconstructed");
    }
    yield* resident(0x57fc,0x58de,0x58e0,0x58e1,0x58f7,0x58fb,0x5901,0x5909,0x590e);
    let result=0;
    if(state.mouse_present){yield* resident(0x5910,0x5911);result=yield* mouseEdges();yield* resident(0x5914);}
    yield* resident(0x5917,0x591b);
    if(result){yield* resident(0x591d,0x5920);}
    else{
      yield* resident(0x5922,0x5927);
      for(let key=0;key<96;key++){
        yield* resident(0x5939,0x593d,0x593f,0x5942,0x5947);
        let clear=!state.keys[key];
        if(!clear){yield* resident(0x5949,0x594d,0x594f,0x5955);clear=!state.bindings[key];}
        if(clear){yield* resident(0x5929,0x592d,0x5930);state.latches[key]=0;}
        else{
          yield* resident(0x5957,0x595b,0x595e,0x5964);
          if(!state.latches[key]){yield* resident(0x5966,0x596c,0x5970,0x5975);state.latches[key]=1;result=state.bindings[key];break;}
        }
        yield* resident(0x5936);
      }
      if(!result){
        yield* resident(0x5939,0x593d,0x5977,0x5978,0x5c52,0x5c55,0x5c57,0x5c5a,0x5c5d,0x5c5f,0x5c61,0x5c63,0x5c64,0x597b,0x597d);
        if(state.modifier&4){yield* resident(0x597f,0x5984);if(state.keys[16])throw new Error("Control-key exit work is not reconstructed");}
        yield* resident(0x598d);
      }
    }
    yield* resident(0x598f,0x5990,0x5992,0x5993);return {result,state};
  }
  static execute(state,{mouseButtons=[]}={}){
    const machine=this.run(state),counts={},callbacks=[],path=[];let next=machine.next(),index=0,instructions=0;
    while(!next.done){
      const step=next.value;
      if(typeof step==='string'){counts[step]=(counts[step]||0)+1;instructions++;path.push(step);next=machine.next();}
      else {callbacks.push(step.callback);next=machine.next(step.callback==='mouse-position'?mouseButtons[index++]:undefined);}
    }
    if(index!==mouseButtons.length)throw new Error("Unused mouse callback results");
    return {...next.value,counts,instructions,callbacks,path};
  }
}
