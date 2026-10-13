"use strict";
// Resident 8955/857A/8822. Shared words are the ten cursor globals, then
// screen (2088) and saved-background (20D0) surface headers, sixteen each.
class OriginalCursorWork {
  static *instructions(...addresses){for(const a of addresses)yield 'resident:'+a.toString(16);}
  static signed(n){return (n<<16)>>16;}
  static *prepare(state,{pointer,rect}){
    const emit=this.instructions,s16=this.signed;
    yield* emit(0x8955,0x895a);
    if(s16(state[0])<0){yield* emit(0x895c);state[0]=(state[0]-1)&65535;yield* emit(0x8960);return;}
    yield* emit(0x8961,0x8962,0x8963,0x8964,0x8965,0x8966,0x896a);
    let overlap=pointer[0]===state[10];
    if(overlap){yield* emit(0x896c,0x896e,0x8972);overlap=pointer[1]===state[11];}
    if(overlap){yield* emit(0x8974,0x8978,0x897a,0x897e,0x8980,0x8983);overlap=s16(state[30]-state[12])>s16(rect[0]);}
    if(overlap){yield* emit(0x8985,0x8987,0x8989,0x898c);overlap=s16(state[31]-state[13])>s16(rect[1]);}
    if(overlap){yield* emit(0x898e,0x8992,0x8994,0x8997);overlap=s16(state[28]-state[12])<s16(rect[2]);}
    if(overlap){yield* emit(0x8999,0x899b,0x899d,0x89a0);overlap=s16(state[29]-state[13])<s16(rect[3]);}
    if(overlap){yield* emit(0x89a2,0x89a3);yield {call:'cursor-hide',address:0x89a3};yield* emit(0x89a6);}
    else {yield* emit(0x89a8);state[0]=(state[0]+1)&65535;}
    yield* emit(0x89ac,0x89ad,0x89ae,0x89af,0x89b0,0x89b1);
  }
  static *hide(state){
    const emit=this.instructions;yield* emit(0x857a);let count=this.signed(state[0]);yield* emit(0x857d,0x857f);
    if(count<0){yield* emit(0x85ac,0x85ad);state[0]=(count-1)&65535;yield* emit(0x85b0);return;}
    yield* emit(0x8581);if(count!==0){yield* emit(0x8583);count=-count;}
    yield* emit(0x8585,0x8586);state[0]=(count-1)&65535;
    yield* emit(0x8589,0x858b);const previous=state[1];state[1]=0;
    yield* emit(0x858f,0x8590,0x8593,0x8594,0x8597,0x8598,0x859b,0x859c,0x859d,0x859e,0x859f,0x85a2,0x85a3,0x85a4);
    yield {call:'surface-copy',address:0x85a4,mode:0,source:0x20d0,destination:0x2088,sourceRect:Array.from(state.slice(28,32)),destinationRect:Array.from(state.slice(28,32))};
    yield* emit(0x85a7);state[1]=previous;yield* emit(0x85ab);
  }
  static *restore(state){
    const emit=this.instructions;yield* emit(0x8822);let count=this.signed(state[0]);yield* emit(0x8826);
    if(count===0){yield* emit(0x8846);return;}
    yield* emit(0x8828,0x882b);
    if(count< -1){yield* emit(0x8842);state[0]=(state[0]+1)&65535;yield* emit(0x8846);return;}
    yield* emit(0x882d);
    if(count!==-1){
      yield* emit(0x882f,0x8830);state[0]=--count;yield* emit(0x8834);
      if(count!==0){yield* emit(0x8846);return;}
      yield* emit(0x8836);const pending=state[2];state[2]=0;yield* emit(0x883a);
      if(pending===0){yield* emit(0x8846);return;}
      yield* emit(0x883c,0x883d);yield {call:'cursor-hide',address:0x883d};yield* emit(0x8840);
    }
    yield* emit(0x8847,0x884a,0x884c);const previous=state[1];state[1]=0x2088;yield* emit(0x8850);
    yield* emit(0x8851,0x8854,0x8858,0x885b);state[29]=(state[4]-state[6]+state[13])&65535;
    yield* emit(0x885e,0x8861);state[31]=(state[29]+16)&65535;
    yield* emit(0x8864,0x8867,0x886b,0x886e);state[28]=(state[3]-state[5]+state[12])&65535;
    yield* emit(0x8871,0x8874);state[30]=(state[28]+16)&65535;
    yield* emit(0x8877,0x887a,0x887b,0x887c,0x887f,0x8880,0x8881,0x8882,0x8883,0x8886,0x8887,0x8888);
    yield {call:'surface-copy',address:0x8888,mode:0,source:0x2088,destination:0x20d0,sourceRect:Array.from(state.slice(28,32)),destinationRect:Array.from(state.slice(28,32))};
    yield* emit(0x888b,0x888f,0x8890);yield {call:'handle-address',address:0x8890,handle:state[7]};
    yield* emit(0x8893,0x8894,0x8895,0x8899,0x889a,0x889b,0x889e,0x889f,0x88a2,0x88a3,0x88a4);
    yield {call:'mask-sprite',address:0x88a4,handle:state[7],mode:1,color:65535,x:state[29],y:state[28]};
    yield* emit(0x88a7,0x88ab,0x88ac);yield {call:'handle-address',address:0x88ac,handle:state[8]};
    yield* emit(0x88af,0x88b0,0x88b1,0x88b5,0x88b6,0x88b7,0x88ba,0x88bb,0x88bf,0x88c0);
    yield {call:'mask-sprite',address:0x88c0,handle:state[8],mode:3,color:state[9],x:state[29],y:state[28]};
    yield* emit(0x88c3);state[1]=previous;yield* emit(0x88c7,0x8842);state[0]=(state[0]+1)&65535;yield* emit(0x8846);
  }
}
