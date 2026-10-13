"use strict";
// Original indexed graphics and recovered SCR semantics. This runtime executes
// resource scripts, never DOS machine code or recorded frame sequences.
const bytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const u16 = (b, at=0) => b[at] | b[at+1] << 8;
const s16 = (b, at=0) => (u16(b, at) << 16) >> 16;
const s32 = (b, at=0) => (u16(b, at) | u16(b, at+2) << 16);

// D51:3BA6: one session-wide stream, seeded from BIOS ticks since midnight.
class OriginalRandom {
  constructor(){this.initialized=false;this.seed=0;this.trace=null;}
  int(maxInclusive){
    if(!this.initialized){const now=new Date(),midnight=new Date(now.getFullYear(),now.getMonth(),now.getDate());this.seed=Math.floor((now-midnight)/1000*1193181/65536)>>>0;this.initialized=true;}
    const before=this.seed;this.seed=(Math.imul(this.seed,214013)+2531011)>>>0;const result=(this.seed>>>16)%(maxInclusive+1);
    if(this.trace)this.trace.push({bound:maxInclusive,before,after:this.seed,result});return result;
  }
  pick(count){return this.int(count-1);}
  reset(seed){this.seed=seed>>>0;this.initialized=true;}
}
const gameplayRandom=new OriginalRandom();

class ResourceStore {
  constructor(data) { this.data=data; this.cache=new Map();this.animationPlans=new Map(); }
  animationResources(archive,id,palette) {
    const key=`${archive}:${id}:${palette}`;
    if(this.animationPlans.has(key))return this.animationPlans.get(key);
    const script=this.data.scripts[`${archive}:${id}`],group=this.palette(archive,palette);
    if(!script)throw new Error(`Missing original script ${archive}:${id}`);
    // Main C449..C567 scans the complete SCR before execution, marking every
    // nonzero Cx shape range. C5AC..C62D then loads marked shapes in ascending
    // palette-relative order, including shapes after the first display.
    const marked=new Set();
    for(const [code,operand]of script.code){
      if(code===0)break;
      if((code&0xf0)!==0xc0)continue;
      const first=u16(operand),last=u16(operand,2);
      if(!first)continue;
      for(let relative=first;relative<=last;relative++){
        if(relative>group.count)throw new Error(`Script ${archive}:${id} references shape ${relative} outside palette ${palette}`);
        marked.add(relative);
      }
    }
    const plan=Object.freeze([...marked].sort((a,b)=>a-b).map(relative=>Object.freeze({relative,id:group.first+relative-1})));
    this.animationPlans.set(key,plan);return plan;
  }
  prepareAnimation(archive,id,palette) {
    const plan=this.animationResources(archive,id,palette);
    for(const resource of plan)this.shape(archive,resource.id);
    return plan;
  }
  shape(archive, id) {
    const key=`${archive}:${id}`;
    if (!this.cache.has(key)) {
      const raw=this.data.shapes[key];
      if (!raw) throw new Error(`Missing original shape ${key}`);
      this.cache.set(key, {w:raw[0], h:raw[1], pixels:bytes(raw[2])});
    }
    return this.cache.get(key);
  }
  palette(archive, id) {
    const value=this.data.palettes[`${archive}:${id}`];
    if (!value) throw new Error(`Missing original palette ${archive}:${id}`);
    if (!value.rgba) value.rgba=Uint32Array.from(value.colors, ([r,g,b]) => (0xff000000 | b<<16 | g<<8 | r)>>>0);
    return value;
  }
}

class Surface {
  constructor(width=320,height=200) {
    this.width=width; this.height=height;
    this.image=new ImageData(width,height);
    this.pixels=new Uint32Array(this.image.data.buffer);
    this.clear();
  }
  clear(color=0xff000000) { this.pixels.fill(color>>>0); }
  clone() { const s=new Surface(this.width,this.height); s.pixels.set(this.pixels); return s; }
  restore(surface) { this.pixels.set(surface.pixels); }
  rect(x,y,w,h,color) {
    const left=Math.max(0,x),right=Math.min(this.width,x+w),top=Math.max(0,y),bottom=Math.min(this.height,y+h);
    if(left>=right||top>=bottom)return;
    for(let j=top;j<bottom;j++)this.pixels.fill(color>>>0,j*this.width+left,j*this.width+right);
  }
  blit(shape,palette,x,y,mode=10,clip=null) {
    x=Math.floor(x); y=Math.floor(y);
    if(mode!==0 && mode!==2 && mode!==10) throw new Error(`Unimplemented original draw mode ${mode}`);
    const left=Math.max(0,x,clip?clip[1]:0), top=Math.max(0,y,clip?clip[0]:0);
    const right=Math.min(this.width,x+shape.w,clip?clip[3]:this.width);
    const bottom=Math.min(this.height,y+shape.h,clip?clip[2]:this.height);
    for(let py=top;py<bottom;py++) for(let px=left;px<right;px++) {
      const index=shape.pixels[(py-y)*shape.w+px-x];
      if(mode===10 && index===0) continue;
      if(index>=palette.length) throw new Error("Image index exceeds selected palette");
      this.pixels[py*this.width+px]=palette[index];
    }
  }
  draw(store,archive,shape,palette,x=0,y=0,mode=10,clip=null) {
    this.blit(store.shape(archive,shape),store.palette(archive,palette).rgba,x,y,mode,clip);
  }
  text(store,text,x,y,color=0xff000000,font=store.data.font,extra=0,clip=null) {
    for(const char of text) {
      const code=char.charCodeAt(0),raw=font[code];
      if(!raw) {x+=4;continue;}
      if(!raw.decoded) raw.decoded={w:raw[0],h:raw[1],pixels:bytes(raw[2])};
      this.blit(raw.decoded,[0,color>>>0],x,y,10,clip);x+=raw[0]+extra;
    }
    return x;
  }
}

