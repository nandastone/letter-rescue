"use strict";
// Presentation model for the pinned DOSBox reference's four-part VGA scanout.
// Receives independently rendered framebuffer commits and an explicit clock.
// This component does not infer CPU drawing time or execute recorded gameplay.
class OriginalScanout {
  constructor({width=320,height=200,parts=4,partMilliseconds}={}) {
    if(!Number.isInteger(width)||width<=0||!Number.isInteger(height)||height<=0||
       !Number.isInteger(parts)||parts<=0||height%parts||!Number.isFinite(partMilliseconds)||!(partMilliseconds>0))
      throw new Error("Invalid scanout geometry or timing");
    this.width=width;this.height=height;this.parts=parts;this.partMilliseconds=partMilliseconds;
    this.commits=[];this.pixels=new Uint32Array(width*height);this.lastFrame=-Infinity;this.presentedThrough=-Infinity;
  }
  commit(milliseconds,pixels) {
    if(!Number.isFinite(milliseconds)||milliseconds<=this.presentedThrough||pixels.length!==this.pixels.length||
       (this.commits.length&&milliseconds<this.commits.at(-1).milliseconds))
      throw new Error("Framebuffer commits must have matching dimensions and ordered timestamps");
    // A later drawing operation must not mutate an already scheduled display.
    this.commits.push({milliseconds,pixels:new Uint32Array(pixels)});
  }
  present(frameStart) {
    if(!Number.isFinite(frameStart)||frameStart<this.lastFrame||!this.commits.length)
      throw new Error("Scanout needs a framebuffer and an ordered frame clock");
    const firstRead=frameStart+this.partMilliseconds;
    if(this.commits[0].milliseconds>firstRead)throw new Error("No framebuffer exists at scanout start");
    let index=0,firstIndex=0;const length=this.pixels.length/this.parts;
    for(let part=0;part<this.parts;part++) {
      const readAt=frameStart+(part+1)*this.partMilliseconds;
      while(index+1<this.commits.length&&this.commits[index+1].milliseconds<=readAt)index++;
      if(part===0)firstIndex=index;
      const start=part*length;
      this.pixels.set(this.commits[index].pixels.subarray(start,start+length),start);
    }
    // Future frames can still need the framebuffer used by this frame's first
    // part. Earlier commits are unreachable and can be released.
    if(firstIndex)this.commits.splice(0,firstIndex);
    this.lastFrame=frameStart;this.presentedThrough=frameStart+this.parts*this.partMilliseconds;return this.pixels;
  }
}
