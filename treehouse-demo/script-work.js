"use strict";
// Main BDA0 interpreter work. Rendering, sound and callbacks yield to the same
// execution clock; their work and state changes must be supplied by the caller.
class OriginalScriptWork {
  static *instructions(...addresses){for(const address of addresses)yield 'main:'+address.toString(16).padStart(4,'0');}
  static *run(state,{readTick}){
    const m=state.memory,v=new DataView(m.buffer,m.byteOffset,m.byteLength),emit=this.instructions;
    const word=offset=>v.getUint16(offset,true),put=(offset,value)=>v.setUint16(offset,value&65535,true);
    const dword=offset=>v.getUint32(offset,true),put32=(offset,value)=>v.setUint32(offset,value>>>0,true);
    const origin=word(0x4e),codeAt=offset=>{
      if(state.readCode)return state.readCode((word(0x4e)+offset)&65535);
      const index=((word(0x4e)-origin)&65535)+offset;if(index>=state.code.length)throw new Error('Script byte window exhausted');return state.code[index];
    };
    const operand=offset=>{
      // A 16-bit effective offset wraps before a word load. The second byte
      // is physically adjacent, even when the first is at segment offset FFFF.
      if(state.readCode){const at=(word(0x4e)+offset)&65535;return state.readCode(at)|(state.readCode(at+1)<<8);}
      return codeAt(offset)|(codeAt(offset+1)<<8);
    },advance=n=>put(0x4e,word(0x4e)+n);
    const context=state.context;let result=0;
    yield* emit(0xbda0,0xbda1,0xbda3,0xbda7,0xbda8,0xbda9,0xbdae,0xbdb1,0xbdb4,0xbdb7);state.context=state.instance;
    const immediate=function*(opcode){
      yield* emit(0xc36b,0xbfd4,0xbfd7,0xbfda,0xbfdd,0xbfe0);
      if((opcode&0xfc)===0x10){
        const offset=0x60+(opcode&3)*4;
        yield* emit(0xbfe5,0xbfe8,0xbfeb,0xbfee,0xbff0,0xbff3,0xbff5,0xbff7,0xbffa,0xbffd,0xc000);
        if(dword(offset)){yield* emit(0xc005,0xc008,0xc00b,0xc00f,0xc012,0xc014,0xc016,0xc019);yield {call:'script-callback',index:opcode&3,argument:operand(1),state};}
        else yield* emit(0xc002);
        yield* emit(0xc01c,0xc01f);advance(3);yield* emit(0xc023);
      }else{
        yield* emit(0xbfe2,0xc026,0xc029,0xc02c,0xc02f,0xc032);
        if((opcode&0xfc)===0x14){
          const offset=0x70+(opcode&3)*2;
          yield* emit(0xc037,0xc03a,0xc03d,0xc040,0xc042,0xc045,0xc047,0xc04a,0xc04e);
          if(word(offset)){
            yield* emit(0xc053,0xc056,0xc058,0xc05b);put(offset,word(offset)-1);yield* emit(0xc05e,0xc062);
            if(word(offset)){yield* emit(0xc067,0xc06a,0xc06e,0xc071,0xc074,0xc077);advance(3+operand(3));yield* emit(0xc07a);}
            else{yield* emit(0xc064,0xc07d,0xc080);advance(5);}
            yield* emit(0xc084);
          }else{
            yield* emit(0xc050,0xc087,0xc08a,0xc08e,0xc091,0xc093,0xc096);put(offset,operand(1));
            yield* emit(0xc099,0xc09c,0xc0a0,0xc0a3,0xc0a6,0xc0a9);advance(3+operand(3));
          }
          yield* emit(0xc0ac);
        }else{
          const slot=opcode&15,offset=0x78+slot*0x22,high=opcode&0xf0;
          yield* emit(0xc034,0xc0af,0xc0b2,0xc0b5,0xc0b8,0xc0bb,0xc0be,0xc0c0,0xc0c3,0xc0c6,0xc0c9,0xc0cc,0xc0cf,0xc0d2,0xc320,0xc323);
          if(high===0xc0)yield* emit(0xc325);
          else{
            yield* emit(0xc328);
            if(high<0xc0){
              yield* emit(0xc32d,0xc330);
              if(high===0x90)yield* emit(0xc332);
              else{yield* emit(0xc335,0xc338);if(high===0xa0)yield* emit(0xc33a);else{yield* emit(0xc33d,0xc340);if(high===0xb0)yield* emit(0xc342);else{yield* emit(0xc345,0xc315,0xc31a);return false;}}}
            }else{
              yield* emit(0xc32a,0xc348,0xc34b);
              if(high===0xd0)yield* emit(0xc34d);
              else{yield* emit(0xc350,0xc353);if(high===0xe0)yield* emit(0xc355);else{yield* emit(0xc358,0xc35b);if(high===0xf0)yield* emit(0xc35d);else{yield* emit(0xc360,0xc315,0xc31a);return false;}}}
            }
          }
          if(high===0x90){
            const old=word(offset+6);yield* emit(0xc0d5,0xc0d8,0xc0db,0xc0de,0xc0e1,0xc0e5,0xc0e8);put(offset+6,old&operand(1));
            yield* emit(0xc0eb,0xc0ee,0xc0f2,0xc0f5);put(offset+6,word(offset+6)|operand(3));const changed=old^word(offset+6);
            yield* emit(0xc0f8,0xc0fb,0xc0fe,0xc101,0xc103);
            if(changed&0xf0){yield* emit(0xc108,0xc10b);m[offset+8]=0;}else yield* emit(0xc105);
            yield* emit(0xc10f,0xc112,0xc115,0xc118,0xc11a);
            if(changed&0xf00){yield* emit(0xc11f,0xc122);m[offset+9]=0;}else yield* emit(0xc11c);
            yield* emit(0xc126,0xc129);advance(5);yield* emit(0xc12d);
          }else if(high===0xa0||high===0xb0){
            const a=high===0xa0;
            yield* emit(...(a?[0xc130,0xc133,0xc136]:[0xc170,0xc173,0xc176]));yield {call:'slot-bounds',slot,state};
            yield* emit(...(a?[0xc139,0xc13c,0xc140,0xc142,0xc145,0xc148]:[0xc179,0xc17c,0xc180,0xc183,0xc188]));
            put32(offset+0xa,(a?dword(offset+0xa):0)+(operand(1)<<16));
            yield* emit(...(a?[0xc14b,0xc14e,0xc152,0xc154,0xc157,0xc15a]:[0xc18b,0xc18e,0xc192,0xc195,0xc19a]));
            put32(offset+0xe,(a?dword(offset+0xe):0)+(operand(3)<<16));
            yield* emit(...(a?[0xc15d,0xc160,0xc163]:[0xc19d,0xc1a0,0xc1a3]));yield {call:'slot-bounds',slot,state};
            yield* emit(...(a?[0xc166,0xc169]:[0xc1a6,0xc1a9]));advance(5);yield* emit(a?0xc16d:0xc1ad);
          }else if(high===0xc0){
            yield* emit(0xc1b0,0xc1b3,0xc1b6);yield {call:'slot-bounds',slot,state};
            yield* emit(0xc1b9,0xc1bc,0xc1c0,0xc1c3);put(offset+4,operand(3));
            yield* emit(0xc1c6,0xc1c9,0xc1cd,0xc1d0);put(offset+2,operand(1));yield* emit(0xc1d3,0xc1d6);put(offset,operand(1));yield* emit(0xc1d8,0xc1db);
            if(operand(1)){yield* emit(0xc1e0,0xc1e3,0xc1e6);yield {call:'slot-bounds',slot,state};yield* emit(0xc1e9);}
            else{yield* emit(0xc1dd,0xc1ec,0xc1ef);yield {call:'slot-reset',slot,state};}
            yield* emit(0xc1f2,0xc1f5);advance(5);yield* emit(0xc1f9);
          }else if(high===0xd0||high===0xe0){
            const delta=high===0xd0?0:0x32,field=high===0xd0?0x12:0x1a;
            yield* emit(...[0xc1fc,0xc1ff,0xc203,0xc207,0xc20a,0xc20d].map(a=>a+delta));put(offset+field,operand(1));put(offset+field+2,operand(3));
            yield* emit(...[0xc210,0xc213,0xc217,0xc21b,0xc21e,0xc221].map(a=>a+delta));put(offset+field+4,operand(5));put(offset+field+6,operand(7));
            yield* emit(...[0xc224,0xc227].map(a=>a+delta));advance(9);yield* emit(0xc22b+delta);
          }else throw new Error('Direct slot draw work is not reconstructed');
        }
      }
      yield* emit(0xc363,0xc386);return true;
    };
    // Preserve the original separate unsigned high/low comparisons. Timer reads
    // happen at the original load instruction, not at interpreter entry.
    const deadline=function*(base){
      const a=base===0?[0xbdce,0xbdd1,0xbdd4,0xbdd7,0xbdda,0xbddd,0xbde0,0xbde4,0xbde8,0xbdea,0xbdec,0xbdef,0xbdf1,0xbdf4,0xbdf6,0xbdf8]:
        base===1?[0xbe03,0xbe06,0xbe09,0xbe0c,0xbe0f,0xbe12,0xbe15,0xbe19,0xbe1d,0xbe1f,0xbe21,0xbe24,0xbe26,0xbe29,0xbe2b,0xbe2d]:
        [0xbefa,0xbefd,0xbf00,0xbf03,0xbf06,0xbf09,0xbf0c,0xbf10,0xbf14,0xbf16,0xbf18,0xbf1b,0xbf1d,0xbf20,0xbf22,0xbf24];
      yield* emit(...a.slice(0,7));const low=readTick(a[6])&65535;
      yield* emit(a[7]);const high=readTick(a[7])>>>16;
      const due=(dword(0x5c)+word(0x5a))>>>0;
      yield* emit(a[8],a[9]);if((due>>>16)>high){yield* emit(a[10]);return false;}
      yield* emit(a[11]);if((due>>>16)<high){yield* emit(a[12]);return true;}
      yield* emit(a[13],a[14]);if((due&65535)>low){yield* emit(a[15]);return false;}return true;
    };
    for(;;){
    yield* emit(0xbdba,0xbdbd,0xbdc0,0xbdc3,0xbdc6,0xbdc9,0xbdcb,0xc366,0xc369);
    const opcode=codeAt(0);
    if(opcode>7){if(yield* immediate(opcode))continue;result=1;break;}
    yield* emit(0xc36e,0xc370,0xc371);
    if(opcode===0){
      if(yield* deadline(0)){yield* emit(0xbdfb);result=1;}yield* emit(0xbe00);
    }else if(opcode===1){
      if(yield* deadline(1)){
        yield* emit(0xbe30,0xbe33);yield {call:'frame-update',state};
        yield* emit(0xbe36);state.display_count=(state.display_count+1)&65535;
        yield* emit(0xbe3a,0xbe3d,0xbe41);
        if(word(0x52)){yield* emit(0xbe43);}
        else{
          yield* emit(0xbe46,0xbe49,0xbe4d,0xbe50);put(0x52,operand(1));
          yield* emit(0xbe53,0xbe56,0xbe5a,0xbe5d);put(0x5a,operand(3));
        }
        yield* emit(0xbe60,0xbe63);put(0x52,word(0x52)-1);yield* emit(0xbe66,0xbe6a);
        if(word(0x52)){yield* emit(0xbe6c);}else{yield* emit(0xbe6f,0xbe72);advance(5);}
      }
      yield* emit(0xbe76);
    }else if(opcode===2){
      yield* emit(0xbe79,0xbe7c,0xbe7f,0xbe82);
      if(!dword(0x52)){
        yield* emit(0xbe87,0xbe8a,0xbe8e,0xbe8f);const low=readTick(0xbe8f)&65535;
        yield* emit(0xbe93);const now=((readTick(0xbe93)&0xffff0000)|low)>>>0,amount=(operand(1)<<16)>>16;
        yield* emit(0xbe97,0xbe99,0xbe9b,0xbe9e,0xbea1);put32(0x52,now+amount);
        yield* emit(0xbea4,0xbea7,0xbeaa,0xbead);
        if(dword(0x5c)){yield* emit(0xbeb2,0xbeb5,0xbeb9,0xbeba,0xbebd,0xbec0);put32(0x5c,dword(0x5c)+amount);}
        else yield* emit(0xbeaf);
        yield* emit(0xbec3);
      }else{
        yield* emit(0xbe84,0xbec6);const low=readTick(0xbec6)&65535;
        yield* emit(0xbec9);const high=readTick(0xbec9)>>>16;
        yield* emit(0xbecd,0xbed0,0xbed3);let due=false;
        if(word(0x54)>high)yield* emit(0xbed5);
        else{
          yield* emit(0xbed8);
          if(word(0x54)<high){yield* emit(0xbeda);due=true;}
          else {yield* emit(0xbedd,0xbee0);due=word(0x52)<=low;if(!due)yield* emit(0xbee2);}
        }
        if(due){yield* emit(0xbee5,0xbee8,0xbeea,0xbeed);put32(0x52,0);yield* emit(0xbef0,0xbef3);advance(3);}
      }
      yield* emit(0xbef7);
    }else if(opcode===3){
      if(yield* deadline(3)){
        yield* emit(0xbf27,0xbf2c);
        if(state.sound_enabled){yield* emit(0xbf31,0xbf34,0xbf38);yield {call:'sound-start',id:operand(1)};}
        else yield* emit(0xbf2e);
        yield* emit(0xbf3d,0xbf40);advance(3);
      }
      yield* emit(0xbf44);
    }else if(opcode===4){
      yield* emit(0xbf47,0xbf4a,0xbf4e);yield {call:'sound-stop',id:operand(1)};
      yield* emit(0xbf53,0xbf56);advance(3);yield* emit(0xbf5a);
    }else if(opcode===5){
      yield* emit(0xbf5d,0xbf60,0xbf64);const active=yield {call:'sound-status',id:operand(1)};
      yield* emit(0xbf69,0xbf6c);if(active)yield* emit(0xbf6e);else{yield* emit(0xbf71,0xbf74);advance(3);}yield* emit(0xbf78);
    }else if(opcode===6){
      yield* emit(0xbf7b,0xbf7e,0xbf82);
      if(m[0x52])yield* emit(0xbf84);else{yield* emit(0xbf87,0xbf8a,0xbf8e,0xbf91);m[0x52]=codeAt(1);}
      yield* emit(0xbf94,0xbf99);let advanceCue=!state.cue;
      if(!state.cue)yield* emit(0xbf9b);
      else{yield* emit(0xbf9e,0xbfa1,0xbfa4,0xbfa7);advanceCue=m[0x52]<=state.cue;if(!advanceCue)yield* emit(0xbfa9);}
      if(advanceCue){yield* emit(0xbfac,0xbfaf);m[0x52]=0;yield* emit(0xbfb3,0xbfb6);advance(2);}yield* emit(0xbfba);
    }else if(opcode===7){
      yield* emit(0xbfbd,0xbfc0);yield {call:'scene-compose',state};
      yield* emit(0xbfc3,0xbfc6);put(0x56,1);yield* emit(0xbfcb,0xbfce);advance(1);yield* emit(0xbfd1);
    }
    break;
    }
    yield* emit(0xc389,0xc38c);state.context=context;
    yield* emit(0xc38f,0xc392,0xc395,0xc396,0xc397,0xc399,0xc39a);return result;
  }
}