class Animation {
  constructor(store,archive,id,palette,{startTick=0,origin=null,onSound=()=>{},onCallback=()=>{},onDisplay=()=>{}}={}) {
    this.store=store; this.archive=archive;this.id=id;this.palette=palette;
    this.script=store.data.scripts[`${archive}:${id}`];
    if(!this.script) throw new Error(`Missing original script ${archive}:${id}`);
    this.resources=store.prepareAnimation(archive,id,palette);
    this.origin=origin || [this.script.bounds[1],this.script.bounds[0]];
    this.pc=0;this.repeat=0;this.delay=0;this.last=0;this.startTick=startTick;
    this.done=false;this.suppress=false;this.onSound=onSound;this.display=[];
    this.onCallback=onCallback;this.onDisplay=onDisplay;
    this.slots=Array.from({length:16},()=>this.empty());
    this.frameUpdates=0;
  }
  empty() { return {shape:0,first:0,end:0,flags:2,x:-2147483648,y:-2147483648,vx:0,vy:0,ax:0,ay:0,sc:0,mc:0}; }
  snapshot() { this.display=this.slots.map(s=>({...s})); }
  advanceSlots() {
    for(const s of this.slots) {
      if(!s.shape) continue;
      const sc=s.sc,mc=s.mc;s.sc=(sc+1)&255;s.mc=(mc+1)&255;
      if(s.first!==s.end && sc>=((s.flags>>>8)&15)) {
        s.sc=0;s.shape+=(s.flags&0x1000)?-1:1;
        if(s.shape>s.end) {
          if(s.flags&0x2000) {s.shape=s.end-1;s.flags|=0x1000;} else s.shape=s.first;
        } else if(s.shape<s.first) {
          if(s.flags&0x2000) {s.shape=s.first+1;s.flags&=~0x1000;} else s.shape=s.end;
        }
      }
      if(mc>=((s.flags>>>4)&15)) {
        s.mc=0;s.x=(s.x+s.vx)|0;s.y=(s.y+s.vy)|0;s.vx=(s.vx+s.ax)|0;s.vy=(s.vy+s.ay)|0;
      }
    }
  }
  step(tick) {
    if(this.done) return false;
    const now=(tick-this.startTick)>>>0;
    // A host tick can service multiple interpreter calls. Yielding instructions
    // remain separate calls; the app services them until no state can advance.
    for(let budget=0;budget<1024;budget++) {
      const op=this.script.code[this.pc];
      if(!op) throw new Error(`Script ${this.id} runs beyond terminator`);
      const [code,b]=op,slot=code&15,s=this.slots[slot];
      const due=now>=((this.last+this.delay)>>>0);
      if(code===0) { if(due) this.done=true;return false; }
      if(code===1) {
        if(!due) return false;
        this.last=now;this.frameUpdates++;
        if(this.suppress){this.display=this.prepared;this.prepared=null;}else this.snapshot();
        this.onDisplay(this);
        this.suppress=false;this.advanceSlots();
        if(this.repeat===0) {this.repeat=u16(b);this.delay=u16(b,2);}
        this.repeat=(this.repeat-1)&65535;
        if(this.repeat===0) this.pc++;
        return true;
      }
      if(code===3) {
        if(!due) return false;
        this.onSound(u16(b));this.pc++;return true;
      }
      // Opcode7 composes offscreen; only opcode1 publishes the prepared frame.
      if(code===7) {this.prepared=this.slots.map(s=>({...s}));this.suppress=true;this.pc++;return true;}
      if(code>=0x10 && code<=0x13) {
        // Null is a no-op; the original instrument audition installs slot0.
        this.onCallback(code&3,u16(b),this);
      } else if((code&0xf0)===0x90) {
        const flags=(s.flags&u16(b))|u16(b,2);
        if((flags&0x0f00)!==(s.flags&0x0f00)) s.sc=0;
        if((flags&0x00f0)!==(s.flags&0x00f0)) s.mc=0;
        s.flags=flags;
      } else if((code&0xf0)===0xa0) {s.x=(s.x+(s16(b)<<16))|0;s.y=(s.y+(s16(b,2)<<16))|0;}
      else if((code&0xf0)===0xb0) {s.x=s16(b)<<16;s.y=s16(b,2)<<16;}
      else if((code&0xf0)===0xc0) {
        if(u16(b)===0) this.slots[slot]=this.empty();
        else {s.shape=s.first=u16(b);s.end=u16(b,2);}
      } else if((code&0xf0)===0xd0) {s.vx=s32(b);s.vy=s32(b,4);}
      else if((code&0xf0)===0xe0) {s.ax=s32(b);s.ay=s32(b,4);}
      else throw new Error(`Unimplemented SCR opcode ${code.toString(16)} in ${this.archive}:${this.id}`);
      this.pc++;
    }
    throw new Error(`Script ${this.id} exceeds instruction budget`);
  }
  update(tick) { for(let calls=0;calls<1024;calls++) if(!this.step(tick)) return;throw new Error("Animation fails to yield"); }
  draw(surface) {
    const palette=this.store.palette(this.archive,this.palette);
    const b=this.script.bounds,w=b[3]-b[1],h=b[2]-b[0];
    const clip=[this.origin[1],this.origin[0],this.origin[1]+h,this.origin[0]+w];
    for(const s of this.display) if(s.shape) {
      surface.blit(this.store.shape(this.archive,palette.first+s.shape-1),palette.rgba,
        this.origin[0]+(s.x>>16),this.origin[1]+(s.y>>16),s.flags&15,clip);
    }
  }
}
