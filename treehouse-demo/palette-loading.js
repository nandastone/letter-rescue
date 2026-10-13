"use strict";
// Main 6416: retain the SHPL, assign its VGA palette banks, then activate it.
// Hardware RGB upload belongs to the renderer; source ownership stays here.
class OriginalPaletteLoading {
  constructor(catalogs){this.catalogs=catalogs;this.memory=catalogs.memory;}
  load(id,banks){
    if(!Number.isInteger(banks)||banks<=0||banks>65535)throw new Error("Explicit original VGA palette banks required");
    const found=this.catalogs.resolve('SHPL',id);if(!found)throw new Error("Missing original palette");
    const handle=this.catalogs.loadSource(found.catalog.handle,'SHPL',id),m=this.memory;
    m.retain(handle);m.address(handle);
    const payload=m.resourcePayloads.get(handle);
    if(!payload||payload.length<7)throw new Error("Truncated original palette");
    payload[4]=banks&255;payload[5]=banks>>>8;
    // E42E only acquires banks when the caller left the word at zero. Main
    // 6416 has already supplied an explicit mask, so activation restores flags.
    const saved=m.handle(handle).state;m.address(handle);m.lock(handle);m.flags(handle,saved);
    return handle;
  }
}
