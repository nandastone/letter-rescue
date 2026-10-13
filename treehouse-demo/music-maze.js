"use strict";
// Overlay 1 maze model and source-derived drawing/path tables. Captured images
// are used only by verification; this activity renders original resources.
class MusicMaze {
  constructor(store,{character,instrument,play,stop,sound,prepareSound=()=>0,stopSound=()=>{},changed,announce,leave,random=null}){
    Object.assign(this,{store,character,instrument,play,stop,sound,prepareSound,stopSound,changed,announce,leave,random});this.t=store.data.music.maze;this.music=store.data.music;this.tick=0;this.history=new Set();this.typeHistory=[0,0];this.patternHistory=Array.from({length:4},()=>[0,0]);this.familyHistory=0;this.supportedTypes=4;this.firstTimbre=true;this.mirrors=new Map();this.voice=null;this.audioQueue=[];this.motion=null;this.started=false;
  }
  pick(n){return this.random?Math.floor(this.random()*n):gameplayRandom.pick(n);}
  shuffle(values){const a=[...values];for(let i=a.length-1;i>0;i--){const j=this.pick(i+1);[a[i],a[j]]=[a[j],a[i]];}return a;}
  get activeSong(){return this.departureSong??this.songs[this.secret];}
  get song(){return this.store.data.songs[`modules:${this.activeSong}`];}
  get title(){return this.store.data.strings['modules:101'][this.activeSong];}
  get busy(){return !!this.motion;}
  get canGuess(){return this.earned>0&&!this.guessLocked&&this.phase==='play'&&!this.busy;}
  hit(b,x,y){return x>=b[1]&&x<b[3]&&y>=b[0]&&y<b[2];}
  replaceSong(){
    if(this.roundReplaced||!this.songs?.length)return;for(const song of this.songs)this.history.add(song);
    if(this.history.size===24){this.history.clear();for(const song of this.songs)this.history.add(song);}
    let song;do{song=this.pick(24);}while(this.history.has(song));this.history.add(song);this.songs[this.secret]=song;this.roundReplaced=true;
  }
  setupRound(){
    this.departureSong=null;this.secret=this.pick(6);this.eliminated=new Set();this.earned=0;this.streak=0;this.node=this.pick(9);this.excluded=2;this.phase='play';this.actor=[...this.t.centers[this.node]];this.actorAnimation=3;this.actorFrame=0;this.challenge(true);this.roundPrepared=true;this.introNode=this.node;
  }
  difficulty(hard){this.initialAdvanced=this.hard=!!hard;if(gameSave)gameSave.preferences.advanced=this.hard;}
  reset(entry=false){
    if(this.phase==='win')this.replaceSong();this.cancel();this.roller=null;this.falling=null;this.landed=null;this.dimOther=null;this.guessHighlight=-1;
    if(this.savedSongs){this.songs=this.savedSongs.slice();this.savedSongs=null;this.songs.forEach(s=>this.history.add(s));}
    else if(!this.songs?.length){this.songs=[];while(this.songs.length<6){let song;do{song=this.pick(24);}while(this.history.has(song));this.history.add(song);this.songs.push(song);}}
    if(!this.started)this.hard=!!this.initialAdvanced;this.started=true;this.roundReplaced=false;this.roundPrepared=false;this.secret??=0;this.earned=0;this.frog=false;
    if(entry||!this.introduced){const tutor=!this.introduced;this.introduced=true;this.run(this.introduction(tutor));}else{this.setupRound();this.run(this.roundEntry());}this.announce('Listen, then choose the sign that matches.');this.changed();
  }
  cancel(){this.stop(this.voice);this.voice=null;this.audioQueue=[];this.motion=null;this.loadingSound=false;this.chooser=false;this.drawerY=null;this.drawerSlots=null;this.questionBlank=false;this.currentEvent=null;this.tutoring=false;this.walking=false;this.accelerate=false;this.dismissAfterMotion=false;this.automaticListening=false;this.pointSprite=null;this.largeIntro=false;this.playerVisible=true;this.revealedSigns=4;this.frogPoint=null;this.frogAnimation=3;this.frogFrame=0;}
  cycle(mask,count,exclude=0){
    mask|=exclude;const start=this.pick(count);let choice=start;
    while(mask&(1<<choice)){choice=(choice+1)%count;if(choice===start)mask=exclude;}
    return [choice,mask|(1<<choice)];
  }
  challenge(first=false){
    this.wrong=new Set();this.wrongCount=0;this.guessLocked=false;this.feedback=-1;this.hint=false;this.actorAnimation=3;this.actorFrame=0;
    const hard=Number(this.hard);do{this.correct=this.pick(4);}while(this.correct===this.excluded);this.excluded=this.t.opposite_direction[this.correct];
    const exclude=this.t.enabled_types[hard].slice(0,this.supportedTypes).reduce((n,v,i)=>n|(!v<<i),0);
    if(first)this.type=this.firstTimbre?4:hard?2:1;
    else [this.type,this.typeHistory[hard]]=this.cycle(this.typeHistory[hard],this.supportedTypes,exclude);
    this.typeHistory[0]|=1<<this.type;this.typeHistory[1]|=1<<this.type;this.choices=Array(4);
    if(this.type===4){
      const families=this.music.followup.members,ambiguous=(a,b)=>a===b||[[20,21],[13,11],[17,7]].some(p=>p.includes(a)&&p.includes(b));
      if(hard){const a=this.pick(7);let b;do{b=this.pick(7);}while(a===b);for(const[f,d]of [[a,0],[b,1]]){const members=families[f];this.choices[d]=members[this.pick(members.length)];let value;do{value=members[this.pick(members.length)];}while(ambiguous(this.choices[d],value));this.choices[d+2]=value;}}
      else{let family;[family,this.familyHistory]=this.cycle(this.familyHistory,7);const members=families[family];this.choices[this.correct]=members[this.pick(members.length)];const used=new Set([family]);for(let d=0;d<4;d++){if(d===this.correct)continue;do{family=this.pick(7);}while(used.has(family));used.add(family);const members=families[family];this.choices[d]=members[this.pick(members.length)];}}
    }else{
      const key=['rhythm_sets','pitch_sets','melody_sets','accidental_sets'][this.type],sets=this.type===3?this.t[key][hard]:this.t[key],count=this.t.challenge_set_counts[hard][this.type];
      let set;[set,this.patternHistory[this.type][hard]]=this.cycle(this.patternHistory[this.type][hard],count);const answers=sets[set],used=new Set();this.choices[this.correct]=answers[0];
      for(let d=0;d<4;d++){if(d===this.correct)continue;let index;do{index=1+this.pick(3);}while(used.has(index));used.add(index);this.choices[d]=answers[index];}
    }
    this.resetIdle();
  }
  resetIdle(){this.targetDue=this.tick+360;this.hintDue=this.tick+900;}
  sampleTicks(key){const sample=this.store.data.pcm[key],q=Math.floor(1000000/sample.rate),rate=q>0&&q<256?Math.floor(1000000/q):sample.rate;return Math.ceil(bytes(sample.pcm).length/rate*(1193181/19886));}
  candidateEvents(direction,visible=false){const member=this.choices[direction];if(this.type===4)return[{pitch:9,instrument:member,finite:true,ticks:this.sampleTicks('voices:'+this.music.instruments[member].sound_id)}];const pitches=this.type===0?[9,9,9]:this.t[['','pitch_patterns','melody_patterns','accidental_patterns'][this.type]][member];return pitches.map((pitch,i)=>({pitch,instrument:9,ticks:this.type===0?this.t.sound_ticks[this.t.rhythm_patterns[member][i]]:25,sign:visible?direction:-1,note:i}));}
  sequence(events){this.stop(this.voice);this.voice=null;this.currentEvent=null;this.audioQueue=[...events];this.audioDue=this.tick;this.stepAudio();return events.reduce((n,e)=>n+e.ticks,0);}
  stepAudio(){if(this.tick<this.audioDue)return;this.stop(this.voice);this.voice=null;const e=this.audioQueue.shift();this.currentEvent=e||null;if(e){if(!e.rest)this.voice=this.play(e.pitch,e.instrument,e.finite);this.audioDue=this.tick+e.ticks;}}
  hearTarget(automatic=false){if(this.phase!=='play'||this.busy)return;this.run(this.listen(this.candidateEvents(this.correct),false,automatic));this.announce('Listen to the sound. Which sign matches?');}
  *listen(events,replay=false,automatic=false){this.automaticListening=automatic;this.replaying=replay;yield this.sequence(events);this.currentEvent=null;this.replaying=false;this.automaticListening=false;if(automatic)this.targetDue=this.tick+360;else this.resetIdle();}
  melody(full=false,song=this.song){const count=full?song[1]:this.earned;return Array.from({length:count},(_,i)=>({pitch:song[5+2*i]&127,rest:song[6+2*i]>=8,instrument:9,scoreIndex:i,ticks:this.music.tempo_factors[song[2]]*this.music.duration_factors[song[6+2*i]]})).filter(e=>e.pitch!==127);}
  *emptyReplay(){this.replaying=true;yield 12;this.replaying=false;this.resetIdle();}
  hearSong(){if(this.busy)return;this.run(this.listen(this.melody(this.phase==='win'),true));this.announce(this.phase==='win'?this.title:`Listen to your ${this.earned} collected notes.`);}
  run(generator){this.motion=generator;this.motionDue=this.tick;this.update(this.tick);this.changed();}
  choose(direction){if(this.phase!=='play'||this.busy||this.chooser||this.wrong.has(direction))return;this.run(this.choiceSequence(direction));}
  *animateActor(actor,animation){const count=this.t.animation_count[animation][actor];for(let frame=0;frame<count;frame++){if(actor){this.frogAnimation=animation;this.frogFrame=frame;}else{this.actorAnimation=animation;this.actorFrame=frame;}yield Math.max(1,this.t.animation_delay[animation]);}if(actor){this.frogAnimation=3;this.frogFrame=0;}else{this.actorAnimation=3;this.actorFrame=0;}}
  *appear(point){this.frog=true;this.frogPoint=[...point];this.sound(10033);yield* this.animateActor(1,13);yield 12;}
  *disappear(){this.sound(10034);yield* this.animateActor(1,14);this.frog=false;}
  *disappointed(){yield 30;for(let n=0;n<2;n++){this.frogAnimation=15;this.sound(10051);yield 10;this.frogAnimation=3;yield 10;this.frogAnimation=16;this.sound(10052);yield 10;this.frogAnimation=3;yield 10;}yield 30;}
  *jumps(actor,count){for(let n=0;n<count;n++){this.sound(10045);yield* this.animateActor(actor,9);this.sound(10046);yield 12;}}
  frogVoice(){this.sound(20100+this.pick(4));}
  *pointFrog(target){const [fy,fx]=this.frogPoint,cx=fx,cy=fy-19,[ty,tx]=target,right=tx>cx;yield* this.animateActor(1,right?12:11);let x=right?cx+(ty>cy?10:8):cx-(ty<cy?22:21),y=right?fy+1-(ty>cy?11:18):fy+1-(ty<cy?18:10);const id=(right?ty>cy:ty<cy)?22050:22051,dx=Math.abs(tx-x),dy=Math.abs(ty-y),sx=Math.sign(tx-x),sy=Math.sign(ty-y);let error=dx?Math.floor(dx/2):-1,n=0;this.sound(1016);for(;;){const end=x===tx&&y===ty;if(end||n%8===0){this.pointSprite={id,x,y};yield 1;}if(end)break;if(error>=0){x+=sx;error-=dy;}else{y+=sy;error+=dx;}n++;}this.pointSprite=null;this.frogAnimation=3;}
  *introduction(tutor=true){this.tutoring=tutor;this.introNode=null;this.stop(this.voice);this.audioQueue=[];this.node=9;this.phase='intro';this.largeIntro=true;this.frog=true;this.frogPoint=[150,42];this.playerVisible=true;this.frogVoice();yield* this.walk(9,1,true);this.frogVoice();yield* this.walkFrogLeft(78);if(!tutor){this.frogVoice();yield* this.walk(9,0,false);}this.setupRound();const node=this.node;this.largeIntro=false;if(!tutor){yield* this.roundEntry();return;}this.playerVisible=false;this.revealedSigns=0;this.frog=true;yield* this.walk(node,2,true,1);for(let d=0;d<4;d++){const [y,x]=this.t.sign_positions[node][d];yield* this.pointFrog([y+(d===1?23:13),x+14]);this.revealedSigns=d+1;yield this.sequence(this.candidateEvents(d,true));yield 30;}yield 90;yield this.sequence(this.candidateEvents(this.correct));yield 30;this.frogVoice();yield* this.walk(node,this.correct,false,1);this.frog=false;this.tutoring=false;this.playerVisible=true;yield* this.roundEntry();}
  *roundEntry(){this.frogVoice();this.playerVisible=true;this.revealedSigns=4;yield* this.walk(this.node,2,true);yield this.sequence(this.candidateEvents(this.correct));this.resetIdle();}
  *walkFrogLeft(distance){this.frogAnimation=4;this.frogFrame=0;yield this.t.animation_delay[4];for(let n=0;n<distance;n+=2){this.frogPoint[1]-=2;this.frogFrame++;yield this.t.animation_delay[4];}this.frog=false;this.frogAnimation=3;this.frogFrame=0;}
  *choiceSequence(direction){
    this.feedback=direction;yield 12;this.feedback=-1;yield this.sequence(this.candidateEvents(direction,true));yield 12;
    yield* this.appear(this.t.sign_actor_targets[this.node][direction]);
    if(direction!==this.correct){this.streak=0;this.difficulty(false);yield* this.disappointed();yield* this.disappear();this.wrong.add(direction);this.wrongCount++;this.announce('Try another sign. Listen again.');if(this.wrongCount>=2)yield* this.flashHint();this.resetIdle();return;}
    this.streak++;if(this.streak===2)this.difficulty(true);this.announce('That matches! You found another note.');this.dimOther=direction;yield* this.pointFrog([106,67]);yield* this.reward();yield 24;yield* this.disappear();yield 60;this.earned++;this.landed=null;
    if(this.earned>=this.song[0]){yield* this.drawer(true);this.guessHighlight=this.secret;yield this.sequence(this.melody());yield 12;yield* this.drawer(false);yield* this.jumps(0,1);yield* this.victory();return;}
    yield this.sequence(this.melody());yield 12;this.sound(10045);yield* this.animateActor(0,8);this.sound(10046);yield 12;this.frogVoice();
    const node=this.node,next=this.t.neighbors[node][direction];yield* this.walk(node,direction,false);this.node=next;const incoming=this.t.opposite_direction[direction];this.dimOther=null;this.challenge();yield* this.walk(next,incoming,true);yield this.sequence(this.candidateEvents(this.correct));this.resetIdle();
  }
  *idleHint(){for(let d=0;d<4;d++){this.feedback=d;yield 12;this.feedback=-1;}this.hintDue=this.tick+900;}
  *winHint(){this.controlFlash=0;yield 18;this.controlFlash=null;yield 12;this.controlFlash=1;yield 18;this.controlFlash=null;this.hintDue=this.tick+900;}
  *flashHint(){for(let i=0;i<3;i++){this.hint=true;yield 12;this.hint=false;if(i<2)yield 12;}this.hintDue=this.tick+900;}
  *reward(){
    const index=this.earned,end=60+13*index+16;this.sound(1002);for(let x=60;x<=end;x++){this.roller=x;yield 1;}this.stopSound();yield 20;
    this.sound(1000);const raw=this.song[5+2*index],p=raw&127,f=raw>>>7,finish=147-(this.music.followup.music.pitch_y_offsets[2+f][p]||0);for(let y=107;y<=finish;y++){this.falling={index,y,landed:y===finish};if(y===finish)this.sound(10025);yield 2;}this.falling=null;this.landed=index;yield 20;this.sound(1002);for(let x=end;x>=60;x--){this.roller=x;yield 1;}this.stopSound();this.roller=null;
  }
  *walk(node,direction,incoming,actor=0){
    this.walking=true;this.accelerate=false;
    const path=this.t.walk_paths[node][direction].map(p=>[...p]);if(path.length)path[path.length-1][1]+=this.t.offscreen_walk_extension[path[path.length-1][0]];
    const point=[...this.t.centers[node]];if(actor)this.frogPoint=point;else this.actor=point;
    if(incoming){for(const[d,n]of path){point[0]+=this.t.direction_vectors[d][0]*n;point[1]+=this.t.direction_vectors[d][1]*n;}path.reverse();for(const segment of path)segment[0]=this.t.opposite_direction[segment[0]];}
    for(const[d,distance]of path){const animation=this.t.walking_animation_ids[d];if(actor){this.frogAnimation=animation;this.frogFrame=0;}else{this.actorAnimation=animation;this.actorFrame=0;}let left=distance;if(!this.accelerate)yield Math.max(1,this.t.animation_delay[animation]);while(left>0){const step=Math.min(left,this.t.step_size[d]);left-=step;point[0]+=this.t.direction_vectors[d][0]*step;point[1]+=this.t.direction_vectors[d][1]*step;if(actor)this.frogFrame++;else this.actorFrame++;if(!this.accelerate)yield Math.max(1,this.t.animation_delay[animation]);}}
    this.walking=false;this.accelerate=false;
    if(actor){this.frogAnimation=3;this.frogFrame=0;}else{this.actorAnimation=3;this.actorFrame=0;}
  }
  *drawer(open){const delay=this.prepareSound(open?1004:1003);if(delay>0){this.loadingSound=true;yield delay;this.loadingSound=false;}if(open){this.drawerSlots=new Set(Array.from({length:6},(_,i)=>i).filter(i=>!this.eliminated.has(i)));this.questionBlank=false;}this.chooser=true;this.sound(open?1004:1003);for(let y=open?106:62;open?y>=60:y<=106;y+=open?-2:2){this.drawerY=y;yield 2;}this.drawerY=null;this.chooser=open;if(!open){this.guessHighlight=-1;this.questionBlank=false;this.resetIdle();}}
  openGuess(){if(!this.canGuess)return;this.stop(this.voice);this.audioQueue=[];this.run(this.drawer(true));}
  closeGuess(){if(this.busy){this.dismissAfterMotion=true;this.interrupt();return;}this.run(this.drawer(false));}
  interrupt(){if(this.loadingSound)return;if(this.tutoring){if(!this.roundPrepared)this.setupRound();const node=this.introNode;this.cancel();this.node=node;this.frog=false;this.run(this.roundEntry());return;}if(this.walking){this.accelerate=true;this.motionDue=this.tick;return;}if(this.currentEvent){this.stop(this.voice);this.voice=null;this.audioQueue=[];this.currentEvent=null;this.audioDue=this.tick;this.motionDue=this.tick;return;}if(this.motion)this.motionDue=this.tick;}
  guess(slot){if(!this.chooser||this.eliminated.has(slot)||this.busy)return;this.run(this.guessSequence(slot));}
  *guessSequence(slot){this.guessHighlight=slot;yield this.sequence(this.introMelody(slot));this.guessLocked=true;this.questionBlank=true;if(slot===this.secret){this.sound(1005);yield this.sampleTicks('digisnd:1005');yield* this.drawer(false);yield* this.jumps(0,this.song[0]-this.earned);yield* this.victory();}else{this.eliminated.add(slot);yield* this.appear([135,197]);yield* this.disappointed();yield* this.disappear();yield* this.drawer(false);this.announce('That is a different song. Find another note before guessing again.');}}
  introMelody(slot){const song=this.store.data.songs[`modules:${this.songs[slot]}`];return Array.from({length:song[0]},(_,i)=>({pitch:song[5+2*i]&127,rest:song[6+2*i]>=8,instrument:9,scoreIndex:i,ticks:this.music.tempo_factors[song[2]]*this.music.duration_factors[song[6+2*i]]})).filter(e=>e.pitch!==127);}
  *victory(){this.chooser=false;yield 24;yield* this.appear(this.t.sign_actor_targets[this.node][1]);yield* this.jumps(1,1);this.frogVoice();this.frogAnimation=5;for(let i=0;i<36;i++){this.frogPoint[0]-=2;this.frogFrame++;yield this.t.animation_delay[5];}this.frog=false;this.frogVoice();yield* this.walk(this.node,1,false);this.node=9;this.phase='arrival';this.actor=[150,162];this.actorAnimation=3;this.actorFrame=0;this.frog=true;this.frogPoint=[150,130];this.frogAnimation=3;this.frogFrame=0;this.earned=this.song[0];yield* this.walk(9,3,true);yield this.sequence(this.melody(true));this.phase='win';this.hintDue=this.tick+900;this.announce(`You found ${this.title}! Play it again, or start a new maze.`);}
  newGame(){if(this.busy)return;this.run(this.endControl(true));}
  returnMusic(){if(this.busy)return;this.run(this.endControl(false));}
  *endControl(again){this.departureSong=this.activeSong;this.replaceSong();this.controlFlash=again?0:1;yield 18;this.controlFlash=null;this.frogVoice();if(again){yield* this.walkFrogLeft(this.t.walk_paths[9][0].reduce((n,p)=>n+p[1],0)+this.t.offscreen_walk_extension[this.t.walk_paths[9][0].at(-1)[0]]);this.frogVoice();yield* this.walk(9,0,false);this.reset();}else{yield* this.walk(9,1,false);this.leave('music');}}
  update(tick){this.tick=tick;let dirty=false;if(this.audioQueue.length||this.voice){if(tick>=this.audioDue){this.stepAudio();dirty=true;}}
    if(this.motion&&tick>=this.motionDue){const motion=this.motion,step=motion.next();if(this.motion===motion){if(step.done){this.motion=null;this.changed();}else this.motionDue=tick+Math.max(1,step.value||1);}dirty=true;}
    if(!this.busy&&this.dismissAfterMotion){this.dismissAfterMotion=false;if(this.chooser)this.closeGuess();}
    if(!this.busy&&this.phase==='win'&&tick>=this.hintDue){this.run(this.winHint());dirty=true;}
    if(!this.busy&&this.phase==='play'&&!this.chooser){if(tick>=this.hintDue){this.run(this.idleHint());dirty=true;}else if(tick>=this.targetDue){this.hearTarget(true);dirty=true;}}return dirty;
  }
  activateControl(index){const r=this.t.ui_rects[index];this.click((r[1]+r[3])/2,(r[0]+r[2])/2);}
  click(x,y){const r=this.t.ui_rects;if(this.hit(r[0],x,y)){this.leave('inside');return;}if(this.hit(r[1],x,y)&&this.phase!=='win'){this.leave('music');return;}
    // The original automatic audition returns to the main input loop with
    // its interrupting click still pending (58F1 -> 524A).
    if(this.busy&&this.automaticListening){this.interrupt();this.motion.next();this.motion=null;}
    if(this.busy){this.interrupt();return;}if(this.phase==='win'){if(this.hit(r[7],x,y))this.newGame();else if(this.hit(r[6],x,y)||this.hit(r[2],x,y))this.returnMusic();else if(this.hit(r[8],x,y))this.hearSong();else this.run(this.winHint());return;}
    if(this.chooser){for(let i=0;i<6;i++)if(this.hit([66+23*Math.floor(i/3),101+25*(i%3),88+23*Math.floor(i/3),121+25*(i%3)],x,y)){this.guess(i);return;}this.closeGuess();return;}
    if(this.hit(r[3],x,y)){this.openGuess();return;}if(this.hit(r[4],x,y)){if(this.earned)this.hearSong();else this.run(this.emptyReplay());return;}
    for(let d=0;d<4;d++){const[y0,x0]=this.t.sign_positions[this.node][d];if(this.hit([y0,x0,y0+36,x0+29],x,y)){this.choose(d);return;}}this.hearTarget();
  }
  draw(surface){
    const s=this.store,t=this.t,g=this.music.followup.music,black=0xff000000,white=0xffffffff,gray=0xff555555;
    const draw=(id,pal,x,y,mode=10)=>surface.draw(s,'modules',id,pal,x,y,mode),glyph=(id,x,y,c=black)=>surface.blit(s.shape('modules',id),[0,c],x,y,10),rect=(x,y,w,h,c=black)=>surface.rect(x,y,w,h,c);
    const note=(raw,d,x,baseY,restX,restY,falling=false,highlight=false)=>{const color=highlight?0xff5555ff:black,glyph=(id,x,y)=>surface.blit(s.shape('modules',id),[0,color],x,y,10),rect=(x,y,w,h)=>surface.rect(x,y,w,h,color);const p=raw&127,f=raw>>>7;if(p===127)return;const off=g.pitch_y_offsets[2+f][p],y=baseY-off;if(d>=8){glyph(2312+d,restX+g.rest_x_offset[0][d-8],restY+g.rest_y_offset[0][d-8]);return;}if(p<=1-f&&!falling)rect(x-2,y+2,9,1);if(this.music.notation.accidentals[p])glyph(f?2316:2314,x-(f?4:5),y-(f?2:1));if([1,3,5].includes(d))glyph(2312,x+6,y+(off%6?3:0));if(d){if(p<12)rect(x+4,y-10,1,11);else rect(x,y+4,1,11);}if(d>=5)for(let i=0;i<(d===7?2:1);i++)glyph(p<12?2308:2310,p<12?x+5:x+1,p<12?y-9+3*i:y+10-3*i);glyph(d<3?2304:2306,x,y);};
    const icon=(song,x,y)=>{const code=this.music.song_icons[song+1],pal=2100+20*((code&0xf7)>>>4);draw(s.palette('modules',pal).first+(code&15)-1,pal,x,y,2);};
    draw(2341+this.node,2340,0,0,2);if(!this.largeIntro)surface.draw(s,'th',8,6,304,1);
    if(this.phase==='win'||this.phase==='arrival'||this.largeIntro){
      if(!this.largeIntro){icon(this.activeSong,30,16);surface.text(s,this.title,55,25);}rect(30,37,212,75,white);
      for(let r=0;r<2;r++){for(let j=0;j<5;j++)rect(30,38+39*r+6*j,211,1);rect(30,38+39*r,1,25);glyph(2302,32,37+39*r);}
      for(let i=0;i<(this.largeIntro?0:this.song[1]);i++)note(this.song[5+2*i],this.song[6+2*i],52+13*(i%15),66+39*Math.floor(i/15),47+13*(i%15),38+39*Math.floor(i/15),false,this.currentEvent?.scoreIndex===i);
      rect(1,96,27,24,this.controlFlash===0?0xff5555ff:white);draw(2357,2340,2,101);rect(272,54,27,24,this.controlFlash===1?0xff5555ff:white);draw(2358,2340,273,56);
    }else{
      surface.draw(s,'th',7,6,280,1);draw(2351,2340,55,107,2);draw(2353,2340,this.roller??60,104);for(let j=0;j<5;j++)rect(65,119+6*j,122,1);rect(65,119,1,25);glyph(2302,67,118);
      rect(189,136,13,16,this.replaying?0xff5555ff:this.earned?white:0xffaaaaaa);glyph(2336,189,136);if(this.earned&&!this.guessLocked)glyph(2335,189,119);
      for(let i=0;i<this.earned+(this.landed!=null?1:0);i++)note(this.song[5+2*i],this.song[6+2*i],87+13*i,147,82+13*i,119,false,this.currentEvent?.scoreIndex===i);
      if(this.falling){const i=this.falling.index,p=this.song[5+2*i],off=g.pitch_y_offsets[2+(p>>>7)][p&127]||0;note(p,this.song[6+2*i],87+13*i,this.falling.y+off,82+13*i,this.falling.y,!this.falling.landed);}
      for(let d=0;d<4;d++){
        const[y,x]=t.sign_positions[this.node][d],member=this.choices[d],yy=y+(d===1?10:0),fill=this.feedback===d||this.hint&&this.correct===d?0xff5555ff:this.wrong.has(d)||(this.dimOther!=null&&d!==this.dimOther)?0xffaaaaaa:white;
        rect(x,y,29,36);rect(x+1,y+1,29,36);rect(x+1,y+1,27,34,white);draw(2352,2340,x+9,y+37);rect(x,y+(d===1?10:25),29,1);glyph(2328+d,x+10,y+(d===1?2:27));
        if(d>=(this.revealedSigns??4))continue;
        if(this.type===4){rect(x,yy,29,26);rect(x+1,yy+1,27,24,fill);const f=this.music.followup,pal=f.fact_icon_groups[member]?2075:2050,id=s.palette('modules',pal).first+f.fact_icon_indices[member]-1,shape=s.shape('modules',id);draw(id,pal,x+14-Math.floor(shape.w/2),yy+13-Math.floor(shape.h/2));}
        else{rect(x+1,yy+1,27,24,fill);for(let j=0;j<5;j++)rect(x+2,yy+2+5*j,25,1,gray);rect(x+2,yy+2,1,21,gray);const pitches=this.type===0?[9,9,9]:t[['','pitch_patterns','melody_patterns','accidental_patterns'][this.type]][member];pitches.forEach((p,n)=>{const duration=this.type===0?t.rhythm_patterns[member][n]:0,f=this.type===3?t.accidental_flags[member][n]:0,a=this.music.notation.accidentals[p],gx=x+2+([0,2].includes(this.type)?3+7*n:this.type===1?5+10*n:7+12*n-(a?f:2)),gy=yy+2+t.challenge_note_y[f][p];const color=this.currentEvent?.sign===d&&this.currentEvent.note===n?0xff5555ff:black;glyph(2332+(p>=11?2:0)+duration,gx,gy,color);if(a)glyph(2314+2*f,gx+f-5,gy-f+8,color);});}
      }
    }
    if(this.playerVisible!==false)this.drawActor(surface,0,this.actor,this.actorAnimation,this.actorFrame);if(this.frog)this.drawActor(surface,1,this.frogPoint||[150,130],this.frogAnimation??3,this.frogFrame??0);if(this.pointSprite){const v=this.pointSprite;surface.draw(s,'th',v.id,22000,v.x,v.y);}
    if(this.chooser){const bar=this.drawerY??60,clip=[60,95,112,177];surface.draw(s,'modules',2355,2340,95,bar+4,2,clip);surface.draw(s,'modules',2354,2340,95,bar,10,clip);for(let i=0;i<6;i++)if(this.drawerSlots?this.drawerSlots.has(i):!this.eliminated.has(i)){const x=101+25*(i%3),y=bar+6+23*Math.floor(i/3),code=this.music.song_icons[this.songs[i]+1],pal=2100+20*(code>>4);if(this.guessHighlight===i){const top=Math.max(60,y-2),bottom=Math.min(112,y+24);if(bottom>top)rect(x-2,top,24,bottom-top,0xff5555ff);}surface.draw(s,'modules',s.palette('modules',pal).first+(code&15)-1,pal,x,y,2,clip);}draw(2356,2340,95,107);rect(189,119,13,16,this.questionBlank?white:0xff5555ff);if(!this.questionBlank)glyph(2335,189,119);}

  }
  drawActor(surface,actor,point,animation,frame){const t=this.t,archive=actor?'th':this.character(),pal=actor?22000:20000,count=t.animation_count[animation][actor]||1,n=frame%count,index=t.animation_first[animation][actor]+(t.animation_reverse[animation]?count-1-n:n),id=this.store.palette(archive,pal).first+index;let shape=this.store.shape(archive,id);
    if(t.animation_mirror[animation]){const key=`${archive}:${id}`;if(!this.mirrors.has(key)){const pixels=new Uint8Array(shape.pixels.length);for(let y=0;y<shape.h;y++)for(let x=0;x<shape.w;x++)pixels[y*shape.w+x]=shape.pixels[y*shape.w+shape.w-1-x];this.mirrors.set(key,{w:shape.w,h:shape.h,pixels});}shape=this.mirrors.get(key);}
    surface.blit(shape,this.store.palette(archive,pal).rgba,point[1]-17,point[0]-(actor?38:40),10);
  }
}
