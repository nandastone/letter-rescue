"use strict";
// Intrinsic guest work for the original resource routines. External callees
// and CPU/PIC scheduling remain separate components.
class OriginalResourceWork {
  static entry({cachedHandle=0,state=0,segment=0}){
    if([cachedHandle,state,segment].some(v=>!Number.isInteger(v)||v<0||v>65535))throw new Error("Invalid original cache entry");
    if(cachedHandle&&(state&0x200))throw new Error("EMS cache entry is not reconstructed");
    const resident=!!(cachedHandle&&((state&15)||segment)),entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x7a30,0x7a31,0x7a34,0x7a37,0x7a38,0x7a3d,0x7a40,0x7a42]);
    if(cachedHandle){
      add([0x7a44,0x7a45,0x7a46,0x7a47,0x7a4a,0x7a4c]);
      if(resident)add([0x7a4e,0x7a4f,0x7a50,0x7a53,0x7a54,0x7a55,0x7a56]);
    }
    if(!resident)add([0x7a58,0x7a5b,0x7a5d]);
    add([0x7a60,0x7a61,0x7a64,0x7a65]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);return {entries,instructions,cycles:instructions,resident};
  }
  static entryMemory(input){
    const work=this.entry(input),merge=call=>{for(const [a,n] of Object.entries(call.entries))work.entries[a]=(work.entries[a]||0)+n;work.instructions+=call.instructions;work.cycles+=call.cycles;};
    work.input={...input};
    if(input.cachedHandle){
      const address=OriginalMemoryWork.address({handle:input.cachedHandle,...input});merge(address);
      work.state=address.state;work.address=address.address;
      if(work.resident){const length=OriginalMemoryWork.length({handle:input.cachedHandle,...input,state:address.state});merge(length);work.bytes=length.bytes;}
    }
    return work;
  }
  // Resident 6628 returns an address without changing the handle's age/flags.
  static handleAddress({handle=0,state=0,segment=0}){
    if([handle,state,segment].some(v=>!Number.isInteger(v)||v<0||v>65535))throw new Error("Invalid original handle address input");
    const entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x6628,0x6629,0x662b,0x662e,0x6630]);let ax=0,dx=0;
    if(handle){
      add([0x6632,0x6635,0x6638]);
      if(!(state&0x200)){
        add([0x663a,0x663d,0x663f,0x6641]);ax=state&15;dx=segment;
        if(ax||dx){add([0x6643,0x6646]);ax+=6;}
      }else add([0x664c,0x664e,0x664f]);
    }else add([0x664c,0x664e,0x664f]);
    add([0x6648,0x6649]);const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,address:16*dx+ax,ax,dx};
  }
  // Resident 7688 only; the lookup/entry/allocation/read/copy callees report
  // their own work. Retryable read errors are not part of this model yet.
  static direct({found=true,cached=false,allocated=true,readError=false}={}){
    const entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x7688,0x7689,0x768b,0x768e,0x768f,0x7690,0x7691,0x7693,0x7696,0x7699,0x769c,0x769e,0x76a1,0x76a4]);
    if(found){
      add([0x76a6,0x76a9,0x76ac,0x76af,0x76b0,0x76b3,0x76b6,0x76b7,0x76bc,0x76bd,0x76be,0x76bf,0x76c2,0x76c5,0x76c8,0x76c9,0x76cc,0x76cd,0x76cf]);
      if(allocated){
        add([0x76d1]);
        if(cached)add([0x76d3,0x76d6,0x76d7,0x76d8,0x76d9,0x76da,0x76dd,0x76de,0x76df,0x76e2,0x76e3,0x76e4,0x76e5]);
        else{
          add([0x76f6,0x76f9,0x76fb,0x76fe,0x7701,0x7703]);
          if(readError)add([0x7705,0x7707,0x7709,0x770a,0x770d,0x7710,0x7711,0x7712,0x7713,0x7716]);
        }
      }
    }
    add([0x76e8,0x76eb,0x76ed,0x76ee,0x76ef,0x76f0,0x76f2,0x76f3]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,action:!found||!allocated?'none':cached?'copy':'read',releaseAfterError:found&&allocated&&!cached&&readError};
  }
  // Resident 7A66 and its 7A30 callee. Allocation/read error recovery is outside
  // this successful-load path; observers must fail if those branches occur.
  static cache({cachedHandle=0,state=0,segment=0,directoryFlags=0}){
    if([cachedHandle,state,segment].some(v=>!Number.isInteger(v)||v<0||v>65535)||!Number.isInteger(directoryFlags)||directoryFlags<0||directoryFlags>255)throw new Error("Invalid original cache state");
    if(cachedHandle&&(state&0x200))throw new Error("EMS cache work is not reconstructed");
    const resident=!!(cachedHandle&&((state&15)||segment)),entries={},add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x7a66,0x7a67,0x7a6a,0x7a6d,0x7a6e,0x7a73,0x7a75]);
    const entry=this.entry({cachedHandle,state,segment});for(const [a,n] of Object.entries(entry.entries))entries[a]=(entries[a]||0)+n;
    add([0x7a78,0x7a7a]);
    if(!resident){
      add([0x7a7c,0x7a7f]);
      if(cachedHandle)add([0x7a81,0x7a82,0x7a83,0x7a84,0x7a85,0x7a88,0x7a89]);
      else add([0x7a8d,0x7a8e,0x7a8f,0x7a90,0x7a93,0x7a95]);
      add([0x7a97,0x7a9a,0x7a9b,0x7a9c,0x7a9f,0x7aa0,0x7aa2,0x7aa5,0x7aa8,0x7aab,0x7aae,0x7ab1,0x7ab3,0x7ab5,0x7ab7,0x7abc,0x7abf,0x7ac2]);
      if(!cachedHandle){
        add([0x7ac4,0x7ac8]);
        if(directoryFlags&0x80)add([0x7aca,0x7acb,0x7acc,0x7acf,0x7ad0,0x7ad1]);
        add([0x7ad4,0x7ad8]);
        if(directoryFlags&0x40)add([0x7ada,0x7adb,0x7adc]);
      }
    }
    add([0x7adf,0x7ae0,0x7ae3,0x7ae4,0x7ae5]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,action:resident?'cached':cachedHandle?'reload':'load',promote:!cachedHandle&&!!(directoryFlags&0x80),discardable:!cachedHandle&&!!(directoryFlags&0x40)};
  }
  static lookup({catalogs,tag,id,builtins=[{tag:'FONT',id:0},{tag:'CURS',id:0}]}){
    const code=s=>{
      if(typeof s!=='string'||!s.length||s.length>4||Array.from(s).some(c=>c.charCodeAt(0)>127))throw new Error("Invalid original resource type");
      return Array.from(s).reduce((v,c)=>v*256+c.charCodeAt(0),0);
    },signed=v=>(v&65535)<<16>>16;
    if(!Number.isInteger(id)||id<0||id>65535)throw new Error("Invalid original resource ID");
    const value=code(tag),high=signed(value/65536),low=signed(value);
    const entries={},handleCalls=[],add=list=>{for(const a of list)entries[a]=(entries[a]||0)+1;};
    add([0x7bc9,0x7bca,0x7bcc,0x7bcf,0x7bd0,0x7bd1,0x7bd4,0x7bd7,0x7bda]);
    const finish=result=>{add([0x7c4f,0x7c51,0x7c52]);const instructions=Object.values(entries).reduce((a,b)=>a+b,0);return {entries,instructions,cycles:instructions,result,handleCalls};};
    for(const catalog of catalogs){
      handleCalls.push(catalog.handle);
      add([0x7bdd,0x7bdf,0x7be1,0x7be2,0x7be3,0x7be6,0x7be7,0x7be9,0x7bec]);
      if(!catalog.types.length)continue;
      add([0x7bee,0x7bef,0x7bf2,0x7bf4,0x7bf7]);
      let lower=0,upper=catalog.types.length+1,type=null;
      for(;;){
        add([0x7bf9,0x7bfb,0x7bfe,0x7c00,0x7c02]);
        const middle=(lower+upper)>>1;if(middle===lower)break;
        const candidate=catalog.types[middle-1],other=code(candidate.tag),otherHigh=signed(other/65536),otherLow=signed(other);
        add([0x7c04,0x7c06,0x7c08,0x7c0a,0x7c0c,0x7c0f]);
        if(high>otherHigh){add([0x7c72,0x7c73]);lower=middle;continue;}
        add([0x7c11]);
        if(high<otherHigh){add([0x7c6d,0x7c70]);upper=middle;continue;}
        add([0x7c13,0x7c16]);
        if(low<otherLow){add([0x7c6d,0x7c70]);upper=middle;continue;}
        add([0x7c18]);
        if(low>otherLow){add([0x7c72,0x7c73]);lower=middle;continue;}
        type=candidate;break;
      }
      if(!type)continue;
      add([0x7c1a,0x7c1d,0x7c20,0x7c22]);if(!type.ids.length)continue;
      add([0x7c24,0x7c25,0x7c28,0x7c2a]);lower=0;upper=type.ids.length+1;
      for(;;){
        add([0x7c2d,0x7c2f,0x7c32,0x7c34,0x7c36]);
        const middle=(lower+upper)>>1;if(middle===lower)break;
        add([0x7c38,0x7c3a,0x7c3c,0x7c3e,0x7c40,0x7c42,0x7c44,0x7c47]);
        if(signed(id)<signed(type.ids[middle-1])){add([0x7c65,0x7c68]);upper=middle;continue;}
        add([0x7c49]);
        if(signed(id)>signed(type.ids[middle-1])){add([0x7c6a,0x7c6b]);lower=middle;continue;}
        add([0x7c4b,0x7c4e]);
        return finish({catalogHandle:catalog.handle,tag,id,index:middle-1,entryOffset:80+type.relative+2+(middle-1)*11});
      }
    }
    add([0x7bdd,0x7bdf,0x7c53,0x7c56,0x7c58,0x7c5b,0x7c5e,0x7c60,0x7c63]);
    if(builtins.length!==2)throw new Error("Original built-in table has two entries");
    for(let i=0;i<builtins.length;i++){
      const candidate=builtins[i],other=code(candidate.tag);
      add([0x7c75,0x7c78,0x7c7c,0x7c7e,0x7c80]);if((other&65535)!==(value&65535))continue;
      add([0x7c82,0x7c85]);if((other>>>16)!==(value>>>16))continue;
      add([0x7c87,0x7c8a]);if(candidate.id!==id)continue;
      add([0x7c8c,0x7c8f,0x7c92,0x7c93]);
      return finish({catalogHandle:0x2055,tag,id,index:i,builtin:true,entryOffset:14+i*15});
    }
    add([0x7c75,0x7c78,0x7c7c]);return finish(null);
  }
  // Resident 794C: open a catalog's file and close files on another volume
  // of the same drive. File-list entries are ordinary model state.
  static open({catalogs,selected,openResult}){
    const files=catalogs.map(c=>({...c})),target=files.find(c=>c.handle===selected);
    if(selected!==0x2055&&!target)throw new Error("Unknown original file catalog");
    const entries={},add=(list,n=1)=>{for(const a of list)entries[a]=(entries[a]||0)+n;};
    add([0x794c,0x794d,0x794e,0x7951,0x7954,0x7959,0x795b,0x795f]);
    let stringIterations=0;const opens=[],closes=[];
    if(selected!==0x2055){
      add([0x7961,0x7964]);
      if(!target.fileHandle){
        if(!Number.isInteger(openResult)||openResult<=0||openResult>65535)throw new Error("Successful DOS file-open result required");
        add([0x7966,0x7969,0x796d,0x796f,0x7971,0x7973]);
        target.fileHandle=openResult;opens.push(target.filename);
      }
      add([0x7976,0x7977,0x7978]);
      for(const other of files){
        add([0x797b,0x797e,0x7980,0x7982,0x7983,0x7984,0x7985,0x7988,0x7989,0x798b,0x798d]);
        if(other.handle===selected)continue;
        add([0x798f,0x7992,0x7996]);
        if(target.filename[0]!==other.filename[0])continue;
        add([0x7998,0x799b]);
        if(target.volume){
          add([0x799d,0x799e,0x799f,0x79a2]);
          let equal=true;
          for(let i=0;;i++){
            add([0x79a5,0x79a6,0x79a7]);stringIterations+=2;
            const a=target.volume.charCodeAt(i)||0,b=other.volume.charCodeAt(i)||0;
            if(a!==b){equal=false;break;}
            add([0x79a9,0x79ab]);if(!a)break;
          }
          add([0x79ad,0x79ae,0x79af]);if(equal)continue;
        }
        add([0x79b1,0x79b3,0x79b7]);
        if(other.fileHandle){add([0x79b9,0x79bb,0x79bd,0x79bf]);closes.push(other.fileHandle);other.fileHandle=0;}
      }
      add([0x797b,0x797e,0x7980]);
    }
    add([0x79ca,0x79cd,0x79ce,0x79cf]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,stringIterations,cycles:instructions+stringIterations,catalogs:files,opens,closes};
  }
  // Pinned DOSBox Pure dos.cpp modify_cycles. Budgets are explicit component
  // inputs until the independent CPU/PIC scheduler can supply them.
  static dosTransfer(bytes,cycles,io=0){
    if(!Number.isInteger(bytes)||bytes<0||bytes>65535||!Number.isInteger(cycles)||cycles<-2147483648||cycles>2147483647||!Number.isSafeInteger(io))throw new Error("Invalid DOS transfer state");
    const complete=4*bytes+5<cycles;
    const ioDebit=complete?4*bytes:cycles;
    if(!Number.isSafeInteger(io+ioDebit))throw new Error("DOS I/O accumulator exceeds exact integer range");
    return {cycles:complete?cycles-4*bytes:5,io:io+ioDebit,ioDebit};
  }
  static read({payload,checksum,directoryFlags=0}){
    if(!payload||payload.length>0xfffff||Array.from(payload).some(v=>!Number.isInteger(v)||v<0||v>255))throw new Error("Invalid original resource bytes");
    if(!Number.isInteger(checksum)||checksum<0||checksum>255)throw new Error("Invalid original checksum byte");
    const entries={},add=(list,n=1)=>{if(n)for(const a of list)entries[a]=(entries[a]||0)+n;};
    add([0x7aef,0x7af0,0x7af2,0x7af5,0x7af9,0x7afc,0x7aff,0x7b02,0x7b05,0x7b08,0x7b0b,0x7b0f]);
    const reads=[];let stringIterations=0;
    if(directoryFlags&0x10){
      add([0x7b11,0x7b12,0x7b13,0x7b16,0x7b17,0x7b18,0x7b19,0x7b1a,0x7b1b,0x7b1e,0x7b20]);
    }else{
      if(payload.length&&((checksum+Array.from(payload).reduce((a,b)=>a+b,0))&255)!==255)throw new Error("Original resource checksum mismatch");
      add([0x7b23,0x7b26,0x7b28,0x7b2d,0x7b30,0x7b33,0x7b35,0x7b38,0x7b3a,0x7b3c,0x7b3f,0x7b42,0x7b43,0x7b44,0x7b46,0x7b48,0x7b4a,0x7b4c,0x7b4e]);
      reads.push(1);let remaining=payload.length;
      for(;;){
        add([0x7b51,0x7b53,0x7b56,0x7b58,0x7b5a,0x7b5c,0x7b5e,0x7b60,0x7b63,0x7b66]);
        if((remaining&65535)<=0xfff0)add([0x7b68,0x7b6c]);
        if(remaining>0xfff0)add([0x7b6e]);
        const count=Math.min(remaining,0xfff0);reads.push(count);
        add([0x7b71,0x7b73,0x7b75,0x7b77,0x7b79,0x7b7b,0x7b7d]);
        if(!count)break;
        add([0x7b7f]);add([0x7b80,0x7b81,0x7b83],count);stringIterations+=count;
        add([0x7b85,0x7b88,0x7b89,0x7b8b,0x7b8e,0x7b92,0x7b95,0x7b98]);
        remaining-=count;
        if(!remaining){add([0x7ba7,0x7baa,0x7bac,0x7bae,0x7bb0]);break;}
        // The canonical low offset is at most 15; adding an FFF0-byte chunk
        // cannot overflow SI. The next pass normalizes its paragraph offset.
        add([0x7b9a,0x7b9c]);
      }
    }
    add([0x7bb1,0x7bb4,0x7bb6,0x7bb7]);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,stringIterations,cycles:instructions+stringIterations,reads,memoryCopyBytes:directoryFlags&0x10?payload.length:0};
  }
}
