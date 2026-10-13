"use strict";
// VGA font activation converts packed glyphs, then transfers the converted
// allocation into the cached font's existing handle (resident D1D8).
class OriginalFontLoading {
  static convert(payload){
    const source=Uint8Array.from(payload),word=at=>source[at]|source[at+1]<<8;
    if(source.length<10||source[1]<source[0])throw new Error("Invalid original font header");
    const count=source[1]-source[0]+1,glyphs=[];
    if(source.length<10+2*count)throw new Error("Truncated original font directory");
    let length=10+8*count;
    for(let i=0;i<count;i++){
      const offset=word(10+2*i);
      if(offset+6>source.length)throw new Error("Invalid original glyph offset");
      const height=word(offset),width=word(offset+2),stride=Math.ceil(width/8);
      if(offset+6+height*stride>source.length)throw new Error("Truncated original glyph bitmap");
      length+=width*height;glyphs.push({offset,height,width,stride});
    }
    if(length>65535)throw new Error("Original converted font exceeds segment size");
    const output=new Uint8Array(length),put=(at,v)=>{output[at]=v&255;output[at+1]=v>>>8;};
    output.set(source.subarray(0,10));let at=10+2*count;
    for(let i=0;i<count;i++){
      const {offset,height,width,stride}=glyphs[i];put(10+2*i,at);
      put(at,height);put(at+2,width);put(at+4,width);
      for(let y=0;y<height;y++)for(let x=0;x<width;x++)output[at+6+y*width+x]=source[offset+6+y*stride+(x>>>3)]&(0x80>>>(x&7))?255:0;
      at+=6+height*width;
    }
    return output;
  }
  static activate(loader,id){
    const m=loader.memory,saved=m.handle(id).state;
    if(saved&0x2000)return id;
    const source=loader.payloads.get(id);
    if(!source)throw new Error("Original font source bytes are unavailable");
    m.lock(id);const bytes=this.convert(source),converted=m.allocateHandle(bytes.length);
    m.lock(converted);m.unlock(converted);m.flags(id,saved);
    const pointer=m.detachHandle(converted);
    if(!m.attachHandle(id,pointer)){m.freeRaw(pointer);m.freeHandle(converted);return 0;}
    m.keepResident(id);m.freeHandle(converted);loader.payloads.set(id,bytes);
    loader.operations.push({kind:'font.convert',bytes:bytes.length});return id;
  }
}
