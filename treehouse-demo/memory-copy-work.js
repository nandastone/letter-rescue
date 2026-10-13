"use strict";
// Resident 6C18: segmented memmove, including backward overlapping copies.
// The logical REP operations are scheduled separately by the CPU slice model.
class OriginalMemoryCopyWork {
  static copy({from,to,bytes}) {
    if([from,to,bytes].some(n=>!Number.isInteger(n)||n<0||n>0xfffff)||from+bytes>0x100000||to+bytes>0x100000)throw new Error("Unsupported original copy outside conventional address range");
    const entries={},repeats=[];let stringIterations=0;
    const run=(first,last=first)=>{
      if(!OriginalHeapInstructionAddresses.includes(first)||!OriginalHeapInstructionAddresses.includes(last))throw new Error("Unknown copy instruction boundary");
      for(const address of OriginalHeapInstructionAddresses)if(address>=first&&address<=last)entries[address]=(entries[address]||0)+1;
    };
    run(0x6c18,0x6c4a);
    if((to>>>4)<=(from>>>4)){
      run(0x6c4c);if((to>>>4)===(from>>>4))run(0x6c4e,0x6c50);
    }
    const backward=to>from&&to<from+bytes;
    if(to>from){
      run(0x6ca4,0x6cbd);const end=from+bytes;
      if((to>>>4)<=(end>>>4)){
        run(0x6cbf);if((to>>>4)===(end>>>4))run(0x6cc1,0x6cc3);
      }
    }
    let remaining=bytes;
    if(backward)run(0x6cc5,0x6cd8);else run(0x6c52);
    const limit=backward?0xffe0:0xfff0;
    for(;;){
      run(backward?0x6cd9:0x6c54,backward?0x6ce4:0x6c5f);
      const chunk=Math.min(remaining,limit);
      if(remaining<limit){
        run(backward?0x6ce6:0x6c61,backward?0x6ce9:0x6c64);
        if(!chunk)break;
        run(backward?0x6ceb:0x6c66,backward?0x6cee:0x6c69);
      }
      run(backward?0x6cf1:0x6c6c,backward?0x6d25:0x6c92);
      repeats.push({address:backward?0x6d23:0x6c90,iterations:chunk>>>1});stringIterations+=chunk>>>1;
      if(chunk&1){run(backward?0x6d27:0x6c94,backward?0x6d2a:0x6c95);stringIterations++;}
      remaining-=chunk;
    }
    run(0x6c97,0x6ca1);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,stringIterations,repeats,cycles:instructions+stringIterations,backward,address:to};
  }
}
