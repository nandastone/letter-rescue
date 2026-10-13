"use strict";
// Intrinsic resident wrappers. Allocator/address callees report their own work.
class OriginalMemoryWrapperWork {
  static result(addresses,extra={}){
    const entries={};for(const a of addresses)entries[a]=(entries[a]||0)+1;
    return {entries,instructions:addresses.length,cycles:addresses.length,...extra};
  }
  static allocateHandle({handle,blockAddress}){
    if(!Number.isInteger(handle)||handle<=0||handle>65531||!Number.isInteger(blockAddress)||blockAddress<=0||blockAddress>0xfffff)throw new Error("Handle allocation failure work is not reconstructed");
    return this.result([
      0x652a,0x652b,0x652d,0x652e,0x652f,
      0x6566,0x6567,0x6568,0x6569,0x656c,0x656f,0x6572,0x6573,0x6574,0x6575,0x6578,0x657b,0x657d,0x657f,0x6581,0x6583,0x6585,0x6588,0x6589,
      0x6532,0x6535,0x6536,0x6538,0x653a,0x653d,0x653f,0x6543,0x6546,0x654a,0x654d,0x6550,0x6551,0x6552,0x6553,0x6554
    ],{handle,state:(blockAddress&15)|0x1f0,segment:blockAddress>>>4,blockFlags:0xc000});
  }
  static farAllocation(){return this.result([0x6e8d,0x6e92,0x6e96,0x6e99,0x6e9e,0x6ea2]);}
  static lock(input){
    const address=OriginalMemoryWork.address(input),list=[0x6510,0x6511,0x6513,0x6516,0x6517,0x6518,0x651b,0x651d,0x651f];
    if(address.address)list.push(0x6521);list.push(0x6526,0x6527);
    return this.result(list,{handle:input.handle,address:address.address,state:address.address?address.state|0x81f0:address.state,addressWork:address});
  }
  static discardable({handle,state=0}){
    OriginalMemoryWork.input({handle,state});
    const list=[0x659e,0x659f,0x65a1,0x65a4,0x65a6];if(handle)list.push(0x65a8);list.push(0x65ad,0x65ae,0x65af);
    return this.result(list,{handle,state:handle?state|0x4000:state});
  }
}
