"use strict";
// Original 65-byte SONG records: two lengths, tempo, instrument, notation,
// followed by thirty pitch/duration pairs. Empty pitches are 0x7f.
class MusicEditor {
  constructor(store,{changed=()=>{},announce=()=>{},play=()=>null,release=()=>{}}={}){
    this.store=store;this.tables=store.data.music.followup.music;this.changed=changed;this.announce=announce;this.play=play;this.release=release;this.voice=null;this.voiceDue=Infinity;this.tick=0;
    this.enabled=false;this.advanced=false;this.index=[0,0];this.duration=[4,4];this.position=0;this.drag=null;this.eraser=false;this.randomTask=null;this.labels=new Set(Array.from({length:30},(_,i)=>i));this.books=Array.from({length:2},()=>Array.from({length:43},()=>this.blank()));
    this.contents=0;this.titleEntry=null;this.cursorColor=0xff55ffff;this.titles=Array.from({length:2},(_,m)=>Array.from({length:43},(_,i)=>this.encodeTitle(this.defaultTitle(m,i))));this.trailing=[36,0];
    for(let m=0;m<2;m++)this.books[m][42]=[...store.data.music.end_songs[m]];
    try{const value=JSON.parse(localStorage.getItem('treehouse-songbooks-v1'));if(value?.version===1&&value.books?.length===2&&value.books.every((book,m)=>book.length===43&&book.every(s=>this.valid(s,m)))){this.books=value.books;if(value.titles?.length===2&&value.titles.every(book=>book.length===43&&book.every(t=>Array.isArray(t)&&t.length===36&&t.every(v=>Number.isInteger(v)&&v>=0&&v<=255))))this.titles=value.titles;if(value.trailing?.length===2)this.trailing=value.trailing;}}catch(_error){}
  }
  blank(){const raw=Array(65).fill(0);raw[2]=3;raw[3]=9;for(let i=0;i<30;i++)raw[5+2*i]=127;return raw;}
  valid(raw,mode=this.mode){return Array.isArray(raw)&&raw.length===65&&raw.every(v=>Number.isInteger(v)&&v>=0&&v<=255)&&raw[mode]<=(mode?30:8)&&raw[2]<5&&raw[3]<42&&raw[4]<2&&Array.from({length:mode?30:8},(_,i)=>raw[5+2*i]===127||((raw[5+2*i]&127)<=16&&raw[6+2*i]<16)).every(Boolean);}
  defaultTitle(mode,index){return `My ${mode?'Long':'Short'} Song #${index+1}`;}
  encodeTitle(title){const result=Array(36).fill(0),chars=this.store.data.music.cp437;Array.from(title).slice(0,35).forEach((c,i)=>{const n=chars.indexOf(c);result[i]=n>0?n:63;});return result;}
  titleAt(mode,index){const raw=this.titles[mode][index];return raw.slice(0,raw.indexOf(0)<0?36:raw.indexOf(0)).map(n=>this.store.data.music.cp437[n]).join('');}
  rename(title){if(!this.editable)return;this.titles[this.mode][this.index[this.mode]]=this.encodeTitle(title);this.save();}
  used(mode,index){return index===42||this.books[mode][index][mode]>0||this.titleAt(mode,index)!==this.defaultTitle(mode,index);}
  firstFree(){return this.books[this.mode].findIndex((_,i)=>!this.used(this.mode,i));}
  exportData(){const result=new Uint8Array(8688);for(let m=0;m<2;m++)for(let i=0;i<43;i++){const n=43*m+i;result.set(this.books[m][i],65*n);result.set(this.titles[m][i],0x15d6+36*n);}result.set(this.trailing,0x21ee);return result;}
  importData(data){if(data.length!==8688)throw new Error('Choose an original SONGS.DAT file (8,688 bytes).');const books=[[],[]],titles=[[],[]];for(let m=0;m<2;m++)for(let i=0;i<43;i++){const n=43*m+i,song=Array.from(data.slice(65*n,65*(n+1)));if(!this.valid(song,m))throw new Error(`Song ${i+1} in the ${m?'long':'short'} book contains invalid note data.`);books[m].push(song);titles[m].push(Array.from(data.slice(0x15d6+36*n,0x15d6+36*(n+1))));}this.books=books;this.titles=titles;this.trailing=Array.from(data.slice(0x21ee));this.select();this.save();}
  get mode(){return Number(this.advanced);}
  get capacity(){return this.advanced?30:8;}
  get editable(){return this.enabled&&this.index[this.mode]<42;}
  get song(){return this.books[this.mode][this.index[this.mode]];}
  get title(){return this.titleAt(this.mode,this.index[this.mode]);}
  select(index=this.index[this.mode]){this.labels=new Set(Array.from({length:30},(_,i)=>i));this.drag=null;this.eraser=false;this.randomTask=null;this.index[this.mode]=Math.max(0,Math.min(42,index));this.position=0;for(let i=0;i<this.capacity;i++)if(this.song[5+2*i]===127){this.position=i;break;}this.changed();}
  save(){try{localStorage.setItem('treehouse-songbooks-v1',JSON.stringify({version:1,books:this.books,titles:this.titles,trailing:this.trailing}));}catch(_error){this.announce('Your song is ready to play. This browser could not save it after closing.');}this.changed();}
  write(pitch,duration=this.duration[this.mode]%8,advance=true){
    if(!this.editable||this.randomTask||this.contents||this.titleEntry)return;
    const raw=this.song,i=this.position;this.labels.add(i);raw[5+2*i]=pitch|(raw[4]<<7);raw[6+2*i]=duration;raw[this.mode]=Math.max(raw[this.mode],i+1);if(advance)this.position=Math.min(this.capacity-1,i+1);this.save();
  }
  clearAll(){for(let m=0;m<2;m++)for(let i=0;i<43;i++){this.books[m][i]=i===42?[...this.store.data.music.end_songs[m]]:this.blank();this.titles[m][i]=this.encodeTitle(this.defaultTitle(m,i));}this.index=[0,0];this.select(0);this.save();}
  beginTitle(tick){if(!this.editable||this.contents)return;this.titleEntry={old:this.title,value:'',start:tick};this.changed();}
  titleKey(key){const entry=this.titleEntry;if(!entry)return false;if(key==='Enter'){this.acceptTitle();return true;}if(key==='Escape')entry.value=entry.old;else if(key==='Backspace'||key==='Delete')entry.value=entry.value.slice(0,-1);else if(key.length===1&&key.charCodeAt(0)>=32&&key.charCodeAt(0)<=126){const next=entry.value+key,w=[...next+'_'].reduce((n,c)=>n+(this.store.data.font[c.charCodeAt(0)]?.[0]||4),0);if(next.length<=35&&113+w<258)entry.value=next;}this.changed();return true;}
  acceptTitle(){if(!this.titleEntry)return;const value=this.titleEntry.value||this.titleEntry.old;this.titleEntry=null;this.rename(value);}
  drawTitle(surface,tick){if(!this.titleEntry)return;const e=this.titleEntry,s=this.store,blue=0xffff5555;surface.rect(111,13,149,13,blue);surface.rect(112,14,147,11,0xffffffff);const x=surface.text(s,e.value,113,15);if(Math.floor((tick-e.start)/6)%2===0)surface.text(s,'_',x,15);}
  drawContents(surface){if(!this.contents)return;const s=this.store,width=str=>[...str].reduce((n,c)=>n+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);surface.rect(88,27,212,75,0xffffffff);surface.rect(88,6,22,20,0xffffffff);surface.rect(113,13,145,13,0xffffffff);surface.text(s,'Table of Contents',137,13,0xff000000,s.data.heading_font,1);for(let slot=0;slot<6;slot++){const i=(this.contents-1)*6+slot,x=slot<3?88:194,y=27+23*(slot%3),code=this.enabled?1:s.data.music.song_icons[i+1],group=2100+20*(code>>4);surface.draw(s,'modules',s.palette('modules',group).first+(code&15)-1,group,x,y,2);const title=this.enabled?this.titleAt(this.mode,i):s.data.strings['modules:101'][i],lines=[''];for(const word of title.split(' ')){const next=lines.at(-1)+(lines.at(-1)?' ':'')+word;if(width(next)>81&&lines.at(-1))lines.push(word);else lines[lines.length-1]=next;}const top=Math.floor((y+y+20-(10*lines.length-1))/2);lines.forEach((line,j)=>surface.text(s,line,x+24,top+10*j));}const roman=['i','ii','iii','iv','v','vi','vii'][this.contents-1];surface.text(s,roman,300-width(roman),93);}
  remove(index=this.position){if(!this.editable)return;this.song[5+2*index]=127;while(this.song[this.mode]>0&&this.song[5+2*(this.song[this.mode]-1)]===127)this.song[this.mode]--;this.save();}
  clear(){if(!this.editable)return;for(let i=0;i<30;i++)this.song[5+2*i]=127;this.song[this.mode]=0;this.position=0;this.titles[this.mode][this.index[this.mode]]=this.encodeTitle(this.defaultTitle(this.mode,this.index[this.mode]));this.save();}
  randomize(tick){if(!this.editable)return;this.song[4]=1;this.song[this.mode]=this.capacity;this.randomTask={index:0,due:tick};this.changed();}
  audition(pitch,duration=null){this.release(this.voice);this.voice=this.play(pitch);this.voiceDue=duration===null?Infinity:this.tick+this.store.data.music.tempo_factors[this.song[2]]*this.store.data.music.duration_factors[duration];}
  update(tick){this.tick=tick;if(this.voice!==null&&tick>=this.voiceDue){this.release(this.voice);this.voice=null;}const task=this.randomTask;if(!task||tick<task.due)return false;const pitches=[0,2,5,7,9,12,14],durations=[2,3,3,4,4,4,4,4,4,6,6,6,6],i=task.index++;this.song[5+2*i]=128|pitches[gameplayRandom.pick(pitches.length)];this.song[6+2*i]=i===this.capacity-1?0:durations[gameplayRandom.pick(durations.length)];task.due=tick+6;if(task.index===this.capacity){this.randomTask=null;this.save();}return true;}
  copy(raw,title,index=this.firstFree()){if(index<0||index>=42)return false;this.select(index);this.books[this.mode][index]=[...raw];this.song[this.mode]=Math.min(this.capacity,raw[this.mode]);this.titles[this.mode][index]=this.encodeTitle(title||this.defaultTitle(this.mode,index));this.select();this.labels.clear();this.save();return true;}
  hit(b,x,y){return x>=b[1]&&x<b[3]&&y>=b[0]&&y<b[2];}
  get noteRects(){return this.advanced?this.tables.advanced_note_rects:this.tables.intro_note_rects;}
  get markers(){return this.advanced?this.tables.advanced_markers:this.tables.intro_markers;}
  pitchAt(y,index){const offset=(this.advanced?56+39*Math.floor(index/15):78)-y;return this.store.data.music.drag_pitches[this.mode][Math.max(0,Math.min(this.advanced?27:36,Math.round(offset)))];}
  click(x,y){
    if(!this.editable||this.randomTask||this.contents||this.titleEntry)return false;
    if(this.hit([105,77,112,117],x,y)){this.eraser=!this.eraser;this.changed();return true;}
    const rects=this.advanced?this.tables.advanced_duration_rects:this.tables.intro_duration_rects,index=rects.findIndex(b=>this.hit(b,x,y));
    if(index>=0){const d=this.tables.duration_values[this.mode][index];this.duration[this.mode]=d%8;this.eraser=false;this.drag={kind:'palette',x,y,moved:false,d,anchor:[rects[index][1]+this.tables.duration_x_offset[16*this.mode+index],rects[index][0]+this.tables.duration_y_offset[16*this.mode+index]]};this.changed();return true;}
    if(this.hit(this.markers[this.position+1],x,y)){this.drag={kind:'marker',x,y,moved:false};return true;}
    const selected=this.noteRects.findIndex(b=>this.hit(b,x,y));
    if(selected>=0){if(this.eraser){this.remove(selected);return true;}if((this.song[5+2*selected]&127)!==127&&this.song[6+2*selected]<8){this.drag={kind:'note',x,y,index:selected,height:this.store.data.music.drag_pitches[this.mode].indexOf(this.song[5+2*selected]&127),moved:false};this.audition(this.song[5+2*selected]&127);this.changed();}return true;}
    return false;
  }
  pointerMoved(){this.cursorColor=0xff55ffff;}
  move(x,y){if(this.eraser&&!this.hit([26,77,112,300],x,y)){this.eraser=false;this.cursorColor=this.store.palette('modules',2200).rgba[12];this.changed();}const d=this.drag;if(!d)return false;if(Math.abs(x-d.x)>2||Math.abs(y-d.y)>2||d.kind==='note')d.moved=true;if(!d.moved)return true;
    if(d.kind==='marker'){const count=this.advanced?15:8,column=Math.max(0,Math.min(count-1,Math.floor((x-(this.advanced?105:114))/(this.advanced?13:22))));this.position=column+(this.advanced&&y>=62?15:0);}
    if(d.kind==='note'){const h=Math.max(0,Math.min(this.advanced?27:36,Math.round(d.height+d.y-y)));this.labels.add(d.index);const pitch=this.store.data.music.drag_pitches[this.mode][h];if(pitch!==(this.song[5+2*d.index]&127)){this.song[5+2*d.index]=pitch|(this.song[5+2*d.index]&128);this.audition(pitch);this.save();}}
    if(d.kind==='palette'){const stem=this.advanced?10:16;d.point=[Math.max(10,Math.min(304,d.anchor[0]+x-d.x)),Math.max(2+stem,Math.min(172+stem,d.anchor[1]+y-d.y))];}this.changed();return true;
  }
  end(cancel=false){const d=this.drag;this.drag=null;if(d?.kind==='note'||cancel){this.release(this.voice);this.voice=null;}if(!d||cancel){this.changed();return;}if(d.kind==='palette'){if(!d.moved&&d.d<8)this.audition(9,d.d);else if(d.point){const i=this.noteRects.findIndex(b=>this.hit(b,...d.point));if(i>=0){this.position=i;const pitch=d.d>=8?5:this.pitchAt(d.point[1],i);this.write(pitch,d.d);if(d.d<8)this.audition(pitch,d.d);}}}this.changed();}
  drawPalette(surface){
    if(!this.enabled)return;
    const s=this.store,t=this.tables,small=this.advanced?1:0,rects=small?t.advanced_duration_rects:t.intro_duration_rects;
    surface.rect(129,111,102,29,0xffffffff);
    for(let i=0;i<rects.length;i++){
      const d=t.duration_values[small][i],x=rects[i][1]+t.duration_x_offset[16*small+i],y=rects[i][0]+t.duration_y_offset[16*small+i],color=d===this.duration[small]?0xff0000aa:0xff000000;
      const glyph=(id,xx,yy)=>surface.blit(s.shape('modules',id),[0,color],xx,yy,10);
      if(d>=8){glyph(2312+d,x,y);continue;}
      glyph((d<3?2303:2305)+small,x,y);
      if(d)surface.rect(x+(small?4:9),y-(small?10:16),1,small?11:18,color);
      if(d>=5)for(let n=0;n<(d===7?2:1);n++)glyph(small?2308:2307,x+(small?5:10),y-(small?9:15)+n*(small?3:5));
      if([1,3,5].includes(d))glyph(small?2312:2311,x+(small?6:11),y+3);
    }
  }
  drawPrint(surface,raw,title,instrument,songId=0){
    const s=this.store,m=this.mode,t=s.data.music,black=0xff000000,white=0xffffffff;
    const [top,left,bottom,right]=m?[68,6,166,317]:[80,60,134,264],clip=[top,left,bottom,right];
    surface.draw(s,'modules',2297+m,2296,0,0,2);
    const box=[top-34,left,top-8,left+29],group=t.followup.fact_icon_groups[instrument]?2075:2050;
    const id=s.palette('modules',group).first+t.followup.fact_icon_indices[instrument]-1,shape=s.shape('modules',id);
    surface.rect(left,top-34,29,26,white);surface.draw(s,'modules',id,group,left+14-Math.floor(shape.w/2),top-21-Math.floor(shape.h/2));
    surface.rect(left,box[0],29,1,black);surface.rect(left,box[2]-1,29,1,black);surface.rect(left,box[0],1,26,black);surface.rect(left+28,box[0],1,26,black);
    const code=t.song_icons[this.enabled?0:songId+1],pal=2100+20*(code>>4);
    surface.draw(s,'modules',s.palette('modules',pal).first+(code&15)-1,pal,left+34,top-32,2);
    surface.text(s,title,left+60,top-26,black,s.data.heading_font,1);
    surface.rect(left,top,right-left,bottom-top,white);
    const glyph=(id,x,y)=>surface.blit(s.shape('modules',id),[0,black],x,y,10,clip);
    const rect=(x,y,w,h)=>{const r=Math.min(right,x+w),b=Math.min(bottom,y+h);x=Math.max(left,x);y=Math.max(top,y);if(r>x&&b>y)surface.rect(x,y,r-x,b-y,black);};
    for(let row=0;row<=m;row++){const y=top+1+53*row;rect(left,y,1,33);for(let n=0;n<5;n++)rect(left,y+8*n,right-left+1,1);glyph(2301,left+2,y-2);}
    for(let i=0;i<raw[m];i++){
      const p=raw[5+2*i]&127,f=raw[5+2*i]>>7,d=raw[6+2*i];if(p===127)continue;
      const baseline=(m?106:118)+53*Math.floor(i/(m?15:8)),slot=(m?28:86)+(m?19:22)*(i%(m?15:8));
      if(d>=8){glyph(2312+d,slot+[3,3,3,6,6,5,5,5][d-8],baseline-37+[8,14,14,11,11,12,12,12][d-8]);continue;}
      const dy=t.notation.normal_y_offsets[f][p],x=slot+6,y=baseline-dy;
      if(p<=1-f)rect(x-3,y+3,17,1);
      if(t.notation.accidentals[p])glyph(f?2315:m?2314:2313,x-(f||m?5:6),y-(f?4:m?1:2));
      if([1,3,5].includes(d))glyph(2311,x+11,y+(dy%8?3:0));
      if(d){const up=p<12;rect(up?x+9:x,up?y-16:y+5,1,18);if(d>=5)for(let n=0;n<(d===7?2:1);n++)glyph(up?2307:2309,up?x+10:x+1,up?y-15+6*n:y+16-6*n);}
      glyph(d<3?2303:2305,x,y);
      if(this.enabled&&!m){const label=t.note_letters[f][p]+(t.notation.accidentals[p]?(f?'b':'#'):''),font=s.data.heading_font,w=[...label].reduce((n,c)=>n+font[c.charCodeAt(0)][0]+1,0);surface.text(s,label,x+5-Math.floor(w/2),baseline+9,black,font,1,clip);}
    }
  }
  drawMarker(surface,playing){if(!this.editable||playing)return;const t=this.tables,b=(this.advanced?t.advanced_markers:t.intro_markers)[this.position+1],id=this.advanced?(this.position<15?2319:2318):2317;surface.blit(this.store.shape('modules',id),[0,0xff00aa00],b[1]+(this.advanced?4:6),b[0]+(this.advanced?0:4),10);}
  drawDrag(surface){const drag=this.drag;if(drag?.kind!=='palette'||!drag.moved||!drag.point)return;const [x,y]=drag.point,d=drag.d,small=Number(this.advanced),color=0xff000000,glyph=(id,xx,yy)=>surface.blit(this.store.shape('modules',id),[0,color],xx,yy,10);
    if(d>=8){glyph(2312+d,x,y);return;}glyph((d<3?2303:2305)+small,x,y);if(d)surface.rect(x+(small?4:9),y-(small?10:16),1,small?11:18,color);if(d>=5)for(let n=0;n<(d===7?2:1);n++)glyph(small?2308:2307,x+(small?5:10),y-(small?9:15)+n*(small?3:5));if([1,3,5].includes(d))glyph(small?2312:2311,x+(small?6:11),y+3);
  }
}
