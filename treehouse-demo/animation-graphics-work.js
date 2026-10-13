"use strict";
// Composes main animation work with resident geometry and indexed rendering.
// The memory adapter is a mutable guest data/image store. It contains current
// state and assets, never a recorded sequence of expected frames or timings.
class OriginalAnimationGraphicsWork {
  constructor({memory,ds,onOperation=()=>{},onReturn=()=>{},shapeConverter=null}){
    this.memory=memory;this.base=16*ds;this.data=memory.subarray(this.base,this.base+65536);this.view=new DataView(memory.buffer,memory.byteOffset,memory.byteLength);this.clipStack=[];this.offsetRect=null;
    const scalar=[0x2062,0x205a,0x2100,0x2064,0x2066,0x20ca,0x20cc,0x20ce,0x20c8,0x2060],offsets=[...scalar,...Array.from({length:16},(_,i)=>0x2088+2*i),...Array.from({length:16},(_,i)=>0x20d0+2*i)];
    this.cursorState=this.wordView(offsets.map(o=>this.base+o));
    this.graphics=new OriginalGraphicsWork({cursorState:this.cursorState,surface:id=>this.surface(id),shape:handle=>this.shape(handle),onOperation,onReturn});
    this.resources=new OriginalResidentResourceWork({memory,ds});
    this.shapeConverter=shapeConverter;
  }
  static get singleStrings(){return new Set([...OriginalGraphicsWork.singleStrings,...OriginalGeometryWork.singleStrings]);}
  word(at){return this.view.getUint16(at,true);}
  wordView(addresses){return new Proxy(Array(addresses.length).fill(0),{get:(target,key)=>typeof key==='string'&&/^\d+$/.test(key)?this.word(addresses[Number(key)]):Reflect.get(target,key),set:(target,key,value)=>{if(typeof key==='string'&&/^\d+$/.test(key)){this.view.setUint16(addresses[Number(key)],value&65535,true);return true;}return Reflect.set(target,key,value);}});}
  words(at,length){return this.wordView(Array.from({length},(_,i)=>at+2*i));}
  surface(id){
    const header=this.words(this.base+id,16),height=(header[4]-header[2])&65535,bytes=height*header[6],address=16*header[1]+header[0];
    if(height>256||bytes>65536||address+bytes>this.memory.length)throw new Error('Invalid animation surface');
    return {header,rows:this.words(this.base+header[7],height),pixels:this.memory.subarray(address,address+bytes)};
  }
  shape(handle){
    const state=this.word(this.base+handle),segment=this.word(this.base+handle+2),address=16*segment+(state&15)+6,header=Array.from(this.words(address,3));
    const bytes=header[0]*header[2];if(!handle||(state&0x200)||address+6+bytes>this.memory.length)throw new Error('Animation shape is not resident');
    return {header,handleWords:{state,segment},address,pixels:this.memory.subarray(address+6,address+6+bytes)};
  }
  state(instance){
    const owner=this,drawing=this.wordView([0x5254,0x5520,0x57c0,0x52ca,0xd96,0xd98,0xd9a,0xd9c,0x5270].map(o=>this.base+o));
    return {instance,memory:this.memory.subarray(this.base+instance,this.base+instance+726),drawing,
      get context(){return owner.cursorState[1];},set context(n){owner.cursorState[1]=n;},
      get display_count(){return owner.word(owner.base+0x5586);},set display_count(n){owner.view.setUint16(owner.base+0x5586,n&65535,true);},
      get sound_enabled(){return owner.word(owner.base+0x5822);},get cue(){return owner.memory[owner.base+0x211b];},
      readCode(offset){const at=16*owner.word(owner.base+instance+0x50)+offset;if(at>=owner.memory.length)throw new Error('Script pointer outside memory');return owner.memory[at];}
    };
  }
  *compose(generator,state){
    const g=OriginalGeometryWork,v=OriginalAnimationWork.view(state),rect=offset=>[0,2,4,6].map(i=>v.word(offset+i));
    let next=generator.next();while(!next.done){const step=next.value;let answer;
      if(typeof step==='string'||step.call?.startsWith('rep-'))answer=yield step;
      else if(step.call==='point-local')answer=yield* g.localPoint(step.point,step.surface);
      else if(step.call==='rectangle-intersection')answer=yield* g.intersection(step.a,step.b,step.out);
      else if(step.call==='rectangle-empty')answer=yield* g.empty(step.rect);
      else if(step.call==='rectangle-union')answer=yield* g.union(step.a,step.b);
      else if(step.call==='rectangle-offset'){
        answer=yield* g.offset(rect(0x46),v.word(0x3e),v.word(0x40));this.offsetRect=answer;
      }else if(step.call==='shape-header'){
        const shape=this.shape(step.handle);yield* OriginalGraphicsWork.handleAddress({handle:step.handle,...shape.handleWords});answer={height:shape.header[0],width:shape.header[1]};
      }else if(step.call==='shape-draw'){
        yield 'resident:8272';answer=yield* this.graphics.sprite({handle:v.word(0x29a+2*step.shape),mode:step.mode,x:step.x,y:step.y});
      }else if(step.call==='clip-push')answer=yield* this.compose(g.clipPush(this.surface(state.context).header,step.rect,this.clipStack),state);
      else if(step.call==='clip-pop')answer=yield* g.clipPop(this.surface(state.context).header,this.clipStack);
      else if(step.call==='background-restore'){
        yield 'resident:7e32';answer=yield* this.graphics.copy({mode:0,source:(state.instance+0x2e)&65535,destination:state.instance,sourceRect:rect(0x10),destinationRect:rect(0x10)});
      }else if(step.call==='surface-display'){
        if(!this.offsetRect)throw new Error('Missing translated display rectangle');yield 'resident:7e32';answer=yield* this.graphics.copy({mode:0,source:state.instance,destination:v.word(0x2c),sourceRect:rect(0x46),destinationRect:this.offsetRect});
      }else if(step.call==='surface-clear')answer=yield* this.compose(g.clear(this.word(this.base+v.word(0x2c)+0x20),rect(0x10)),state);
      else if(step.call==='rectangle-fill'){yield 'resident:a2d0';answer=yield* this.graphics.fill(step);}
      else if(step.call==='near-fill')answer=yield* g.nearFill(this.data,(state.instance+0x46)&65535,step.bytes,step.value);
      else if(step.call==='near-copy'){
        const bytes=Uint8Array.from(step.words.flatMap(n=>[n&255,(n>>>8)&255]));answer=yield* g.nearCopy(this.data,0,step.destination&65535,step.bytes,{sourceBytes:bytes});
      }else if(step.call==='caption-draw')answer=yield* this.compose(this.resources.caption(step,this.graphics),state);
      else if(step.call==='convert-shape')answer=this.shapeConverter?yield* this.shapeConverter.convert(step):yield step;
      else if(step.call==='free-shape')answer=this.shapeConverter?.heap?yield* this.shapeConverter.heap.free(step.handle):yield step;
      else if(step.call==='allocate-shape')answer=yield step;
      else throw new Error('Animation callee requires composition: '+step.call);
      next=generator.next(answer);
    }return next.value;
  }
  *frame(state,{readTick}){return yield* this.compose(OriginalAnimationWork.frame(state,{readTick}),state);}
}
