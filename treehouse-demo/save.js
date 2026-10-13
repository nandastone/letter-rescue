"use strict";
// STATUS.DAT is three raw DOS memory ranges, with no header. Keep the imported
// bytes and patch only runtime values that actually change. Unknown words,
// inactive records, old handles and trailing bytes survive an untouched export.
class TreehouseSave {
  constructor(data){
    if(!(data instanceof Uint8Array)||data.length<2704)throw new Error('Choose a complete STATUS.DAT file (at least 2,704 bytes).');
    this.data=data.slice();this.view=new DataView(this.data.buffer);this.observed=new Map();this.warnings=[];
  }
  word(offset){return this.view.getUint16(offset,true);}
  signed(offset){return this.view.getInt16(offset,true);}
  valid(value,min,max,fallback,label){if(Number.isInteger(value)&&value>=min&&value<=max)return value;this.warnings.push(label);return fallback;}
  get(offset,min=0,max=1,fallback=0){return this.valid(this.word(offset),min,max,fallback,`Field ${offset.toString(16)}`);}
  track(key,value,write){const current=JSON.stringify(value);if(!this.observed.has(key)){this.observed.set(key,current);if(this.initialize)write();return;}if(this.observed.get(key)===current)return;write();this.observed.set(key,current);}
  observe(key,value){this.observed.set(key,JSON.stringify(value));}
  put(offset,value){this.view.setUint16(offset,value,true);}
  scalar(offset,value){this.track(`w${offset}`,value,()=>this.put(offset,value));}
  array(offset,values,byte=false){values.forEach((value,i)=>{const at=offset+i*(byte?1:2);this.track(`${byte?'b':'w'}${at}`,value,()=>{if(byte)this.data[at]=value;else this.put(at,value);});});}
  exportData(){return this.data.slice();}
}

