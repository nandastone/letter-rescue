"use strict";
// Composes cursor, VGA copies and sprites on caller-owned indexed surfaces.
// Resolvers provide current headers, row tables, buffers and resident shapes;
// no recorded operation schedule or expected output enters this executor.
class OriginalGraphicsWork {
  constructor({cursorState,surface,shape,onOperation=()=>{},onReturn=()=>{}}){
    this.state=cursorState;this.surface=surface;this.shape=shape;this.onOperation=onOperation;this.onReturn=onReturn;
  }
  static get singleStrings(){return new Set([...OriginalSurfaceCopyWork.singleStrings,...OriginalMonoSpriteWork.singleStrings,...OriginalSpriteWork.singleStrings,...OriginalRectFillWork.singleStrings]);}
  static *handleAddress({handle,state,segment}){
    const emit=OriginalCursorWork.instructions;yield* emit(0x6628,0x6629,0x662b,0x662e,0x6630);
    let address=0,empty=!handle;
    if(handle){yield* emit(0x6632,0x6635,0x6638);empty=!!(state&0x200);}
    if(empty)yield* emit(0x664c,0x664e,0x664f);
    else{
      yield* emit(0x663a,0x663d,0x663f,0x6641);const offset=state&15;
      if(offset||segment){yield* emit(0x6643,0x6646);address=16*segment+offset+6;}
    }
    yield* emit(0x6648,0x6649);return address;
  }
  *compose(generator){
    let next=generator.next();
    while(!next.done){
      const step=next.value;let result;
      if(typeof step==='string')yield step;
      else if(['rep-move-words','rep-store-words','rep-move-bytes','rep-store-bytes'].includes(step.call))result=yield step;
      else if(step.call==='cursor-prepare')result=yield* this.cursor('prepare',{pointer:step.surface.slice(0,2),rect:step.rect});
      else if(step.call==='cursor-hide')result=yield* this.cursor('hide');
      else if(step.call==='cursor-restore')result=yield* this.cursor('restore');
      else if(step.call==='surface-copy'){
        yield 'resident:7e32';result=yield* this.copy({mode:step.mode,source:step.source,destination:step.destination,sourceRect:step.sourceRect,destinationRect:step.destinationRect});
      }else if(step.call==='mask-sprite'){
        yield 'resident:826e';result=yield* this.sprite({...step,mask:true});
      }else if(step.call==='handle-address'){
        const shape=this.shape(step.handle);result=yield* OriginalGraphicsWork.handleAddress({handle:step.handle,...shape.handleWords});
        if(result!==shape.address)throw new Error('Resident shape handle address differs');
      }else throw new Error('Uncomposed graphics callee: '+step.call);
      next=generator.next(result);
    }
    return next.value;
  }
  *cursor(kind,input={}){
    if(!['prepare','hide','restore'].includes(kind))throw new Error('Unknown cursor operation');
    this.onOperation({kind:'cursor',operation:kind,input});
    const value=yield* this.compose(OriginalCursorWork[kind](this.state,input));this.onReturn({kind:'cursor',operation:kind,value});return value;
  }
  *copy({mode,source,destination,sourceRect,destinationRect}){
    const src=this.surface(source),dst=this.surface(destination);
    const input={mode,context:this.state[1],source_id:source,destination_id:destination,source:src.header,destination:dst.header,source_rows:src.rows,destination_rows:dst.rows,source_rect:sourceRect,destination_rect:destinationRect,sourcePixels:src.pixels,destinationPixels:dst.pixels};
    this.onOperation({kind:'copy',input});const value=yield* this.compose(OriginalSurfaceCopyWork.run(input));this.onReturn({kind:'copy',value});return value;
  }
  *sprite({handle,mode,color=0,x,y,mask=false}){
    const dst=this.surface(this.state[1]),shape=this.shape(handle);
    const input={mode,color,x,y,shape:shape.header,surface:dst.header,rows:dst.rows,sourcePixels:shape.pixels,destinationPixels:dst.pixels};
    this.onOperation({kind:'sprite',handle,mask,input});
    const value=yield* this.compose((mask?OriginalMonoSpriteWork:OriginalSpriteWork).run(input));this.onReturn({kind:'sprite',value});return value;
  }
  *fill({mode,color,rect}){
    const dst=this.surface(this.state[1]),input={mode,color,rect,surface:dst.header,rows:dst.rows,destinationPixels:dst.pixels};
    this.onOperation({kind:'fill',input});const value=yield* this.compose(OriginalRectFillWork.run(input));this.onReturn({kind:'fill',value});return value;
  }
}
