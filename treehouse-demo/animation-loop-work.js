"use strict";
// Main 4855..48C0: one shared instance, script bytes and mutable game globals.
// The execution host supplies interrupts/devices and any unresolved callees.
class OriginalAnimationLoopWork {
  constructor({adapter,instance,firstFrame,baseId,activity,sound=null,onIteration=()=>{}}){
    this.adapter=adapter;this.state=adapter.state(instance);this.firstFrame=firstFrame;this.baseId=baseId;this.activity=activity;this.sound=sound;this.onIteration=onIteration;this.iterations=0;
  }
  readTick(){return this.adapter.view.getUint32(this.adapter.base+0x201e,true);}
  *compose(generator){
    let next=generator.next();while(!next.done){const step=next.value;let answer;
      if(typeof step==='string'||step.call?.startsWith('rep-'))answer=yield step;
      else if(step.call==='frame-update')answer=yield* this.adapter.frame(this.state,{readTick:()=>this.readTick()});
      else if(step.call==='scene-compose')answer=yield* this.adapter.compose(OriginalAnimationWork.compose(this.state),this.state);
      else if(step.call==='slot-bounds')answer=yield* this.adapter.compose(OriginalAnimationWork.bounds(this.state,step.slot),this.state);
      else if(step.call==='sound-start'&&this.sound)answer=yield* this.sound.start(step.id);
      else answer=yield {...step,instance:this.state.instance,baseId:this.baseId,activity:this.activity};
      next=generator.next(answer);
    }return next.value;
  }
  *run(){
    yield* OriginalScriptWork.instructions(0x4855,0x4858,0x4859,0x485a);
    for(;;){
      const result=yield* this.compose(OriginalScriptWork.run(this.state,{readTick:()=>this.readTick()}));this.iterations++;this.onIteration({iteration:this.iterations,result,state:this.state});
      const next=yield* this.compose(OriginalScriptWrapperWork.run({result,firstFrame:this.firstFrame,displayCount:this.state.display_count,baseId:this.baseId,suppressCallback:this.adapter.word(this.adapter.base+0x5296),callbackFrame:this.adapter.word(this.adapter.base+0xdc6)}));
      if(next.done){yield 'main:48c0';return {...next,iterations:this.iterations};}
    }
  }
}