// Activities stay lazily constructed; their saved fields are applied once on
// first entry. Live matches and animation timers are intentionally session state.
class GamePersistence {
  constructor(store){
    this.store=store;this.loaded=new Set();this.enabled=false;
    try{const saved=localStorage.getItem('treehouse-status-v1');if(saved){this.file=new TreehouseSave(bytes(saved));this.enabled=true;}}catch(_error){}
    this.file??=new TreehouseSave(bytes(store.data.status));
    this.file.initialize=!this.enabled;
    this.preferences={sound:true,printing:true,printer:0,advanced:false,speed:false};
    if(this.enabled)this.loadCore();
    else this.captureCore();
  }
  loadCore(){const f=this.file;
    musicEditor.enabled=!!f.get(0x5a);longScore=musicEditor.advanced=!!f.get(0x5c);repeatSong=!!f.get(0x5e);
    musicEditor.index=[f.valid(f.data[0x57],0,42,0,'Short song page'),f.valid(f.data[0x59],0,42,0,'Long song page')];
    this.listeningPages=[f.valid(f.data[0x56],0,24,0,'Listening page'),f.valid(f.data[0x58],0,24,0,'Listening page')];songId=this.listeningPages[Number(longScore)];
    this.preferences={advanced:!!f.get(0x60),sound:!!f.get(0x62,0,1,1),printing:!!f.get(0x64,0,1,1),printer:f.get(0x66),speed:!!f.get(0x6a)};
    audio.enabled=this.preferences.sound;$('sound').checked=audio.enabled;room.cloud=f.get(0x6c,0,6,5);
    instrument=currentMusicSong()[3];
    this.loadObjects();this.captureCore();
  }
  loadObjects(){const f=this.file,list=[],types=new Set(),count=f.get(0x8ea,0,21,0);
    for(let i=0;i<count;i++){const at=0x8ec+20*i,type=f.word(at),state=f.word(at+2),inside=f.word(at+4),rect=Array.from({length:4},(_,j)=>f.signed(at+6+2*j));
      if(type>20||inside>1||types.has(type)||rect[0]>=rect[2]||rect[1]>=rect[3]){f.warnings.push(`Room object ${i+1}`);continue;}
      if(type===15||type===7&&state===5)continue;types.add(type);
      const normalized=type===6?Math.max(1,Math.min(3,state%10)):[7,14].includes(type)?Math.max(1,Math.min(4,state)):1;
      list.push({type,state:normalized,inside:!!inside,rect,due:0});
    }
    resident.objects=list;if(!types.has(8))resident.create(8);balloon.hidden=!types.has(6);const b=list.find(o=>o.type===6);if(b){balloon.x=b.rect[1];balloon.y=b.rect[0];}
    for(const o of list)if(o.type===11||o.type===16)o.due=tick+(o.type===11?6+gameplayRandom.int(10):120+gameplayRandom.int(60))*60;
  }
  captureCore(){const f=this.file,p=this.preferences;
    this.listeningPages??=[songId,songId];if(this.lastSong!==undefined&&this.lastSong!==songId)this.listeningPages=[songId,songId];this.lastSong=songId;
    f.array(0x56,[this.listeningPages[0],musicEditor.index[0],this.listeningPages[1],musicEditor.index[1]],true);
    for(const [at,value]of [[0x5a,+musicEditor.enabled],[0x5c,+longScore],[0x5e,+repeatSong],[0x60,+p.advanced],[0x62,+audio.enabled],[0x64,+p.printing],[0x66,p.printer],[0x6a,+p.speed],[0x6c,room.cloud]])f.scalar(at,value);
    // Used flags may contain noncanonical nonzero bytes in original files.
    for(let m=0;m<2;m++)for(let i=0;i<43;i++){const at=m*43+i,used=musicEditor.used(m,i);f.track(`used${at}`,used,()=>{f.data[at]=+used;});}
    const objects=resident.objects.map(o=>({type:o.type,state:o.state,inside:+o.inside,rect:resident.bounds(o).slice()}));
    f.track('objects',objects,()=>{f.put(0x8ea,objects.length);objects.forEach((o,i)=>{const at=0x8ec+20*i;f.put(at,o.type);f.put(at+2,o.state);f.put(at+4,o.inside);o.rect.forEach((v,j)=>f.put(at+6+2*j,v));});});
  }
  loadActivity(kind,activity){if(this.loaded.has(kind))return;this.loaded.add(kind);const f=this.file;
    if(this.enabled){
      if(kind==='nature'){
        const n=activity;n.time=f.get(0x6e);n.attribute=f.get(0x70,0,6);n.values=Array.from({length:7},(_,i)=>f.get(0x74+2*i,0,n.strings(5200+i).length-1));n.category=f.valid(f.signed(0x72),-1,8+n.time,-1,'Animal class');
        if(!n.availableClasses().has(n.category))n.category=-1;
        n.objects=[[],[]];for(let t=0;t<2;t++)for(let i=0;i<f.get(0x82+2*t,0,40);i++){const slot=2*i+t,id=f.word(0x86+2*slot),at=0x126+8*slot,rect=Array.from({length:4},(_,j)=>f.signed(at+2*j)),a=n.tables.animals[id];if(!a||a.active_time!==t){f.warnings.push('Placed animal');continue;}const s=this.store.shape('modules',a.large);if(rect[1]<131||rect[0]<5||rect[1]+s.w>315||rect[0]+s.h>195){f.warnings.push('Animal position');continue;}n.objects[t].push({id,x:rect[1],y:rect[0],blink:0,due:tick+120});}
        n.quiz.opponent=f.get(0x3b6,1,2,1);n.quiz.help=Array.from({length:3},(_,i)=>!!f.get(0x3b8+2*i));
      }else if(kind==='board'){
        activity.mode=f.get(0x3a6);activity.opponent=f.get(0x3a8,1,2,1);activity.savedLevels=Array.from({length:6},(_,i)=>f.get(0x3aa+2*i,0,2));activity.levels=[activity.savedLevels[3*activity.mode],activity.savedLevels[3*activity.mode+activity.opponent]];
      }else if(kind==='theater'){
        const t=activity;t.mixUp=!!f.get(0x3be);t.propsEnabled=!!f.get(0x3c0);t.selection=[8,8,6,4].map((n,i)=>f.valid(f.signed(0x3c2+2*i),-1,n-1,-1,'Sentence choice'));t.order=Array.from({length:4},(_,i)=>f.get(0x8a2+2*i,0,3,i));if(new Set(t.order).size!==4)t.order=[0,1,2,3];t.previousValidation=f.get(0x8e8,0,6);t.actorDrag=Array.from({length:7},(_,i)=>[f.signed(0x886+4*i),f.signed(0x888+4*i)]);
        t.props=Array.from({length:6},()=>[]);for(let place=0;place<6;place++)for(let i=0;i<f.get(0x3ca+2*place,0,20);i++){const slot=20*place+i,code=f.word(0x796+2*slot),palette=t.tables.prop_group[place]?3175:3145,id=palette+(code&255),at=0x3d6+8*slot,y=f.signed(at),x=f.signed(at+2);if((code>>8)!==t.tables.prop_group[place]||(code&255)<t.tables.prop_first[place]||(code&255)>=t.tables.prop_first[place]+t.tables.prop_count[place]||x<0||y<0||x>=320||y>=200){f.warnings.push('Theater decoration');continue;}t.props[place].push({id,palette,x,y});}
      }else if(kind==='maze'){
        activity.history=new Set(Array.from({length:24},(_,i)=>i).filter(i=>f.word(0x8aa+2*i)));const songs=Array.from({length:6},(_,i)=>f.get(0x8da+2*i,0,23,i));activity.savedSongs=new Set(songs).size===6?songs:null;
      }
    }
    if(kind==='maze'){activity.initialAdvanced=this.preferences.advanced;activity.hard=this.preferences.advanced;if(!this.enabled){activity.history=new Set(Array.from({length:24},(_,i)=>i).filter(i=>f.word(0x8aa+2*i)));const songs=Array.from({length:6},(_,i)=>f.get(0x8da+2*i,0,23,i));activity.savedSongs=new Set(songs).size===6?songs:null;}}
    this.captureActivity(kind,activity);
  }
  captureActivity(kind,a){const f=this.file;
    if(kind==='nature'){
      f.scalar(0x6e,a.time);f.scalar(0x70,a.attribute);f.scalar(0x72,a.category);f.array(0x74,a.values);f.scalar(0x3b6,a.quiz.opponent);f.array(0x3b8,a.quiz.help.map(Number));
      for(let t=0;t<2;t++){const list=a.objects[t];f.track(`animals${t}`,list.map(o=>[o.id,o.x,o.y]),()=>{f.put(0x82+2*t,list.length);list.forEach((o,i)=>{const slot=2*i+t,s=this.store.shape('modules',a.tables.animals[o.id].large);f.put(0x86+2*slot,o.id);[o.y,o.x,o.y+s.h,o.x+s.w].forEach((v,j)=>f.put(0x126+8*slot+2*j,v));});});}
    }else if(kind==='board'){
      a.savedLevels??=Array(6).fill(0);a.savedLevels[3*a.mode]=a.levels[0];a.savedLevels[3*a.mode+a.opponent]=a.levels[1];f.scalar(0x3a6,a.mode);f.scalar(0x3a8,a.opponent);f.array(0x3aa,a.savedLevels);
    }else if(kind==='theater'){
      f.scalar(0x3be,+a.mixUp);f.scalar(0x3c0,+a.propsEnabled);f.array(0x3c2,a.selection);f.array(0x8a2,a.order);f.scalar(0x8e8,a.previousValidation);f.array(0x886,a.actorDrag.flat());
      a.props.forEach((list,place)=>f.track(`props${place}`,list,()=>{f.put(0x3ca+2*place,list.length);list.forEach((o,i)=>{const slot=20*place+i,s=this.store.shape('modules',o.id);f.put(0x796+2*slot,((o.palette===3175?1:0)<<8)|(o.id-o.palette));[o.y,o.x,o.y+s.h,o.x+s.w].forEach((v,j)=>f.put(0x3d6+8*slot+2*j,v));});}));
    }else if(kind==='maze'){
      f.array(0x8aa,Array.from({length:24},(_,i)=>+a.history.has(i)));if(a.songs)f.array(0x8da,a.songs);
    }
  }
  capture(){this.captureCore();for(const [kind,a]of [['nature',nature],['board',boardgame],['theater',theater],['maze',maze]])if(a&&this.loaded.has(kind))this.captureActivity(kind,a);}
  save(){this.capture();try{let encoded='';for(let i=0;i<this.file.data.length;i+=8192)encoded+=String.fromCharCode(...this.file.data.subarray(i,i+8192));localStorage.setItem('treehouse-status-v1',btoa(encoded));}catch(_error){status('Your game is ready. This browser could not save it after closing.');}}
  exportData(){this.capture();return this.file.exportData();}
  importData(data){const file=new TreehouseSave(data);this.file=file;this.enabled=true;this.loaded.clear();this.lastSong=undefined;this.listeningPages=null;this.loadCore();resident.active=null;resident.actionPreparation=null;resident.clearingBalloon=false;resident.queue=[];resident.objectTask=null;resident.objectMotion=null;resident.objectSprite=null;resident.windowAnimation=null;resident.consuming=null;roomTravel=null;audio.stopAll();exterior.fresh(tick);resident.ambientAnimation=null;resident.pose=0;resident.wakeTime=null;resident.selected=false;resident.need('hunger',1+gameplayRandom.int(2));resident.need('fatigue',1+gameplayRandom.int(2));if(nature){nature.mode='explore';nature.eraseTask=null;nature.eraseEffect=null;nature.drag=null;nature.undo=null;nature.quiz.task=null;nature.quiz.candidateWait=false;nature.quiz.leadWait=false;nature.quiz.winAnimation=null;nature.quiz.options=true;}if(boardgame){boardgame.motion.cancel();boardgame.options=true;boardgame.played=false;boardgame.optionsBackground=null;}if(maze){maze.cancel();maze.started=false;}for(const [kind,a]of [['nature',nature],['board',boardgame],['theater',theater],['maze',maze]])if(a)this.loadActivity(kind,a);this.save();resident.save();if(theater)theater.save();return file.warnings;}
}
