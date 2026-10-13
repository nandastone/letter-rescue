"use strict";
// Resident 70E8 intrinsic instruction work, driven by modeled block decisions.
// Callee work is separate; unsupported arena growth is rejected explicitly.
class OriginalMemoryResizeWork {
  static resize(memory,block,payload){
    const heap=memory.heap,needed=heap.required(payload),flags=block.flags,entries={};
    const run=(first,last=first)=>{
      if(!OriginalResizeInstructionAddresses.includes(first)||!OriginalResizeInstructionAddresses.includes(last))throw new Error("Unknown resize instruction boundary");
      for(const address of OriginalResizeInstructionAddresses)if(address>=first&&address<=last)entries[address]=(entries[address]||0)+1;
    };
    run(0x70e8,0x7102);run(0x7107,0x7126);
    if((block.size>>>4)<=(needed>>>4)){
      run(0x7128);
      if((block.size>>>4)===(needed>>>4)){
        run(0x712a,0x712c);if(block.size>=needed)run(0x712e);
      }
    }
    const grew=block.size<needed;
    if(grew){
      run(0x7197,0x71a3);
      for(let guard=0;guard<100000;guard++){
        run(0x71a4);block.flags=0;heap.coalesce(block);block.flags=flags;
        run(0x71a7,0x71ac);
        if((block.size>>>4)<=(needed>>>4)){
          run(0x71ae);if((block.size>>>4)===(needed>>>4))run(0x71b0,0x71b3);
        }
        if(block.size>=needed){run(0x71b5);break;}
        run(0x71b8,0x71ba);
        if(heap.next(block).flags!==0xc000)throw new Error("Resize pressure/arena-growth work is not reconstructed");
        run(0x71bc,0x71dd);block.flags=0x8000;const moved=heap.relocate(heap.next(block));block.flags=flags;
        run(0x71e0,0x71e6);
        if(!moved)throw new Error("Failed resize relocation work is not reconstructed");
      }
      if(block.size<needed)throw new Error("Resize work failed to terminate");
    }
    if(grew||block.size!==needed){
      run(0x7130,0x7137);
      if((block.size&15)<(needed&15))run(0x7139,0x713c);
      run(0x713d,0x713f);const remainder=block.size-needed;
      if(remainder<16)run(0x7141,0x7144);
      if(remainder<6)run(0x7146,0x714b);else run(0x714d,0x715d);
      run(0x7160,0x717d);block.flags=0;heap.reserve(block,payload,false);block.flags=flags;
    }else heap.search=block.address;
    run(0x717f,0x7196);
    const instructions=Object.values(entries).reduce((a,b)=>a+b,0);
    return {entries,instructions,cycles:instructions,address:block.address,bytes:payload};
  }
}

// Boundaries decoded from pinned DOS 1.1 executable, resident 70E8..7207.
const OriginalResizeInstructionAddresses = [28904, 28905, 28907, 28910, 28911, 28914, 28917, 28920, 28923, 28925, 28927, 28930, 28932, 28935, 28937, 28940, 28942, 28944, 28946, 28948, 28949, 28952, 28955, 28957, 28960, 28962, 28964, 28966, 28968, 28970, 28972, 28974, 28976, 28979, 28981, 28983, 28985, 28988, 28989, 28991, 28993, 28996, 28998, 29000, 29003, 29005, 29007, 29009, 29011, 29013, 29016, 29020, 29021, 29024, 29026, 29028, 29031, 29034, 29036, 29039, 29041, 29043, 29045, 29048, 29050, 29053, 29055, 29056, 29061, 29065, 29069, 29072, 29074, 29075, 29077, 29078, 29079, 29080, 29081, 29084, 29087, 29090, 29091, 29092, 29095, 29097, 29100, 29102, 29104, 29107, 29109, 29112, 29114, 29116, 29118, 29122, 29126, 29127, 29128, 29129, 29130, 29132, 29134, 29137, 29139, 29141, 29143, 29145, 29147, 29149, 29152, 29153, 29154, 29155, 29156, 29158, 29160, 29163, 29165, 29168, 29169, 29171, 29173, 29174, 29175, 29178, 29179, 29180, 29181, 29184, 29186, 29187, 29188, 29190];
