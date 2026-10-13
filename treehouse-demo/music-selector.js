"use strict";
// Overlay 1 family/portrait menus, using recovered tables and original resources.
class MusicSelector {
  constructor(store,{current,choose,play,stop,changed,leave}){
    this.store=store;this.tables=store.data.music.followup;Object.assign(this,{current,choose,play,stop,changed,leave});this.voice=null;
    this.open=false;this.category=-1;this.info=0;this.fact=0;this.tick=0;this.performance=null;this.still=null;this.stillInstrument=-1;
  }
  name(id){return this.store.data.music.instruments[id].name;}
  facts(){return this.store.data.strings[`modules:${this.info}`]||[];}
  show(category=-1){this.open=true;this.category=category;this.performance=null;if(category>=0){this.info=category;this.fact=0;}this.changed();}
  select(id){if(this.info===id)this.fact=(this.fact+1)%Math.max(1,this.facts().length);else this.fact=0;this.info=id;this.choose(id);this.audition();this.changed();}
  animation(tick,callback=()=>{}){const group=this.store.data.music.instruments[this.current()].animation_group,b=this.store.data.scripts[`th:${group}`].bounds;const a=new Animation(this.store,'th',group,group,{startTick:tick,origin:[1,199-(b[2]-b[0])],onCallback:callback});a.update(tick);return a;}
  audition(){this.stop(this.voice);this.performance=this.animation(this.tick,slot=>{if(slot===0){this.stop(this.voice);this.voice=this.play();}});}
  update(tick){this.tick=tick;if(this.open&&this.performance&&!this.performance.done){this.performance.update(tick);if(this.performance.done){this.stop(this.voice);this.voice=null;}return true;}return false;}
  nextFact(){this.fact=(this.fact+1)%Math.max(1,this.facts().length);this.changed();}
  hit(b,x,y){return x>=b[1]&&x<b[3]&&y>=b[0]&&y<b[2];}
  click(x,y){
    const t=this.tables,r=this.category<0?t.menu_rectangles:t.instrument_rectangles;
    if(this.hit(r[0],x,y)){this.leave('inside');return;}if(this.hit(r[1],x,y)){this.leave('music');return;}
    if(this.category<0){for(let i=0;i<7;i++)if(this.hit(r[2+i],x,y)){this.show(i);return;}}
    else{
      if(this.hit(r[2],x,y)){this.show();return;}if(this.hit(r[3],x,y)){this.select(this.category);return;}
      if([4,5,6].some(i=>this.hit(r[i],x,y))){this.nextFact();return;}
      for(let i=0;i<t.members[this.category].length;i++){const id=t.members[this.category][i],s=this.store.shape('modules',2401+10*this.category+i),x0=t.portrait_x[id],y0=t.portrait_y[id];if(this.hit([y0-6,x0-6,y0+s.h+6,x0+s.w+6],x,y)){this.select(id);return;}}
    }
    if(x<63&&y>100)this.audition();
  }
  heading(surface,value,b,outline=true){
    const s=this.store,font=s.data.heading_font,w=[...value].reduce((n,c)=>n+(font[c.charCodeAt(0)]?.[0]||3)+1,0),h=font[value.charCodeAt(0)][1];
    const x=Math.floor((b[1]+b[3])/2)-Math.floor(w/2),y=Math.floor((b[0]+b[2])/2)-Math.floor((h+1)/2);
    if(outline)for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)surface.text(s,value,x+dx,y+dy,0xff000000,font,1);
    surface.text(s,value,x,y,outline?0xffaaaaaa:0xff000000,font,1);
  }
  draw(surface){
    const s=this.store,t=this.tables,p=s.palette('modules',2270).rgba,draw=(id,pal,x,y,mode=10)=>surface.draw(s,'modules',id,pal,x,y,mode),fill=(b,c)=>surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],c);
    draw(this.category<0?2271:2272,2270,0,0,2);
    if(this.category<0){
      for(let i=0;i<3;i++){const [top,left,bottom,right]=t.menu_rectangles[2+i],c=p[t.category_palette_index[i]];surface.rect(left+1,top+2,right-left,bottom-top-2,0xff000000);surface.rect(left+2,top+1,right-left-2,bottom-top,0xff000000);surface.rect(left,top+1,right-left,bottom-top-2,c);surface.rect(left+1,top,right-left-2,bottom-top,c);}
      for(let i=0;i<7;i++)this.heading(surface,this.name(i),t.menu_rectangles[2+i]);
    }else{
      const c=this.category,r=t.instrument_rectangles;
      t.members[c].forEach((id,i)=>draw(2401+10*c+i,2400+10*c,t.portrait_x[id],t.portrait_y[id]));
      draw(2273,2270,259,3);fill(r[3],p[t.category_palette_index[c]]);this.heading(surface,this.name(c),r[3]);this.heading(surface,this.name(this.info),[102,227,114,305],false);
      surface.rect(63,144,120,48,0xffffffff);draw(2001+(this.info===21?20:this.info),2000,63,144,2);
      const box=r[4];fill(box,0xffffffff);surface.rect(box[1],box[0],box[3]-box[1],1,0xff000000);surface.rect(box[1],box[2]-1,box[3]-box[1],1,0xff000000);surface.rect(box[1],box[0],1,box[2]-box[0],0xff000000);surface.rect(box[3]-1,box[0],1,box[2]-box[0],0xff000000);
      const group=t.fact_icon_groups[this.info]?2075:2050,palette=s.palette('modules',group),id=palette.first+t.fact_icon_indices[this.info]-1,shape=s.shape('modules',id);draw(id,group,Math.floor((box[1]+box[3])/2)-Math.floor(shape.w/2),Math.floor((box[0]+box[2])/2)-Math.floor(shape.h/2));
      const width=value=>[...value].reduce((n,ch)=>n+(s.data.font[ch.charCodeAt(0)]?.[0]||4),0),lines=[];let line='';
      for(const word of (this.facts()[this.fact]||'').split(' ')){const trial=line?line+' '+word:word;if(width(trial)>113){lines.push(line);line=word;}else line=trial;}lines.push(line);
      const y=160-Math.floor(lines.length*10/2);lines.forEach((value,i)=>surface.text(s,value,193,y+10*i,0xff000000,s.data.font,0,r[6]));
    }
    surface.draw(s,'th',8,6,304,1);surface.draw(s,'th',7,6,280,1);
    if(this.performance&&!this.performance.done)this.performance.draw(surface);
    else{const id=this.current();if(this.stillInstrument!==id){this.still=this.animation(0);this.stillInstrument=id;}this.still.draw(surface);}
  }
}
