"use strict";
// Resident drawing loop 0xD91..0xF36. The backing image is 94 by 47 pixels.
class Chalkboard {
  constructor(store,changed=()=>{},returned=()=>{}) {
    this.colors=[5,62,37,3,44,11,0].map(i=>store.palette("th64",4).rgba[i]);
    this.names=["White","Red","Yellow","Violet","Green","Pink","Eraser"];
    this.bitmap=new Surface(94,47);this.tool=-1;this.previous=null;this.history=[];this.changed=changed;this.returned=returned;this.returnedColor=null;
  }
  select(tool){this.end();this.tool=tool;this.returnedColor=null;this.changed();}
  remember(){this.history.push(this.bitmap.pixels.slice());if(this.history.length>30)this.history.shift();}
  begin(x,y){if(this.tool<0)return false;this.remember();this.previous=null;this.move(x,y,true);return true;}
  move(x,y,held=false,smooth=false) {
    x=Math.floor(x);y=Math.floor(y);this.returnedColor=null;
    // The original installs the arrow before resetting its logical color.
    // That displayed arrow keeps the tool color until the next pointer move.
    if(!smooth&&(x<52||x>=157||y<40||y>=97)){this.end();if(this.tool>=0){this.returnedColor=this.tool===6?0xffffffff:this.colors[this.tool];this.tool=-1;this.returned();this.changed();}return[x,y];}
    if(this.tool<0||!held){this.previous=null;return[x,y];}
    if(this.previous&&this.tool<6){
      const [px,py]=this.previous;
      if(smooth){const steps=Math.max(Math.abs(x-px),Math.abs(y-py));for(let i=1;i<steps;i++)this.stamp(Math.round(px+(x-px)*i/steps),Math.round(py+(y-py)*i/steps));}
      else {x=Math.max(px-2,Math.min(px+2,x));y=Math.max(py-2,Math.min(py+2,y));}
    }
    this.stamp(x,y);this.previous=[x,y];return[x,y];
  }
  stamp(x,y){const eraser=this.tool===6;this.bitmap.rect(x-60+(eraser?1:-1),y-45+(eraser?1:-1),eraser?6:2,eraser?10:2,this.colors[this.tool]);}
  end(){this.previous=null;}
  clear(){this.end();this.remember();this.bitmap.clear();this.changed();}
  undo(){this.end();const old=this.history.pop();if(old)this.bitmap.pixels.set(old);this.changed();}
  draw(surface){
    for(let y=0;y<47;y++)surface.pixels.set(this.bitmap.pixels.subarray(y*94,(y+1)*94),(y+45)*surface.width+60);
  }
  drawTray(surface){
    if(this.tool>=0){const x=63+12*this.tool,w=this.tool===6?14:10;surface.rect(x,92,w,1,0xff000000);surface.rect(x,93,w,2,0xff696969);}
  }
}
