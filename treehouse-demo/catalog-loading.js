"use strict";
// Resident 7808: allocate the archive directory, link it into the loaded-file
// list, preload flagged resources, then release the catalog lock.
class OriginalCatalogLoading {
  constructor(memory,{files=[],lookup=0}={}){
    this.memory=memory;this.files=files.map(f=>({...f}));this.lookup=lookup;this.catalogs=new Map();
  }
  static directory(archive){
    const bytes=Uint8Array.from(archive),view=new DataView(bytes.buffer),word=at=>view.getUint16(at,true);
    if(bytes.length<8)throw new Error("Truncated original archive");
    const offset=view.getUint32(0,true),size=word(4);
    if(offset<6||size<2||offset+size!==bytes.length)throw new Error("Invalid original archive directory");
    const count=word(offset),records=[],types=[];
    if(2+6*count>size)throw new Error("Truncated original archive types");
    for(let i=0;i<count;i++){
      const at=offset+2+6*i,code=view.getUint32(at,true),relative=word(at+4),table=offset+relative;
      if(relative<2+6*count||relative+2>size)throw new Error("Invalid original resource table");
      const n=word(table),ids=[],tag=String.fromCharCode(code>>>24,(code>>>16)&255,(code>>>8)&255,code&255).replace(/^\0+|\0+$/g,'');
      if(relative+2+11*n>size)throw new Error("Truncated original resource table");
      for(let j=0;j<n;j++){
        const row=table+2+11*j,id=word(row),start=view.getUint32(row+2,true),length=word(row+6),flags=bytes[row+8];
        if(start<6||start+1+length>offset||word(row+9)!==0)throw new Error("Invalid original resource entry");
        const payload=bytes.slice(start+1,start+1+length);
        let sum=bytes[start];for(const value of payload)sum+=value;
        if((sum&255)!==255)throw new Error("Invalid original resource checksum");
        records.push({tag,id,offset:start,length,flags,handle:0,row:row-offset,payload});ids.push(id);
      }
      types.push({tag,relative,ids});
    }
    return {bytes:bytes.slice(offset),size,records,types};
  }
  open({archive,filename,volume,fileHandle}){
    if(typeof filename!=='string'||filename.length>=64||typeof volume!=='string'||volume.length>=12||!Number.isInteger(fileHandle)||fileHandle<0||fileHandle>65535)throw new Error("Invalid original archive file metadata");
    const directory=OriginalCatalogLoading.directory(archive),m=this.memory;
    const handle=m.allocateHandle(directory.size+80);m.lock(handle);
    const file={handle,fileHandle,volume,filename},loader=new OriginalResourceLoading(m,handle,{observeWork:false});
    const catalog={...directory,...file,previous:this.files[0]?.handle||0,loader};
    this.files.unshift(file);this.lookup=handle;this.catalogs.set(handle,catalog);
    // Opening an archive visits resource tables in their stored order.
    for(const entry of catalog.records)if(entry.flags&0x20)this.loadSource(handle,entry.tag,entry.id);
    m.unlock(handle);return handle;
  }
  loadSource(handle,tag,id){
    const catalog=this.catalogs.get(handle),entry=catalog?.records.find(e=>e.tag===tag&&e.id===id);
    if(!entry)throw new Error("Missing original catalog resource");
    entry.handle=catalog.loader.source(`${tag}:${id}`,entry.payload,entry.flags);
    const owner=this.memory.resourceOwners.get(entry.handle);if(owner)owner.entry=entry;
    return entry.handle;
  }
  loadShape(handle,id,paletteHandle){
    const catalog=this.catalogs.get(handle),entry=catalog?.records.find(e=>e.tag==='SHAP'&&e.id===id);
    if(!entry)throw new Error("Missing original catalog shape");
    if(!catalog.shapeLoader){
      catalog.shapeLoader=new OriginalShapeLoading(this.memory,handle,{observeWork:false});
      catalog.shapeLoader.sources=catalog.loader.sources;
    }
    const converted=catalog.shapeLoader.load({key:`SHAP:${id}`,payload:entry.payload,directoryFlags:entry.flags,paletteHandle});
    entry.handle=catalog.loader.sources.get(`SHAP:${id}`);
    const owner=this.memory.resourceOwners.get(entry.handle);if(owner)owner.entry=entry;
    return converted;
  }
  resolve(tag,id){
    let handle=this.lookup;const seen=new Set();
    while(handle){
      if(seen.has(handle))throw new Error("Cyclic original archive lookup list");
      seen.add(handle);const catalog=this.catalogs.get(handle);
      if(!catalog)throw new Error("Original archive lookup state is unavailable");
      const entry=catalog.records.find(e=>e.tag===tag&&e.id===id);
      if(entry)return {catalog,entry};handle=catalog.previous;
    }
    return null;
  }
  snapshot(handle){
    const c=this.catalogs.get(handle);if(!c)throw new Error("Unknown original catalog");
    const h=this.memory.handle(handle);
    return {handle,state:h.state,segment:h.segment,archive:c.filename.split(/[/\\]/).at(-1).replace(/\.dat$/i,'').toLowerCase(),
      records:c.records.map(({row,payload,...entry})=>({...entry})),types:c.types.map(t=>({...t,ids:t.ids.slice()}))};
  }
}
