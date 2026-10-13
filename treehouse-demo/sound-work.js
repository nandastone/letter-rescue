"use strict";
// Resident E964: variable-width delta PCM decoder and its intrinsic work.
// Counts derive from compressed bytes, never recorded timing schedules.
class OriginalSoundWork {
  static preparation({action,count,packedBytes}) {
    if(!['prepared','missing','non-digital','uncompressed','decoded'].includes(action))throw new Error("Unsupported sound preparation work");
    const entries={},add=addresses=>{for(const a of addresses)entries[a]=(entries[a]||0)+1;};
    add([0xe6e6,0xe6e7,0xe6e9,0xe6ec,0xe6ed,0xe6ee,0xe6f1,0xe6f2,0xe6f3,0xe6f4,0xe6f7,0xe6fa]);
    if(action==='prepared')add([0xe6fc]);
    else {
      add([0xe6ff,0xe700,0xe701,0xe702,0xe705,0xe707,0xe70a,0xe70c]);
      if(action==='missing')add([0xe70e,0xe954,0xe956]);
      else {
        add([0xe711,0xe714,0xe718]);
        if(action==='non-digital')add([0xe71a]);
        else {
          add([0xe71d,0xe722,0xe727,0xe728,0xe729,0xe72a,0xe72d,0xe730,0xe733,0xe736,0xe739,0xe73c,0xe740,0xe741,0xe742]);
          if(action==='decoded'){
            if(!Number.isInteger(count)||count<1||count>65535||!Number.isInteger(packedBytes)||packedBytes<3||packedBytes>0xfffff)throw new Error("Invalid compressed preparation lengths");
            add([0xe744,0xe88e,0xe892,0xe894,0xe897,0xe89a,0xe89d,0xe89f]);
            if(packedBytes<65536)add([0xe8a1,0xe8a4]);
            if(count<packedBytes)add([0xe8a6,0xe8a9]);
            add([0xe8ac,0xe8af,0xe8b2,0xe8b5,0xe8b6,0xe8b9,0xe8bc,0xe8bd,0xe8be,0xe8bf,0xe8c0,0xe8c3,0xe8c5,
              0xe8ca,0xe8cb,0xe8cc,0xe8cd,0xe8d0,0xe8d2,0xe8d4,0xe8d7,0xe8da,0xe8dd,0xe8e0,0xe8e3,0xe8e4,0xe8e5,0xe8e8,0xe8eb,0xe8ec,0xe8ed,0xe8f0,0xe8f3,0xe8f6,0xe8f9,0xe8fc,0xe8ff,0xe900,0xe901,
              0xe904,0xe907,0xe90a,0xe90d,0xe910,0xe911,0xe912,0xe915,0xe918,0xe91d,0xe920,0xe924,0xe925,0xe928,0xe92b,0xe92e,0xe931,0xe932,0xe933,0xe934,0xe935,0xe938,0xe939,0xe93a,0xe93b,0xe93e]);
          }
          // Rate is within the bounds already checked by OriginalSoundLoading.
          add([0xe747,0xe74a,0xe74b,0xe74c,0xe74f,0xe751,0xe754,0xe756,0xe75a,0xe75c,0xe942,0xe945,0xe949,0xe94e,0xe950,0xe761,0xe763,0xe765]);
        }
      }
    }
    if(action!=='missing')add([0xe958]);
    add([0xe95b,0xe95c,0xe95d,0xe95f,0xe960]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions};
  }
  static decode(compressed) {
    if(compressed.length<3||Array.from(compressed).some(b=>!Number.isInteger(b)||b<0||b>255))throw new Error("Invalid original sound stream");
    const count=compressed[0]|compressed[1]<<8;
    if(!count)throw new Error("Empty original sound stream");
    const entries={},add=addresses=>{for(const a of addresses)entries[a]=(entries[a]||0)+1;};
    add([0xe964,0xe965,0xe967,0xe968,0xe969,0xe96a,0xe96b,0xe96e,0xe971,0xe972,0xe974,0xe975,0xe977,0xe979,0xe97a]);
    let value=compressed[2],bit=24,width=0;const pcm=[value];
    for(;;){
      add([0xe97b,0xe97d]);if(pcm.length>=count)break;
      add([0xe97f,0xe981,0xe983]);if(!width)add([0xe985]);
      let code=0;
      for(let n=width||3;n>0;n--){
        if(bit>=compressed.length*8)throw new Error("Truncated original sound bit stream");
        add([0xe987,0xe989,0xe98b,0xe98d,0xe98f]);
        const one=(compressed[bit>>>3]>>>(7-(bit&7)))&1;code=code*2+one;
        if(one)add([0xe991]);
        add([0xe993,0xe995,0xe998]);bit++;
      }
      add([0xe987,0xe989,0xe99a,0xe99c]);
      if(width){
        const marker=1<<(width-1);add([0xe99e,0xe9a0]);
        if(code===marker){width=0;add([0xe9ac,0xe9ae]);continue;}
        add([0xe9a2]);if(code>marker){add([0xe9a4]);code-=1<<width;}
        value=(value+code)&255;pcm.push(value);add([0xe9a6,0xe9a8,0xe9a9]);
      }else{
        add([0xe9b0,0xe9b3]);
        if(code===7){value=(value+128)&255;pcm.push(value);add([0xe9b5,0xe9b7,0xe9b8]);}
        else {width=code+2;add([0xe9ba,0xe9bc,0xe9be,0xe9c1,0xe9c3]);}
      }
    }
    add([0xe9c6,0xe9c7,0xe9c8,0xe9cb,0xe9ce,0xe9cf,0xe9d0,0xe9d2,0xe9d3]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0),stringIterations=count+2;
    return {pcm,consumedBytes:Math.ceil(bit/8),entries,instructions,stringIterations,cycles:instructions+stringIterations};
  }
}
