"use strict";
const $=id=>document.getElementById(id);
const store=new ResourceStore(ORIGINAL),screen=new Surface(),canvas=$("game"),ctx=canvas.getContext("2d",{alpha:false});
ctx.imageSmoothingEnabled=false;
// Original scene initializer 0x59C0 recolors the second character's clothing.
store.palette("th",8001).rgba[9]=0xffff8a10;store.palette("th",8001).rgba[10]=0xffaa5d08;
const music=ORIGINAL.music,NOTE_NAMES=["C","C sharp","D","D sharp","E","F","F sharp","G","G sharp","A","A sharp","B","C","C sharp","D","D sharp","E"];
const BLACK=new Set([1,3,6,8,10,13,15]);
const WHITE=[0,2,4,5,7,9,11,12,14,16];
const TICK_HZ=1193181/19886;

class OriginalAudio {
  constructor(){this.context=null;this.buffers=new Map();this.active=new Map();this.preparedSamples=new Set();this.enabled=true;this.serial=0;this.order=0;this.errors=[];}
  prepareDecoder(key){
    const data=ORIGINAL.pcm[key];if(!data||this.preparedSamples.has(key))return 0;
    this.preparedSamples.add(key);
    return data.decode_cycles*TICK_HZ/(1000*ORIGINAL.platform.cpu_cycles_per_millisecond);
  }
  async unlock(){
    if(!this.context){const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio){status("This browser cannot play audio.");return;}this.context=new Audio({sampleRate:48000});}
    if(this.context.state!=="running")await this.context.resume();
    // Module loading must not hold up game input or discard a quick click.
    // Commands are retained until the channel is ready, including cancellations.
    this.prepareContext().catch(error=>{this.errors.push(String(error));this.active.clear();status('Audio could not start. Reload to retry.');});
  }
  async prepareContext(context=this.context){
    if(this.rendererContext===this.context)return this.preparing;
    this.renderer?.disconnect();this.outputGain?.disconnect();this.renderer=null;this.outputGain=null;this.rendererContext=this.context;
    const owner=this.context;this.pendingCommands=[];this.loadedSamples=new Set();
    this.preparing=(async()=>{
      if(context.sampleRate!==48000)throw new Error("Original audio requires a 48 kHz rendering context");
      await context.audioWorklet.addModule('data:application/javascript,'+encodeURIComponent(originalAudioWorkletSource()));
      if(this.rendererContext!==owner)return;
      const node=new AudioWorkletNode(context,'treehouse-digital-channel',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[1]});
      node.onprocessorerror=()=>{this.errors.push('Original audio processor failed');this.active.clear();status('Audio playback stopped. Reload to restart it.');};
      const gain=context.createGain();gain.gain.value=1;node.connect(gain);gain.connect(context.destination);
      this.barriers=new Map();node.port.onmessage=({data})=>{if(data.ended!==undefined)this.active.delete(data.ended);if(data.barrier!==undefined){this.barriers.get(data.barrier)?.();this.barriers.delete(data.barrier);}};
      this.renderer=node;this.outputGain=gain;for(const voice of this.active.values())voice.gain=gain;
      for(const command of this.pendingCommands)node.port.postMessage(command);this.pendingCommands=[];
    })();return this.preparing;
  }
  buffer(key){
    if(this.buffers.has(key))return this.buffers.get(key);const data=ORIGINAL.pcm[key];
    if(!data)throw new Error(`Missing decoded sample ${key}`);
    const samples=bytes(data.pcm),buffer=this.context.createBuffer(1,samples.length,data.rate),channel=buffer.getChannelData(0);
    for(let i=0;i<samples.length;i++)channel[i]=(samples[i]-128)/128;this.buffers.set(key,buffer);return buffer;
  }
  rate(requested){const q=Math.floor(1000000/requested);return q>0&&q<256?Math.floor(1000000/q):requested;}
  renderRate(rate){return Math.floor(rate*16384/48000)*48000/16384;}
  async flushCommands(){await this.preparing;return new Promise(resolve=>{const token=++this.order;this.barriers.set(token,resolve);this.renderer.port.postMessage({type:'barrier',token});});}
  post(command){if(this.renderer)this.renderer.port.postMessage(command);else this.pendingCommands.push(command);}
  command(type,id,when,extra={}){this.post({type,id,frame:Math.round(Math.max(this.context.currentTime,when??this.context.currentTime)*48000),order:++this.order,...extra});}
  start(key,rate=null,when=null,{loop=true}={}){
    if(ORIGINAL.pcm[key])this.preparedSamples.add(key);
    if(!this.context||!this.enabled||this.context.state!=="running"||this.rendererContext!==this.context)return null;
    const data=ORIGINAL.pcm[key];if(!data)return null;for(const id of [...this.active.keys()])this.stop(id,when);
    if(!this.loadedSamples.has(key)){this.post({type:'sample',key,pcm:bytes(data.pcm)});this.loadedSamples.add(key);}
    const effective=this.rate(rate||data.rate),renderRate=this.renderRate(effective),buffer=this.buffer(key),loopEnd=data.loop_end||buffer.length;
    const looping=!!(loop&&data.loop&&loopEnd>data.loop_start),id=++this.serial,start=when??this.context.currentTime;
    const source={buffer,loop:looping,loopStart:data.loop_start/data.rate,loopEnd:loopEnd/data.rate,playbackRate:{value:renderRate/data.rate}};
    const voice={source,gain:this.outputGain,key,rate:effective,renderRate,start,released:false};this.active.set(id,voice);
    this.command('start',id,start,{key,rate:effective,loop:looping,loopStart:data.loop_start,loopEnd});return id;
  }
  stop(id,when=null){if(!this.active.has(id))return;this.command('stop',id,when);this.active.delete(id);}
  release(id){const voice=this.active.get(id);if(!voice||voice.released)return;voice.released=true;this.command('release',id);}
  stopAll(){for(const id of [...this.active.keys()])this.stop(id);}
  stopSound(sound=0){for(const [id,voice]of this.active)if(!sound||voice.key===`digisnd:${sound}`||voice.key===`voices:${sound}`)this.stop(id);}
}
const audio=new OriginalAudio();
let scene="outside",character="boy",tick=0,animations=[],entering=false,transition=null;
let roomTravel=null;
let songId=20,instrument=11,songPosition=-1,songPlaying=false,songEvents=[],songCursor=0,songDue=0,songVoice=null;
let tempo=3,telescope=2,factIndex=0,recording=false,recorded=[],recordStart=0;
let audition=null,auditionVoice=null,musicAuditionPitch=null,musicAuditionDue=0,longScore=false,repeatSong=false;
const musicIdle={frame:-1,due:600};
let theater=null,nature=null,boardgame=null,maze=null;
let gameSave=null,preferences=null,statusOverlay=null;
const balloon={x:96,y:43,due:0,lifting:false};
const chalk=new Chalkboard(store,()=>{dirty=true;if(chalk.tool>=0){balloon.lifting=true;balloon.due=tick+2;}syncChalkTools();},()=>resident.scheduleAmbient());let chalkOpen=false;
let lastFrame=performance.now(),clockRemainder=0,dirty=true,failed=false;
let pointer=[160,100],pointerVisible=!matchMedia("(pointer: coarse)").matches;
const held=new Map(),pointers=new Map(),savedKey="treehouse-demo-melody-v1";
const downKeys=new Set(),pointerKeys=new Set();
let pointerKeyDue=0,pointerShift=false;
const stats={frames:0,notesPlayed:0,animationsCompleted:0,errors:[],songCompletions:0};
const musicEditor=new MusicEditor(store,{play:p=>playPitch(p),release:v=>audio.stop(v),changed:()=>{dirty=true;const p=$('note-position');if(p)p.value=musicEditor.position;const d=$('note-duration');if(d)d.value=musicEditor.duration[musicEditor.mode];},announce:status});
const room=new TreehouseRoom(store,{changed:()=>{dirty=true;if(scene==='inside')calendarPanel();},announce:status,speak:theaterSpeech,stopSound:id=>audio.stopSound(id),animate:id=>animation('th',id,id),balloon,calendarComplete:open=>{if(open)resident.scheduleAmbient();else resident.enterScene();},environmentComplete:()=>resident.scheduleAmbient()});
const resident=new RoomCharacter(store,{character:()=>character,scene:()=>scene,room,balloon,roomIdle:serviceBalloon,sound:theaterSpeech,stopSound:id=>audio.stopSound(id),changed:()=>{dirty=true;},announce:status});
const exterior=new TreehouseExterior(store,resident,room,{sound:theaterSpeech,stopSound:()=>audio.stopAll(),changed:()=>{dirty=true;},leave:()=>setScene('outside')});
const rewards=new TreehouseRewards(store,{character:()=>character,sound:theaterSpeech,grant:type=>{resident.create(type);resident.save();},changed:()=>{dirty=true;}});
resident.ambientAllowed=()=>chalk.tool<0&&!entering;
// Built-in songs retain separate speed/instrument/notation in each score mode.
// The original stores these in executable memory, outside STATUS.DAT.
const listeningBooks={songs:Array.from({length:2},(_,mode)=>Array.from({length:25},(_,id)=>{
  const song=[...ORIGINAL.songs[`modules:${id}`]];
  for(let field=0;field<3;field++)song[2+field]=music.listening_defaults[field][25*mode+id];
  return song;
}))};
let musicDialog=null,musicPrint=null;
const musicSelector=new MusicSelector(store,{current:()=>instrument,choose:id=>{releaseAll();instrument=id;currentMusicSong()[3]=id;if(musicEditor.enabled)musicEditor.save();factIndex=0;},play:()=>playPitch(9),stop:voice=>audio.stop(voice),changed:()=>{dirty=true;if(scene==='music')musicSelectorPanel();},leave:next=>{musicSelector.open=false;navigateScene(next);}});
function status(message){$("status").textContent=message;}
function draw(archive,id,palette,x=0,y=0,mode=10){screen.draw(store,archive,id,palette,x,y,mode);}
function text(value,x,y,color=0xff000000){screen.text(store,String(value),x,y,color);}
function animation(archive,id,palette,options={}) {
  const a=new Animation(store,archive,id,palette,{startTick:tick,onSound:id=>{a.soundDue=tick+theaterSpeech(id);},...options});
  a.soundDue=tick;a.update(tick);return a;
}
function button(label,action,primary=false) {
  const b=document.createElement("button");b.textContent=label;if(primary)b.className="primary";
  b.onclick=async()=>{await audio.unlock();if(roomTravel){navigateScene(scene);return;}if(['inside','outside','hollow'].includes(scene)&&(resident.interruptAudio()||room.interruptAudio()))return;if(scene==='telescope'&&interruptTelescope())return;if(scene==='nature'&&nature.mode==='quiz'&&nature.quiz.interruptWait())return;action();};return b;
}
function row(...buttons) {const r=document.createElement("div");r.className="button-row";r.append(...buttons);return r;}
function selectControl(label,id,options,value,change) {
  const wrap=document.createElement("div"),l=document.createElement("label"),s=document.createElement("select");
  l.className="control-label";l.htmlFor=id;l.textContent=label;s.id=id;
  for(const [v,name]of options){const o=document.createElement("option");o.value=v;o.textContent=name;s.append(o);}
  s.value=value;s.onchange=async()=>{await audio.unlock();change(Number(s.value));};wrap.append(l,s);return wrap;
}
function panel(chapter,heading,instructions,caption) {
  $("chapter").textContent=chapter;$("heading").textContent=heading;$("instructions").textContent=instructions;$("caption").textContent=caption;
  $("controls").replaceChildren();$("fact-card").hidden=true;$("touch-keys").hidden=scene!=="music";
  $("back").disabled=scene==="outside";$("scene-label").textContent={outside:"Outside the treehouse",inside:"Inside the treehouse",music:"The music room",maze:"The musical maze",telescope:"Through the telescope",theater:"The sentence theater",boardgame:"The board game",nature:"The nature activity",hollow:"The squirrels' home"}[scene];
  canvas.setAttribute("aria-label",`${heading} ${instructions}`);status("");
}
function stopPlayback(silent=false) {
  songPlaying=false;songPosition=-1;musicAuditionPitch=null;audio.stop(songVoice);songVoice=null;
  if(!silent)status("Song stopped.");
  updatePlayButton();dirty=true;
}
function releaseAll() {
  // Audio unlock can complete after focus loss. Clear the gesture markers it
  // checks as well as the notes that have already started.
  downKeys.clear();pointerKeys.clear();pointerShift=false;pointers.clear();
  for(const key of $('touch-keys').querySelectorAll('button')){delete key.dataset.pressed;delete key.dataset.keyHeld;}
  chalk.end();resident.end(true);theater?.endDrag(true);nature?.endDrag();musicEditor.end(true);
  for(const owner of [...held.keys()])noteUp(owner);
  audio.stopAll();
}
function chooseFriend(){if(roomTravel||resident.busy||scene==='inside'&&room.busy)return;resident.selected=false;exterior.fresh(tick);setScene('outside');}
function navigateScene(next){
  if(roomTravel){roomTravel.effect?.interrupt();resident.interruptAudio();if(roomTravel.phase==='pause')roomTravel.due=tick;return;}
  if(scene==='music'&&next==='maze'||scene==='maze'&&next==='music'){
    const returning=scene==='maze';
    stopPlayback(true);releaseAll();audition=null;audio.stopAll();
    if(returning)setScene('music');
    roomTravel={phase:'effect',maze:true,effect:new MazeTransition(store,{character,returning,tick,sound:id=>audio.start(`digisnd:${id}`),complete:()=>{roomTravel=null;if(!returning)setScene('maze');else musicIdle.due=tick+600;}})};
    dirty=true;return;
  }
  if(scene==='nature'&&nature.mode==='quiz'&&nature.quiz.interruptWait())return;
  if(scene==='telescope'&&interruptTelescope())return;
  if(['inside','outside','hollow'].includes(scene)&&(resident.interruptAudio()||room.interruptAudio()))return;
  if(['inside','outside'].includes(scene)&&(resident.busy||scene==='inside'&&room.busy)||entering)return;
  if(scene==='hollow'){if(resident.busy)return;setScene(next==='inside'?'outside':next);return;}
  const activities=['music','nature','theater','boardgame'];
  if(scene==='inside'&&(activities.includes(next)||next==='telescope')){
    if(resident.pose===4){resident.wake(true,()=>navigateScene(next));return;}
    releaseAll();roomTravel={next,phase:'prepare',telescope:next==='telescope'};
    if(next==='telescope')resident.action(19);else resident.center();
    updateRoomTravel();dirty=true;return;
  }
  if(next==='inside'&&(activities.includes(scene)||scene==='telescope'||scene==='maze')){
    if(scene==='nature'&&nature?.eraseTask)return;
    if(scene==='theater'&&!theater.exitReady){theater.leave(()=>navigateScene(next));return;}
    const previous=scene==='maze'?'music':scene;setScene('inside');
    roomTravel={next:'inside',returning:true,phase:'prepare',telescope:previous==='telescope',variant:activities.indexOf(previous)};
    if(previous==='telescope')resident.action(28);
    updateRoomTravel();dirty=true;return;
  }
  setScene(next);
}
function updateRoomTravel(){
  const t=roomTravel;if(!t)return;
  if(t.phase==='prepare'){
    // Activity returns rebuild the room and finish the return effect before
    // servicing overdue needs; telescope movement still owns its action here.
    if(!t.returning||t.telescope){resident.update(tick);if(resident.busy)return;}
    if(t.telescope){if(t.returning){roomTravel=null;return;}t.phase='pause';t.due=tick+60;return;}
    t.phase='effect';t.effect=new RoomTransition(store,{variant:t.returning?t.variant:['music','nature','theater','boardgame'].indexOf(t.next),returning:t.returning,tick,speak:theaterSpeech,stopSound:()=>audio.stopAll(),complete:()=>{roomTravel=null;if(t.returning)resident.postponeWarnings(tick);else{setScene(t.next);if(t.next==='theater')theater.enter();}}});
  }else if(t.phase==='pause'){if(tick>=t.due){roomTravel=null;setScene(t.next);}}
  else t.effect.update(tick);
}
function setScene(next) {
  const previousScene=scene;
  if(rewards.active&&rewards.phase!=='choose'){rewards.interrupt();return;}
  if(scene==='nature'&&nature?.eraseTask)return;
  if(preferences)closePreferences();
  if(scene==='inside'&&next!=='inside'&&(resident.busy||room.busy))return;
  if(scene==='inside'&&!['inside','outside'].includes(next)&&resident.pose===4&&!resident.active){resident.wake(true,()=>setScene(next));return;}
  musicAuditionPitch=null;
  if(rewards.active){rewards.active=false;rewards.sprite=null;}
  if(maze&&scene==='maze'&&maze.phase==='win')maze.replaceSong();
  gameSave?.save();resident.save();
  room.leave();
  if(maze&&scene==='maze'){maze.cancel();maze.started=false;}
  musicEditor.end(true);musicEditor.acceptTitle();musicDialog=null;musicPrint=null;
  musicSelector.open=false;
  stopPlayback(true);releaseAll();
  if(theater){theater.stop();theater.drag=null;theater.save();}
  if(nature)nature.endDrag();chalk.end();chalk.tool=-1;chalk.returnedColor=null;
  if(recording)finishRecording();
  if(window.speechSynthesis)window.speechSynthesis.cancel();
  if(next==="inside"){balloon.due=tick+48;room.enter(tick);}
  scene=next;if(next==='inside'||next==='outside'&&resident.selected)resident.enterScene();animations=[];audition=null;entering=false;transition=null;dirty=true;
  if(next==="outside") {
    if(resident.selected){
      panel('01 / IN THE YARD','Who lives outside?','Visit the squirrels, watch the pond, or say hello to your friend at the window.','Click the ladder to go inside. Try the cloud, sun, birdhouse, pond, window and tree hollow.');
      $('controls').append(button('Go inside',()=>navigateScene('inside'),true),button('Visit the squirrels',()=>navigateScene('hollow')));
      for(const [label,x,y]of [['Change the cloud',80,25],['Watch the sun',20,20],['Watch the birdhouse',145,90],['Watch the pond',50,190],['Call your friend',237,45]])$('controls').append(button(label,()=>exterior.click(x,y)));
      $('controls').append(button('Choose another friend',chooseFriend));
    }else{
      animations=[animation("th",8000,8000),animation("th",8001,8001)];
      // Native setup stops each greeting after its first displayed picture.
      for(const a of animations)a.done=true;
      panel("01 / WELCOME","Come on in.","Choose a friend. Then come inside and make some music.","Click either character, or choose a friend with the buttons.");
      $("controls").append(row(button("Choose the boy",()=>enter("boy"),true),button("Choose the girl",()=>enter("girl"))));
    }
  } else if(next==='hollow'){
    exterior.enterHollow();panel('09 / SQUIRREL HOME','Home sweet home.','Two squirrels are resting in their tree. Give them a nut or see who wakes up.','You can toss three nuts on each visit. Click outside their home to return to the yard.');
    for(const [label,x,y]of [['Wake the upper squirrel',160,90],['Wake the lower squirrel',115,115],['Toss a nut',235,145],['Read the sign',180,40]])$('controls').append(button(label,()=>exterior.hollowClick(x,y)));
    $('controls').append(button('Back to the yard',()=>navigateScene('outside')));
  } else if(next==="inside") {
    panel("02 / EXPLORE","Your treehouse.","Make music, explore nature, put on a play, draw, or play the board game.","Choose an activity in the room or use the large buttons. Click your friend to see an original animation.");
    $("controls").append(button("Make some music",()=>navigateScene("music"),true),button("Put on a play",()=>navigateScene("theater")),button("Explore nature",()=>navigateScene("nature")),button("Play the board game",()=>navigateScene("boardgame")),button("Look through the telescope",()=>navigateScene("telescope")),button("Draw on the chalkboard",()=>{chalkOpen=!chalkOpen;insidePanel();}),button('Go outside',()=>navigateScene('outside')),button("Choose another friend",chooseFriend));
    if(chalkOpen)chalkPanel();
    $('controls').append(button('Read the calendar',()=>room.readCalendar()),button('Change the cloud picture',()=>{room.nextCloud();audio.start('digisnd:1044');}),button('What time is it?',tellTime),button('Watch the spider',()=>room.interact('spider')),button('Watch the nest',()=>room.interact('nest')),button('Listen to the nest',()=>room.interact('chirp')),button('Talk to your friend',()=>resident.clickCharacter()),button('How is your friend?',()=>resident.speakStatus()),button('Offer an apple',()=>{if(!resident.busy)resident.offer(resident.create(18));}),button('Offer the pillow',()=>{if(!resident.busy)resident.offer(resident.create(8));}));calendarPanel();
  } else if(next==="music") {
    if(previousScene!=="music"){musicIdle.frame=-1;musicIdle.due=tick+600;}
    const song=currentMusicSong();tempo=song[2];
    panel("03 / MAKE MUSIC","Play your own tune.","Tap the keys to make music. Pick an instrument, listen to a song, or record your own tune.","Use the onscreen keys, or the original keyboard layout: Z S X D C V G B H N J M , L . ; / . Use Play song to listen. Arrow keys move the pointer; Enter or Space presses it.");
    $("controls").append(
      selectControl("Instrument","instrument",music.instruments.map(i=>[i.id,i.name]),instrument,id=>{instrument=id;currentMusicSong()[3]=id;if(musicEditor.enabled)musicEditor.save();factIndex=0;releaseAll();audition=null;showFact();dirty=true;}),
      button("Hear this instrument",auditionInstrument),
      selectControl("Song","song",musicEditor.enabled?Array.from({length:43},(_,i)=>[i,i===42?'The End':musicEditor.titleAt(musicEditor.mode,i)]):ORIGINAL.strings["modules:101"].slice(0,25).map((s,i)=>[i,s]),musicEditor.enabled?musicEditor.index[musicEditor.mode]:songId,selectMusicPage),
      row(button("Play song",toggleSong,true),button("Stop",()=>stopPlayback())),
      selectControl("Speed","tempo",[[0,"Very slow"],[1,"Slow"],[2,"Steady"],[3,"Quick"],[4,"Very quick"]],tempo,value=>{stopPlayback(true);tempo=value;currentMusicSong()[2]=value;if(musicEditor.enabled)musicEditor.save();}),
      row(button("Record a tune",toggleRecording),button("Play my tune",playRecording)));
    $("controls").querySelectorAll(".button-row")[0].firstChild.id="play-song";
    $("controls").querySelectorAll(".button-row")[1].firstChild.id="record";
    $("controls").append(selectControl("Score size","score-size",[[0,"Large notes"],[1,"Two music staffs"]],Number(longScore),value=>setMusicScore(!!value)));
    $("controls").append(selectControl('Repeat song','repeat-song',[[0,'Play once'],[1,'Keep playing']],Number(repeatSong),v=>{repeatSong=!!v;dirty=true;}));
    $("controls").append(selectControl("Music book","music-book",[[0,"Listen to original songs"],[1,"Compose my own songs"]],Number(musicEditor.enabled),value=>setMusicComposing(!!value)));
    if(musicEditor.enabled)musicEditorPanel();
    else $("controls").append(button("Copy this song to my book",copyMusicSong));
    $("controls").append(button("Explore instrument families",()=>{stopPlayback(true);releaseAll();musicSelector.show();}));
    $("controls").append(button('Print score',printMusic),button('Song contents',()=>showMusicContents(1)),button('Play the musical maze',()=>navigateScene('maze')));
    showFact();updatePlayButton();musicContentsPanel();
  } else if(next==='maze'){
    if(!maze)maze=new MusicMaze(store,{character:()=>character,instrument:()=>instrument,play:playPitch,stop:v=>audio.stop(v),sound:id=>audio.start(`digisnd:${id}`),prepareSound:id=>audio.prepareDecoder(`digisnd:${id}`),stopSound:id=>audio.stopSound(id),changed:()=>{dirty=true;if(scene==='maze')mazePanel();},announce:status,leave:navigateScene});
    panel('08 / LISTEN AND EXPLORE','Find the hidden song.','Listen to the sound, then choose the matching sign. Each match earns a note.','Collect notes or guess the song from its picture. The four signs lead to different parts of the maze.');
    gameSave?.loadActivity('maze',maze);maze.tick=tick;if(!maze.started)maze.reset(true);mazePanel();
  } else if(next==="theater") {
    if(!theater)theater=new TheaterActivity(store,{speak:theaterSpeech,stopSound:id=>audio.stopSound(id),changed:()=>{dirty=true;if(scene==="theater")theaterPanel();},announce:status});
    gameSave?.loadActivity('theater',theater);theater.tick=tick;
    panel("04 / SENTENCE THEATER","Put on a play.","Choose who, what they do, where, and when. Then watch your sentence come to life.","Use the notebook or the large word lists. Click the director to perform. You can drag your actor and decorations around the stage.");
    theaterPanel();
  } else if(next==="boardgame") {
    if(!boardgame)boardgame=new BoardGame(store,{character:()=>character,speak:theaterSpeech,stopSpeak:()=>audio.stopAll(),changed:()=>{dirty=true;if(scene==="boardgame")boardgamePanel();}});
    gameSave?.loadActivity('board',boardgame);boardgame.award=()=>openPrizes('boardgame');boardgame.tick=tick;boardgame.enter();
    panel("07 / COUNT AND COMPARE","Take a drive.","Follow the roads, count your money or chips, and choose which reward to collect.","Roll with the question mark. Follow the arrows one space at a time, or choose a destination you can reach with your remaining moves.");boardgamePanel();
  } else if(next==="nature") {
    if(!nature)nature=new NatureActivity(store,{character:()=>character,speak:theaterSpeech,stopSound:id=>audio.stopSound(id),confirm:askNature,print:printNature,changed:()=>{dirty=true;if(scene==="nature")naturePanel();},announce:status});
    gameSave?.loadActivity('nature',nature);nature.quiz.award=()=>openPrizes('nature');nature.tick=tick;nature.interact();
    panel("05 / EXPLORE NATURE","Who lives here?","Discover animals and what makes them alike. Choose a group, read a fact, and make your own nature scene.","Drag animals into the scene. Tap the sun or moon to switch between day and night. Drag an animal out to remove it.");
    naturePanel();
  } else if(next==="telescope") {
    telescope=rewards.nextView();startTelescopeAnimation();
    panel("04 / TAKE A LOOK","What can you see?","Look closely. Choose a different view and see what you can spot.","Four original telescope pictures. Use the buttons to change the view. Arrow keys move the pointer; Enter or Space presses it.");
    const names=["The planets","A little alien","The birdbath","The robot’s shelf"];
    for(let i=0;i<names.length;i++)$("controls").append(button(names[i],()=>{telescope=i;startTelescopeAnimation();status(names[i]);dirty=true;}));
  }
}
function openPrizes(activity){
  if(rewards.active)return;
  const background=new Surface();let kind,role,upper,panel,destination,done;
  if(activity==='nature'){
    const q=nature.quiz;if(q.winner<0||q.winAnimation&&!q.winAnimation.done)return;
    q.draw(background);q.player=q.winner;background.rect(137,8,25,25,0xffffffff);background.rect(8,125,156,10,0xffffffff);kind='nature';role=q.role();upper=panel=[6,30,116,128];destination=role===2?q.tables.quiz_rectangles[10]:[1,304,23,320];done=()=>{q.start();naturePanel();};
  }else{
    const g=boardgame;if(g.motion.busy||g.winner<0&&g.loser<0)return;
    g.draw(background);const recipient=g.winner>=0?g.winner:1-g.loser;role=recipient===0?0:g.opponent;kind=g.mode?'chips':'money';
    const r=[...g.tables.game_rects.slice(0,6),...(g.mode?g.tables.chip_rects:g.tables.money_rects)];upper=r[g.mode?15:14];panel=r[g.mode?14:15];destination=r[role===2?10:0];done=()=>{g.start();boardgamePanel();};
  }
  rewards.tick=tick;rewards.open({kind,role,background,upper,panel,destination,done,cancel:()=>navigateScene('inside')});
  $('controls').replaceChildren();const names=role===2?['Robot prize 1','Robot prize 2','Robot prize 3','Robot prize 4','Robot prize 5','Robot prize 6']:['Dragon egg','Paper airplane','Magnifying glass','Ice cream','Lollipop','Caterpillar','Balloons','Flower'];
  rewards.choices.forEach((id,i)=>$('controls').append(button(names[id],()=>rewards.choose(i))));status('Choose your prize.');
}
function tellTime(){const now=room.now();room.sayTime(now,false,()=>resident.scheduleAmbient());status(`It is ${now.toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})}.`);}
function calendarPanel(){
  $('calendar-panel')?.remove();if(!room.open)return;const box=document.createElement('section');box.id='calendar-panel';box.className='reading-card';const date=document.createElement('p'),heading=document.createElement('h3'),body=document.createElement('p');date.textContent=room.dateLabel;heading.textContent=room.story.heading;body.textContent=room.story.body;body.className='reading';box.append(date,heading,body,row(button('Previous day',()=>room.browse(-1)),button('Next day',()=>room.browse(1))),button('Today',()=>room.chooseDate(room.now())),button('Close the calendar',()=>room.toggle()));$('controls').prepend(box);
}
function mazePanel(){
  $('controls').replaceChildren();const heading=document.createElement('p');heading.className='reading';heading.textContent=maze.phase==='win'?`You found ${maze.title}!`:`${maze.earned} of ${maze.song[0]} notes found.`;$('controls').append(heading);
  if(maze.phase==='intro'){$('controls').append(button('Skip introduction',()=>maze.interrupt()),button('Back to the piano',()=>navigateScene('music')));return;}
  if(maze.phase==='win'){$('controls').append(button('Hear the whole song',()=>maze.activateControl(8),true),button('Start a new maze',()=>maze.activateControl(7)));}
  else if(maze.chooser){maze.songs.forEach((song,i)=>{if(!maze.eliminated.has(i))$('controls').append(button(store.data.strings['modules:101'][song],()=>maze.guess(i)));});$('controls').append(button('Keep exploring',()=>maze.closeGuess()));}
  else{
    $('controls').append(button('Hear the sound again',()=>maze.hearTarget(),true));
    const directions=['Left','Up','Right','Down'];for(let d=0;d<4;d++){const choice=maze.choices[d],label=maze.type===4?music.instruments[choice].name:maze.type===0?maze.t.rhythm_patterns[choice].map(n=>n?'long':'short').join(' · '):maze.candidateEvents(d).map(e=>NOTE_NAMES[e.pitch]).join(' · '),b=button(`${directions[d]}: ${label}`,()=>maze.choose(d));b.disabled=maze.busy||maze.wrong.has(d);$('controls').append(b);}
    if(maze.earned){$('controls').append(button('Hear my collected notes',()=>maze.hearSong()));const b=button('Guess the song',()=>maze.openGuess());b.disabled=!maze.canGuess;$('controls').append(b);}
  }
  $('controls').append(button('Back to the piano',()=>maze.phase==='win'?maze.activateControl(6):navigateScene('music')));
}
function selectMusicPage(id){stopPlayback(true);releaseAll();musicEditor.end(true);musicEditor.contents=0;musicEditor.acceptTitle();if(musicEditor.enabled){musicEditor.select(id);instrument=musicEditor.song[3];}else{songId=Math.max(0,Math.min(24,id));instrument=currentMusicSong()[3];}if(musicTerminal())repeatSong=false;setScene('music');if(musicTerminal())toggleSong();}
function musicTerminal(){return musicEditor.enabled?!musicEditor.editable:songId===24;}
function showMusicContents(page){stopPlayback(true);releaseAll();musicEditor.acceptTitle();musicEditor.contents=Math.max(1,Math.min(musicEditor.enabled?7:4,page));musicContentsPanel();dirty=true;}
function musicContentsPanel(){document.getElementById('music-contents')?.remove();if(!musicEditor.contents)return;const card=document.createElement('div');card.id='music-contents';card.className='reading-card';const heading=document.createElement('h3');heading.textContent=`Song contents · ${musicEditor.contents}`;card.append(heading);for(let i=(musicEditor.contents-1)*6;i<musicEditor.contents*6;i++)card.append(button(musicEditor.enabled?musicEditor.titleAt(musicEditor.mode,i):ORIGINAL.strings['modules:101'][i],()=>selectMusicPage(i)));card.append(row(button('Previous contents page',()=>showMusicContents(musicEditor.contents-1)),button('Next contents page',()=>turnMusicPage(1))),button('Return to my song',()=>selectMusicPage(musicEditor.enabled?musicEditor.index[musicEditor.mode]:songId)));$('controls').prepend(card);}
function turnMusicPage(direction){if(musicEditor.contents){const next=musicEditor.contents+direction;if(next>(musicEditor.enabled?7:4))selectMusicPage(0);else showMusicContents(next);}else{const index=musicEditor.enabled?musicEditor.index[musicEditor.mode]:songId;if(index===0&&direction<0)showMusicContents(musicEditor.enabled?7:4);else selectMusicPage(index+direction);}}
function musicEditorPanel(){
  if(musicEditor.editable){
    const label=document.createElement('label'),input=document.createElement('input');label.textContent='Song name';label.className='control-label';label.htmlFor='song-title';input.id='song-title';input.maxLength=35;input.value=musicEditor.title;input.onchange=()=>{musicEditor.rename(input.value);$('song').selectedOptions[0].textContent=musicEditor.title;};$('controls').append(label,input);
    const names=['Whole note','Dotted half note','Half note','Dotted quarter note','Quarter note','Dotted eighth note','Eighth note','Sixteenth note'];
    $('controls').append(selectControl('Note length','note-duration',(longScore?[0,1,2,3,4,5,6,7]:[0,2,3,4,6]).map(d=>[d,names[d]]),musicEditor.duration[musicEditor.mode],d=>{musicEditor.duration[musicEditor.mode]=d;dirty=true;}),selectControl('Next note position','note-position',Array.from({length:musicEditor.capacity},(_,i)=>[i,i+1]),musicEditor.position,i=>{musicEditor.position=i;dirty=true;}),selectControl('New note spelling','note-spelling',[[0,'Sharps'],[1,'Flats']],musicEditor.song[4],v=>{musicEditor.song[4]=v;musicEditor.save();}),row(button('Add a rest',()=>musicEditor.write(5,8+musicEditor.duration[musicEditor.mode]%8)),button('Erase selected note',()=>musicEditor.remove())),row(button('Erase this song',eraseMusicSong),button('Create a random song',()=>askMusic('Create new song?',()=>musicEditor.randomize(tick)))));
  }
  const file=document.createElement('input');file.type='file';file.accept='.dat';file.id='songbook-file';file.hidden=true;
  file.onchange=async()=>{if(!file.files[0])return;try{musicEditor.importData(new Uint8Array(await file.files[0].arrayBuffer()));instrument=musicEditor.song[3];setScene('music');status('Both songbooks loaded.');}catch(e){status(e.message);}file.value='';};
  $('controls').append(file,row(button('Download songbooks',()=>{const url=URL.createObjectURL(new Blob([musicEditor.exportData()],{type:'application/octet-stream'})),link=document.createElement('a');link.href=url;link.download='SONGS.DAT';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}),button('Open songbooks',()=>file.click())),button('Print this page',printMusic));
}
function printMusic(){
  if(gameSave&&!gameSave.preferences.printing){status('Printing is turned off in Settings.');return;}
  if(musicEditor.contents||musicTerminal())return;
  askMusic('Print song?',()=>{releaseAll();musicPrint=new Surface();musicEditor.drawPrint(musicPrint,currentMusicSong(),currentMusicTitle(),instrument,songId);$('controls').replaceChildren(button('Print score',()=>{render();window.print();},true),button('Back to the piano',()=>navigateScene('music')));status('Your printable score is ready.');dirty=true;});
}
function askMusic(message,yes){stopPlayback(true);musicEditor.end(true);musicDialog={message,yes,start:tick};const box=document.createElement('div');box.id='music-question';box.className='reading-card';const p=document.createElement('p');p.className='reading';p.textContent=message;box.append(p,row(button('Yes',()=>answerMusic(true),true),button('No',()=>answerMusic(false))));$('controls').prepend(box);dirty=true;}
function answerMusic(yes){const dialog=musicDialog;if(!dialog)return;musicDialog=null;$('music-question')?.remove();if(yes)dialog.yes();dirty=true;}
function eraseMusicSong(all=false){if(!musicEditor.editable||musicEditor.contents)return;if(all){askMusic('Erase ALL songs?',()=>{musicEditor.clearAll();instrument=musicEditor.song[3];setScene('music');});return;}if(!musicEditor.used(musicEditor.mode,musicEditor.index[musicEditor.mode])){status('Nothing to erase!');return;}askMusic('Erase the whole song?',()=>{musicEditor.clear();setScene('music');});}
function copyMusicSong(){if(musicEditor.contents||musicTerminal())return;musicEditor.advanced=longScore;const free=musicEditor.firstFree();if(free<0){status('Your song book is full!');return;}const raw=[...currentMusicSong()],title='My '+currentMusicTitle();raw[3]=instrument;raw[2]=tempo;askMusic('Copy song to your book?',()=>{setMusicComposing(true);musicEditor.copy(raw,title,free);instrument=raw[3];setScene('music');});}
function drawMusicDialog(){
  if(!musicDialog)return;screen.rect(5,16,74,65,0xff000000);screen.rect(6,17,72,63,0xffffffff);
  const phase=Math.floor((tick-musicDialog.start)/12);for(const[id,x,y]of [[character==='girl'?82:81,25,character==='girl'?1:8],[83,1,33],[84,79,33],[85,29,81],[86+(phase&1),7,40],[88+[0,1,2,1][phase&3],43,40]])draw('th',id,80,x,y,id>=86?2:10);
  const rounded=(x,y,c)=>{screen.rect(x+1,y,24,9,c);screen.rect(x,y+1,26,7,c);};for(const[x,color]of [[11,0xff00aa00],[47,0xff0000aa]]){rounded(x+1,70,0xff000000);rounded(x,69,color);}text('Yes',16,70);text('No',55,70);
  const labels={'Copy song to your book?':[['Copy song to',13],['your book?',17]],'Erase the whole song?':[['Erase the',20],['whole song?',14]],'Erase ALL songs?':[['Erase ALL',20],['songs?',28]],'Print song?':[['Print song?',15]],'Create new song?':[['Create new',15],['song?',29]]};
  labels[musicDialog.message]?.forEach(([s,x],i)=>text(s,x,19+10*i));
}
function insidePanel(){setScene("inside");}
function syncChalkTools(){
  const select=$("chalk-tool");if(select)select.value=chalk.tool;
  const undo=$("chalk-undo");if(undo)undo.disabled=!chalk.history.length;
}
function chalkPanel(){
  $("controls").append(selectControl("Chalk color","chalk-tool",[[-1,"Choose some chalk…"],...chalk.names.map((n,i)=>[i,n])],chalk.tool,i=>chalk.select(i)));
  const pad=document.createElement("canvas");pad.id="chalk-pad";pad.width=94;pad.height=47;pad.className="chalk-pad";pad.tabIndex=0;pad.setAttribute("aria-label","Enlarged chalkboard drawing pad");
  const position=e=>{const r=pad.getBoundingClientRect();return[60+(e.clientX-r.left-pad.clientLeft)*94/pad.clientWidth,45+(e.clientY-r.top-pad.clientTop)*47/pad.clientHeight];};
  let owner=null;
  pad.onpointerdown=e=>{e.preventDefault();if(owner!==null)return;owner=e.pointerId;pad.setPointerCapture(owner);if(chalk.tool<0)chalk.select(0);chalk.begin(...position(e));dirty=true;syncChalkTools();};
  pad.onpointermove=e=>{if(e.pointerId!==owner)return;chalk.move(...position(e),true,true);dirty=true;};
  for(const type of ["pointerup","pointercancel","lostpointercapture"])pad.addEventListener(type,e=>{if(e.pointerId===owner){owner=null;chalk.end();}});
  const undo=button("Undo drawing",()=>chalk.undo());undo.id="chalk-undo";
  $("controls").append(pad,row(undo,button("Clear chalkboard",askChalk)));syncChalkTools();
}
function boardgamePanel(){
  if(rewards.active)return;
  const g=boardgame,controls=$("controls");controls.replaceChildren();$("instructions").textContent=g.notice;
  if(g.options){
    controls.append(selectControl("Game","board-mode",[[0,"Money game"],[1,"Chip game"]],g.mode,i=>g.selectGame(i)),selectControl("Play with","board-opponent",[[2,"The robot"],[1,"A friend"]],g.opponent,i=>g.selectGame(g.mode,i)));
    for(const p of g.opponent===1?[0,1]:[0])controls.append(selectControl(p?"Your friend's goal":"Your goal",`board-goal-${p}`,g.tables.goals.map((n,i)=>[i,g.amount(n)]),g.levels[p],i=>{g.levels[p]=i;}));
    controls.append(button("Start the board game",()=>g.start(),true));return;
  }
  const balance=document.createElement("p");balance.className="reading";balance.textContent=`You: ${g.amount(g.balances[0])} · ${g.opponent===2?"Robot":"Friend"}: ${g.amount(g.balances[1])}`;controls.append(balance);
  if(g.phase==="exchange"){$("instructions").textContent=g.exchangeText();controls.append(button("Trade these chips",()=>g.exchangeChips(),true));}
  else if(g.phase==="reward")for(let i=0;i<2;i++){
    const description=document.createElement("p");description.className="reading";
    if(g.mode)description.textContent=i===0?`${g.rewards[0]} chips + your balance = ?`:`? chips + your balance = ${g.balances[g.player]+g.rewards[1]}`;
    else{const names=[["dollar coin","dollar coins"],["half dollar","half dollars"],["quarter","quarters"],["dime","dimes"],["nickel","nickels"],["penny","pennies"]];description.textContent=g.rewardCoins[i].map((n,d)=>n?`${n} ${names[d][n===1?0:1]}`:null).filter(Boolean).join(", ");}
    controls.append(description,button(`Choose the ${g.mode?["left","right"][i]:["upper","lower"][i]} amount`,()=>g.choose(i),true));
  }
  else if(g.phase==="ready"||g.phase==="result")controls.append(button(g.winner>=0||g.loser>=0?"Choose a prize":"Roll for the next turn",()=>g.roll(),true));
  else if(g.phase==="move"&&!g.moving&&g.role()!==2){
    const dirs=["left","up","right","down"];
    g.tables.adjacency[g.nodes[g.player]].forEach((node,d)=>{if(node>=0)controls.append(button(`Drive ${dirs[d]}`,()=>g.move(node)));});
  }
  controls.append(button("Game options",()=>g.showOptions()));
}
function naturePanel() {
  if(rewards.active)return;
  if(nature.mode==="quiz"){quizPanel();return;}
  $("heading").textContent="Who lives here?";$("instructions").textContent="Discover animals and what makes them alike. Choose a group, read a fact, and make your own nature scene.";
  const focus=document.activeElement?.id,controls=$("controls");controls.replaceChildren();
  controls.append(selectControl("Look for","nature-attribute",nature.attributeNames().map((s,i)=>[i,s.toLowerCase()]),nature.attribute,i=>nature.selectAttribute(i,false)),
    selectControl("Description","nature-value",nature.valueNames().map((s,i)=>[i,s]),nature.values[nature.attribute],i=>nature.selectValue(i)),
    selectControl("Animal group","nature-class",[[-1,"Choose a group…"],...nature.classNames().map((s,i)=>[i,s]).filter(([i])=>nature.availableClasses().has(i))],nature.category,i=>nature.selectClass(i)));
  if(nature.category>=0){controls.append(selectControl("Animal","nature-animal",[[-1,"Choose an animal…"],...nature.animals().map(a=>[a.id,nature.name(a.id)])],nature.selected,i=>{if(i>=0)nature.selectAnimal(i);}));}
  if(nature.selected>=0)controls.append(button("Add this animal",()=>nature.addAnimal(nature.selected),true));
  controls.append(button("Play the animal guessing game",()=>nature.enterQuiz()),button(nature.time?"Switch to daytime":"Switch to nighttime",()=>nature.toggleTime()),button("Clear this scene",()=>nature.requestClear()),button("Clear day and night scenes",()=>nature.requestClear(true)),button("Print this scene",printNature));
  if(nature.undo)controls.append(button("Undo clear",()=>nature.undoClear()));
  $("fact-card").hidden=nature.selected<0;$("fact-title").textContent=nature.selected<0?"Animal facts":nature.name(nature.selected);$("fact").textContent=nature.fact();$("next-fact").hidden=nature.selected<0;
  if(focus&&document.getElementById(focus))document.getElementById(focus).focus({preventScroll:true});
}
function quizPanel() {
  const q=nature.quiz,controls=$("controls");controls.replaceChildren();
  $("heading").textContent="Find the secret animal.";$("instructions").textContent=q.options?"Play with a friend or the robot. Ask about the animals, cross out the ones that do not fit, and make a guess.":q.notice;
  $("fact-card").hidden=true;$("next-fact").hidden=true;
  if(q.options){
    controls.append(selectControl("Play with","quiz-opponent",[[2,"The robot"],[1,"A friend"]],q.opponent,v=>{q.opponent=v;q.changed();}));
    for(const [role,label]of [[0,"Help me cross out animals"],...(q.opponent===1?[[1,"Help my friend cross out animals"]]:[])]){
      const row=document.createElement("label"),input=document.createElement("input");row.className="theater-option";input.type="checkbox";input.id=`quiz-help-${role}`;input.checked=q.help[role];input.onchange=()=>{q.help[role]=input.checked;dirty=true;};row.append(input,document.createTextNode(label));controls.append(row);
    }
    controls.append(button("Start the guessing game",()=>q.start(),true));return;
  }
  if(q.busy){const waiting=document.createElement('p');waiting.textContent='Watch and listen…';controls.append(waiting);return;}
  if(q.winner>=0){controls.append(button('See the other animal',()=>q.inspectWinner(1-q.player)),button("Choose a prize",()=>q.roll(),true),button("Game options",()=>{q.options=true;q.changed();}));return;}
  if(q.phase!=="question")controls.append(button("Roll for the next turn",()=>q.roll(),true));
  if(q.phase==="question"&&q.role()!==2){
    for(const i of q.available){const label=nature.strings(5300)[i].toLowerCase();controls.append(button(`Ask about ${label}`,()=>q.ask(i)));}
    controls.append(button("Make a guess",()=>q.toggleGuess(),true));
  }
  if(q.phase!=="ready"){
    const grid=document.createElement("div");grid.className="animal-candidates";
    q.cards[q.player].forEach((id,index)=>{const r=document.createElement("div"),active=!!(q.remaining[q.player]&(1<<index));r.className="candidate-row";const name=button(nature.name(id),()=>q.choose(index));name.disabled=q.role()===2||(q.guessing&&!active);name.setAttribute("aria-label",`${q.guessing?"Guess":"Inspect"} ${nature.name(id)}`);if(!active)name.classList.add("crossed-out");const cross=button(active?"×":"↶",()=>q.crossOut(index));cross.disabled=q.role()===2;cross.setAttribute("aria-label",`${active?"Cross out":"Restore"} ${nature.name(id)}`);r.append(name,cross);grid.append(r);});controls.append(grid);
    if(q.selected>=0||q.answer||q.explanation){$("fact-card").hidden=false;$("fact-title").textContent=q.explanation?q.names()[q.selectedAttribute]:q.selected>=0?nature.name(q.cards[q.player][q.selected]):"Your clue";$("fact").textContent=q.explanation||q.answer||nature.strings(5100+q.cards[q.player][q.selected])[0];}
  }
  controls.append(button("Game options",()=>{q.options=true;q.robotDue=null;q.changed();}));
}
function theaterSpeech(id,rate=null,{fractional=false}={}) {
  const key=ORIGINAL.pcm[`digisnd:${id}`]?`digisnd:${id}`:`voices:${id}`,sample=ORIGINAL.pcm[key];
  if(!sample||!audio.enabled)return 0;
  audio.stopAll();audio.start(key,rate);const duration=bytes(sample.pcm).length/audio.rate(rate??sample.rate)*TICK_HZ;return fractional?duration:Math.ceil(duration);
}
function theaterPanel() {
  const focus=document.activeElement?.id,controls=$("controls");controls.replaceChildren();
  const checkbox=(title,id,checked,change)=>{
    const label=document.createElement("label"),input=document.createElement("input");label.className="theater-option";input.type="checkbox";input.id=id;input.checked=checked;
    input.onchange=()=>{change(input.checked);dirty=true;};label.append(input,document.createTextNode(title));return label;
  };
  if(theater.options){
    controls.append(checkbox("Move the sentence parts","mix-up",theater.mixUp,v=>theater.setOption('mixUp',v)),checkbox("Add stage decorations","props",theater.propsEnabled,v=>theater.setOption('propsEnabled',v)),button("Start the theater",()=>theater.start(),true));
    $("fact-card").hidden=true;
  } else {
    const labels=["Who or what?","Does what?","Where?","When?"];
    for(let category=0;category<4;category++){
      const choices=[[-1,category<2?"Choose a word…":"Not in this sentence"],...theater.choices(category).map((s,i)=>[i,s])];
      controls.append(selectControl(labels[category],`theater-part-${category}`,choices,theater.selection[category],id=>theater.choose(category,id)));
    }
    controls.append(row(button(theater.playing?"Stop the play":"Perform my sentence",()=>{if(theater.playing){theater.stop();audio.stopAll();theater.changed();}else theater.play();},true),button("Options",()=>{theater.stop();theater.options=true;theater.changed();})));
    if(theater.mixUp){
      const order=document.createElement("div");order.className="sentence-order";
      for(const category of theater.order){const r=document.createElement("div");r.className="order-row";const title=document.createElement("span");title.textContent=["Who","Action","Where","When"][category];
        const left=button("←",()=>theater.movePart(category,-1)),right=button("→",()=>theater.movePart(category,1));left.setAttribute("aria-label",`Move ${title.textContent} earlier`);right.setAttribute("aria-label",`Move ${title.textContent} later`);left.disabled=theater.order[0]===category||theater.playing;right.disabled=theater.order[3]===category||theater.playing;r.append(title,left,right);order.append(r);}
      controls.append(order,row(button("Mix up the sentence",()=>theater.shuffle()),button("Fix the sentence order",()=>theater.correct())));
    }
    if(theater.propsEnabled){controls.append(button("Choose decorations",()=>theater.showChoices(4)),button("Remove last decoration",()=>theater.removeLastProp()));}
    $("fact-card").hidden=false;$("fact-title").textContent="Your sentence";$("fact").textContent=theater.sentence()||"Choose who or what will be in your play.";
    $("next-fact").hidden=true;
  }
  if(focus&&document.getElementById(focus))document.getElementById(focus).focus({preventScroll:true});
}
function enter(who) {
  if(entering||resident.busy)return;character=who;entering=true;
  // Original calls 0x083A,0x0899,0x0902: selected greeting, other greeting,
  // selected entrance. They run synchronously, not at the same time.
  const selected=who==="boy"?0:1,sequence=[[selected,8000+selected],[1-selected,8001-selected],[selected,8002+selected]];
  let active;
  const next=()=>{const [slot,id]=sequence.shift();active=animation("th",id,8000+slot);animations[slot]=active;};
  next();
  transition=()=>{if(!active.done)return false;if(sequence.length)next();else setScene("inside");return true;};
  status("Let's go inside!");for(const b of $("controls").querySelectorAll("button"))b.disabled=true;
}
function showFact() {
  $("next-fact").hidden=false;
  const name=music.instruments.find(i=>i.id===instrument).name;
  const facts=ORIGINAL.strings[`modules:${instrument}`]||[];
  $("fact-card").hidden=!facts.length;$("fact-title").textContent=name;
  $("fact").textContent=(facts[factIndex%facts.length]||"").replace(/([A-Za-z])-\s+([a-z])/g,"$1$2");
}
function musicSelectorPanel(){
  const controls=$("controls");controls.replaceChildren();
  if(musicSelector.category<0){for(let i=0;i<7;i++)controls.append(button(musicSelector.name(i),()=>musicSelector.show(i)));$("fact-card").hidden=true;}
  else{
    const category=musicSelector.category;
    controls.append(button(`Play the ${musicSelector.name(category)} ensemble`,()=>musicSelector.select(category),true));
    for(const id of musicSelector.tables.members[category])controls.append(button(musicSelector.name(id),()=>musicSelector.select(id)));
    controls.append(button("More instrument families",()=>musicSelector.show()),button("Next fact",()=>musicSelector.nextFact()));
    $("fact-card").hidden=false;$("fact-title").textContent=musicSelector.name(musicSelector.info);$("fact").textContent=musicSelector.facts()[musicSelector.fact]||'';
  }
  $("next-fact").hidden=true;controls.append(button("Back to the piano",()=>musicSelector.leave('music')));
  status(musicSelector.category<0?'Choose an instrument family.':'Choose a picture to hear its sound.');
}
function playPitch(pitch,selectedInstrument=instrument,finite=false) {
  const id=music.instruments.find(i=>i.id===selectedInstrument).sound_id;
  stats.notesPlayed++;
  return audio.start(`voices:${id}`,music.playback_rates[pitch],null,{loop:!finite});
}
function currentMusicSong(){return musicEditor.enabled?musicEditor.song:listeningBooks.songs[Number(longScore)][songId];}
function currentMusicTitle(){return musicEditor.enabled?musicEditor.title:ORIGINAL.strings['modules:101'][songId];}
function setMusicComposing(enabled){
  if(enabled===musicEditor.enabled)return;stopPlayback(true);releaseAll();musicEditor.acceptTitle();musicEditor.contents=0;
  if(enabled){musicEditor.enabled=true;musicEditor.advanced=longScore;musicEditor.select();instrument=musicEditor.song[3];}
  else{musicEditor.enabled=false;instrument=currentMusicSong()[3];}
  setScene('music');
}
function setMusicScore(advanced){stopPlayback(true);releaseAll();musicEditor.acceptTitle();musicEditor.contents=0;longScore=advanced;musicEditor.advanced=advanced;if(musicEditor.enabled)musicEditor.select();instrument=currentMusicSong()[3];setScene('music');}
function finishMusicIdle(){musicIdle.frame=-1;musicIdle.due=tick+60*(10+gameplayRandom.pick(21));dirty=true;}
function noteDown(pitch,owner) {
  if(scene!=="music"||musicPrint||musicDialog||musicEditor.titleEntry||held.has(owner))return;
  if(musicIdle.frame>=0)finishMusicIdle();
  if(held.size)for(const previous of [...held.keys()])noteUp(previous);
  audition=null;
  stopPlayback(true);
  const note={pitch,voice:playPitch(pitch),started:tick};held.set(owner,note);
  if(!musicEditor.enabled&&!musicSelector.open&&!musicEditor.contents){musicAuditionPitch=pitch;musicAuditionDue=tick+120;}
  if(musicEditor.editable&&!musicSelector.open&&!musicEditor.contents&&!musicEditor.titleEntry){note.written={mode:musicEditor.mode,index:musicEditor.index[musicEditor.mode],position:musicEditor.position};musicEditor.write(pitch,undefined,false);}
  if(recording)recorded.push({pitch,start:tick-recordStart,end:null,owner});
  status(`${NOTE_NAMES[pitch]} · ${music.instruments.find(i=>i.id===instrument).name}`);
  updateKeys();dirty=true;
}
function noteUp(owner) {
  const note=held.get(owner);if(!note)return;
  audio.stop(note.voice);held.delete(owner);
  if(note.written&&musicEditor.mode===note.written.mode&&musicEditor.index[musicEditor.mode]===note.written.index){musicEditor.position=Math.min(musicEditor.capacity-1,note.written.position+1);musicEditor.changed();}
  if(recording){const entry=[...recorded].reverse().find(e=>e.owner===owner&&e.end===null);if(entry)entry.end=Math.max(entry.start+1,tick-recordStart);}
  updateKeys();dirty=true;
}
function updateKeys() {
  const active=new Set([...held.values()].map(n=>n.pitch));
  if(songPlaying&&songPosition>=0){const event=songEvents[songPosition];if(event&&!event.rest)active.add(event.pitch);}
  for(const b of $("touch-keys").querySelectorAll("button")){const yes=active.has(Number(b.dataset.pitch));b.classList.toggle("held",yes);b.setAttribute("aria-pressed",String(yes));}
}
function updatePlayButton() {if($("play-song"))$("play-song").textContent=songPlaying?"Stop song":"Play song";updateKeys();}
function songSequence() {
  const raw=currentMusicSong(),events=[];
  for(let i=0;i<raw[longScore?1:0];i++) {
    const pitch=raw[5+i*2]&127,duration=raw[6+i*2];
    if(pitch===127)continue;
    if(pitch>16||duration>15)throw new Error("Unexpected original SONG event");
    events.push({pitch,notationFlag:raw[5+i*2]>>>7,duration,sourceIndex:i,rest:duration>=8,ticks:music.tempo_factors[tempo]*music.duration_factors[duration]});
  }
  return events;
}
function toggleSong(){if(songPlaying){stopPlayback();return;}if(recording)finishRecording();startSequence(songSequence(),currentMusicTitle());}
function startSequence(events,label) {
  releaseAll();audition=null;musicAuditionPitch=null;songEvents=events;songCursor=0;songPosition=-1;songDue=tick;songPlaying=true;
  status(`Playing ${label}.`);updatePlayButton();advanceSong();
}
function advanceSong() {
  if(!songPlaying||tick<songDue)return;
  audio.stop(songVoice);songVoice=null;
  if(songCursor>=songEvents.length&&repeatSong&&songEvents.length)songCursor=0;
  if(songCursor>=songEvents.length){songPlaying=false;songPosition=-1;stats.songCompletions++;status("The end. Try another tune, or play your own!");updatePlayButton();dirty=true;return;}
  const event=songEvents[songCursor];songPosition=songCursor++;
  if(!event.rest)songVoice=playPitch(event.pitch);
  songDue=tick+event.ticks;updateKeys();dirty=true;
}
function toggleRecording() {
  if(recording){finishRecording();return;}
  stopPlayback(true);releaseAll();recorded=[];recordStart=tick;recording=true;
  $("record").textContent="Finish recording";$("record").classList.add("recording");status("Recording. Play a tune, then choose Finish recording.");
}
function finishRecording() {
  if(!recording)return;
  releaseAll();recording=false;
  const clean=recorded.filter(e=>e.end!==null).map(({pitch,start,end})=>({pitch,start,end}));
  recorded=clean;
  try{localStorage.setItem(savedKey,JSON.stringify({version:1,instrument,notes:clean}));status(clean.length?"Your tune is saved on this device.":"No notes recorded yet.");}
  catch(_error){status("Your tune is ready to play. This browser could not save it after closing.");}
  if($("record")){$("record").textContent="Record a tune";$("record").classList.remove("recording");}
}
function playRecording() {
  if(recording)finishRecording();
  if(!recorded.length) {
    try{const value=JSON.parse(localStorage.getItem(savedKey));if(value?.version===1&&Array.isArray(value.notes))recorded=value.notes.filter(n=>Number.isInteger(n.pitch)&&n.pitch>=0&&n.pitch<=16&&Number.isFinite(n.start)&&Number.isFinite(n.end)&&n.end>n.start);}
    catch(_error){}
  }
  if(!recorded.length){status("Record a few notes first, then play your tune here.");return;}
  // The original music editor is monophonic; every new key releases the old.
  const notes=[...recorded].sort((a,b)=>a.start-b.start),events=[];
  for(let i=0;i<notes.length;i++) {
    const n=notes[i],next=notes[i+1],end=next?Math.min(n.end,next.start):n.end;
    events.push({pitch:n.pitch,rest:false,ticks:Math.max(1,end-n.start)});
    if(next&&next.start>end)events.push({pitch:0,rest:true,ticks:next.start-end});
  }
  startSequence(events,"your tune");
}

function outside() {
  draw("th64",1,0,0,0,2);
  if(resident.selected)exterior.drawCloud(screen);
  else{draw("th64",2,0,2,0);draw("th64",3,0,0,109);exterior.drawCredits(screen);for(const a of [...animations].sort((a,b)=>Number(!a.done)-Number(!b.done)))a.draw(screen);}
  if(resident.selected){resident.drawObjects(screen,false);resident.drawObjectMotion(screen);resident.drawObjects(screen,false,null,true);}
}
function inside({characterVisible=true,curtainVisible=true}={}) {
  draw("th64",5,4,0,0,2);chalk.draw(screen);
  room.drawCloud(screen);room.drawPortrait(screen);
  for(const [id,pal,x,y]of [[1109,1100,49,121],[1256,1250,211,84],[1251,1250,211,81],[1228,1200,132,21],[926,900,151,182],[919,900,236,117]])if(id!==1109||curtainVisible)draw("th",id,pal,x,y);
  room.drawDateClock(screen);room.drawCalendar(screen);
  [0xffffffff,0xff0000ff,0xff20f7f7,0xffff0465,0xff00aa08,0xffc7c7ff].forEach((color,i)=>screen.rect(63+12*i,93,10,2,color));
  screen.rect(135,92,14,3,0xff000000);screen.rect(136,92,12,1,0xffffffff);screen.rect(136,93,12,2,0xffaaaaaa);
  chalk.drawTray(screen);
  // Original interior setup 0x2266 -> 0x35FA clears hotspot20 when its
  // message state is empty. Preserve the complete rectangle operation.
  screen.rect(4,140,30,13,0xffffffff);
  resident.drawNap(screen);resident.drawObjects(screen,true);
  if(characterVisible){if(animations.length)for(const a of animations)a.draw(screen);else resident.draw(screen);}
  resident.drawObjects(screen,true,null,true);
  room.drawEnvironment(screen);resident.drawObjectMotion(screen);if(scene==='inside'&&resident.objectSprite&&!balloon.hidden){const o=resident.objects.find(o=>o.type===6),t=o&&resident.tables.objects[6];if(o&&t)draw('th',store.palette('th',t.palette).first+t.states[o.state]-1,t.palette,balloon.x,balloon.y);}
}
function instrumentPicture() {
  if(audition&&!audition.done){audition.draw(screen);return;}
  const group=music.instruments.find(i=>i.id===instrument).animation_group;
  // A still pose uses the script's first displayed composition. The callback
  // instructions used for later performance animation are not approximated.
  const script=store.data.scripts[`th:${group}`],palette=store.palette("th",group);
  const slots=Array.from({length:16},()=>({shape:0,x:0,y:0,mode:10}));
  for(const[op,b]of script.code) {
    const s=slots[op&15];if(op===1||op===7)break;
    if((op&240)===192)s.shape=u16(b);
    if((op&240)===176){s.x=s16(b);s.y=s16(b,2);}
    if((op&240)===144)s.mode=u16(b,2)&15;
  }
  for(const s of slots)if(s.shape)screen.blit(store.shape("th",palette.first+s.shape-1),palette.rgba,
    40-Math.floor((script.bounds[3]-script.bounds[1])/2)+s.x,92-(script.bounds[2]-script.bounds[0])+s.y,s.mode,[0,0,99,79]);
}
function auditionInstrument() {
  stopPlayback(true);releaseAll();
  const group=music.instruments.find(i=>i.id===instrument).animation_group,b=store.data.scripts[`th:${group}`].bounds;
  audition=animation("th",group,group,{origin:[40-Math.floor((b[3]-b[1])/2),92-(b[2]-b[0])],
    onSound:()=>{},
    onCallback:slot=>{if(slot===0){audio.stop(auditionVoice);auditionVoice=playPitch(9);}}});
  status(`Listen to the ${music.instruments.find(i=>i.id===instrument).name.toLowerCase()}.`);dirty=true;
}
function drawScore() {
  if(longScore){drawLongScore();return;}
  const raw=currentMusicSong(),playing=songPlaying&&songPosition>=0?songEvents[songPosition]:null;
  const single=musicAuditionPitch!==null&&!musicEditor.enabled&&!songPlaying&&!musicEditor.contents;
  const page=Math.floor((playing?.sourceIndex||0)/8),first=page*8,black=0xff000000;
  const glyph=(id,x,y,color=black)=>screen.blit(store.shape("modules",id),[0,color],x,y,10);
  screen.rect(88,27,212,75,0xffffffff);
  for(let j=0;j<5;j++)screen.rect(88,41+j*8,206,1,black);
  screen.rect(88,41,1,33,black);
  glyph(2301,90,39);
  for(let i=0;i<8;i++) {
    if(single?i!==3:first+i>=raw[0])continue;
    const pitch=single?musicAuditionPitch:raw[5+(first+i)*2]&127,flag=single?raw[4]:raw[5+(first+i)*2]>>>7,d=single?4:raw[6+(first+i)*2];
    if(pitch===127)continue;
    const black=musicEditor.enabled&&musicEditor.drag?.kind==='note'&&musicEditor.drag.index===first+i?0xff0000aa:0xff000000,glyph=(id,x,y,color=black)=>screen.blit(store.shape('modules',id),[0,color],x,y,10);
    const x=120+i*22,offset=music.notation.normal_y_offsets[flag][pitch],y=78-offset;
    if(d>=8){glyph(2312+d,114+i*22+[1,1,1,4,4,3,3,3][d-8],41+[6,10,10,7,7,8,8,8][d-8]);continue;}
    glyph(d<=2?2303:2305,x,y);
    if(d>0){if(pitch<12)screen.rect(x+9,y-16,1,18,black);else screen.rect(x,y+5,1,18,black);}
    if(d>=5){if(pitch<12){glyph(2307,x+10,y-15);if(d===7)glyph(2307,x+10,y-10);}else{glyph(2309,x+1,y+16);if(d===7)glyph(2309,x+1,y+11);}}
    if([1,3,5].includes(d))glyph(2311,x+11,y+(offset%8!==0?3:0));
    if(pitch<=1-flag)screen.rect(x-3,y+3,17,1,black);
    if(music.notation.accidentals[pitch])glyph(flag?2315:2313,x-(flag?5:6),y-(flag?4:2));
    if(single||musicEditor.enabled&&musicEditor.labels.has(first+i)){const label=music.note_letters[flag][pitch]+(music.notation.accidentals[pitch]?(flag?'b':'#'):''),font=store.data.heading_font,w=[...label].reduce((n,c)=>n+font[c.charCodeAt(0)][0]+1,0);screen.text(store,label,x+5-Math.floor(w/2),87,black,font,1);}
    if(playing?.sourceIndex===first+i)glyph(2317,x,33,0xff0000ff);
  }
}
function drawLongScore(){
  const raw=currentMusicSong(),playing=songPlaying&&songPosition>=0?songEvents[songPosition]:null;
  const single=musicAuditionPitch!==null&&!musicEditor.enabled&&!songPlaying&&!musicEditor.contents;
  const t=music.followup.music,first=Math.floor((playing?.sourceIndex||0)/30)*30,black=0xff000000;
  const glyph=(id,x,y,color=black)=>screen.blit(store.shape("modules",id),[0,color],x,y,10);
  screen.rect(88,27,212,75,0xffffffff);
  for(let row=0;row<2;row++){for(let j=0;j<5;j++)screen.rect(88,28+39*row+6*j,211,1,black);screen.rect(88,28+39*row,1,25,black);glyph(2302,90,27+39*row);}
  for(let i=0;i<30;i++){
    if(single?i!==6&&i!==21:first+i>=raw[1])continue;
    const pitch=single?musicAuditionPitch:raw[5+2*(first+i)]&127,flag=single?raw[4]:raw[5+2*(first+i)]>>>7,d=single?4:raw[6+2*(first+i)],row=Math.floor(i/15),col=i%15;
    if(pitch===127)continue;
    const black=musicEditor.enabled&&musicEditor.drag?.kind==='note'&&musicEditor.drag.index===first+i?0xff0000aa:0xff000000,glyph=(id,x,y,color=black)=>screen.blit(store.shape('modules',id),[0,color],x,y,10);
    if(d>=8){glyph(2312+d,105+13*col+t.rest_x_offset[0][d-8],28+39*row+t.rest_y_offset[0][d-8]);continue;}
    const offset=t.pitch_y_offsets[2+flag][pitch],x=110+13*col,y=56+39*row-offset;
    if(pitch<=1-flag)screen.rect(x-2,y+2,9,1,black);
    if(music.notation.accidentals[pitch])glyph(flag?2316:2314,x-(flag?4:5),y-(flag?2:1));
    if([1,3,5].includes(d))glyph(2312,x+6,y+(offset%6?3:0));
    if(d){if(pitch<12)screen.rect(x+4,y-10,1,11,black);else screen.rect(x,y+4,1,11,black);}
    if(d>=5)for(let n=0;n<(d===7?2:1);n++)glyph(pitch<12?2308:2310,pitch<12?x+5:x+1,pitch<12?y-9+3*n:y+10-3*n);
    glyph(d<3?2304:2306,x,y);
    if(playing?.sourceIndex===first+i){const b=t.advanced_markers?.[i+1];if(b)glyph(row?2318:2319,b[1]+4,b[0],0xff0000ff);}
  }
}
function musicRoom({instrumentVisible=true}={}) {
  if(musicPrint){screen.restore(musicPrint);return;}
  if(musicSelector.open){musicSelector.draw(screen);return;}
  draw("modules",2201,2200,0,0,2);if(!musicDialog&&instrumentVisible)instrumentPicture();
  for(const[id,x,y]of [[musicEditor.enabled?2246:2245,264,161],[longScore?2248:2247,265,140],[repeatSong?2244:2243,54,159],[2259,289,113],[musicEditor.enabled?2253:2263,235,113],[musicEditor.enabled?2255:2257,262,113],[songPlaying?2242:2241,56,138],[2249,12,115],[currentMusicSong()[4]?2252:2251,98,117],[2261,44,115],[2262,[46,55,64,73,82][tempo],127],[2264,258,1],[2265,260,8]])draw("modules",id,2240,x,y,2);
  screen.rect(129,111,102,29,store.palette("modules",2200).rgba[3]);
  const icon=music.song_icons[musicEditor.enabled?0:songId+1],iconGroup=2100+20*((icon&0xf7)>>>4);
  if(icon)draw("modules",iconGroup+(icon&15),iconGroup,88,6,2);
  draw("th",8,6,304,1);
  const instrumentName=music.instruments.find(i=>i.id===instrument).name;
  const width=[...instrumentName].reduce((n,c)=>n+(ORIGINAL.font[c.charCodeAt(0)]?.[0]||4),0);
  text(instrumentName,13+Math.floor((57-width)/2),96);
  text(currentMusicTitle().slice(0,33),113,15);
  const pageNumber=String((musicEditor.enabled?musicEditor.index[musicEditor.mode]:songId)+1),pageWidth=[...pageNumber].reduce((n,c)=>n+ORIGINAL.font[c.charCodeAt(0)][0],0);
  text(pageNumber,271-Math.floor(pageWidth/2),10);
  if(musicEditor.enabled){for(let i=0;i<5;i++)screen.rect(305,38+i*12,13,9,0xffb6b6b6);if(!musicEditor.eraser)draw('modules',2208,2200,77,105);}
  for(const[label,x,y]of musicEditor.enabled?[["1",311,39],["10",308,51],["20",306,63],["30",306,75],["40",306,87]]:[["1",311,39],["6",309,51],["12",308,63],["18",308,75],["24",306,87]])text(label,x,y);
  drawScore();
  musicEditor.drawPalette(screen);musicEditor.drawMarker(screen,songPlaying);
  if(musicTerminal()){screen.rect(88,6,22,20,0xffffffff);screen.rect(113,13,145,13,0xffffffff);screen.rect(88,27,212,75,0xffffffff);screen.rect(258,8,23,6,0xff000000);screen.rect(258,9,23,13,0xffffffff);draw('modules',2207,2200,98,27,2);}
  musicEditor.drawContents(screen);if(musicEditor.contents){screen.rect(258,8,23,6,0xff000000);screen.rect(258,9,23,13,0xffffffff);}musicEditor.drawTitle(screen,tick);
  if(musicIdle.frame>=0){const b=music.idle_rect;draw("modules",2129+music.idle_frames[musicIdle.frame],2120,b[1],b[0],2);}
  const active=new Set([...held.values()].map(n=>n.pitch));
  if(songPlaying&&songPosition>=0&&!songEvents[songPosition].rest)active.add(songEvents[songPosition].pitch);
  for(const key of music.keys.filter(k=>!BLACK.has(k.pitch)))if(active.has(key.pitch))draw("modules",key.pressed_shape,2200,key.rectangle[1],key.rectangle[0],2);
  for(const key of music.keys.filter(k=>BLACK.has(k.pitch)))if(active.has(key.pitch))draw("modules",key.pressed_shape,2200,key.rectangle[1],key.rectangle[0],2);
  musicEditor.drawDrag(screen);drawMusicDialog();
}
function telescopeBusy(){return scene==='telescope'&&animations.some(a=>!a.done||a.tailWait);}
function interruptTelescope(){if(!telescopeBusy())return false;for(const a of animations)if(a.done&&a.tailWait){a.tailWait=false;audio.stopAll();dirty=true;}return true;}
function startTelescopeAnimation(replay=false) {
  animations=telescope<3?[animation('th',[800,820,840][telescope],[800,820,840][telescope])]:[];
  if(telescope===3){const a=new Animation(store,'modules',3610,3600,{startTick:tick,origin:[181,93],onSound:id=>{a.soundDue=tick+theaterSpeech(id);}});a.soundDue=tick;while(!a.frameUpdates)a.step(tick);a.tailWait=rewards.shelf.some(Boolean);a.done=!a.tailWait;animations=[a];}
}
function telescopeView() {
  screen.clear();const id=781+2*telescope,shape=store.shape("th",id);
  if(telescope===3)screen.draw(store,'th',id,780+2*telescope,160-Math.floor(shape.w/2),100-Math.floor(shape.h/2),2,[34,77,168,243]);
  // Original 6CEE subtracts each truncated half-size from the screen center.
  else draw("th",id,780+2*telescope,160-Math.floor(shape.w/2),100-Math.floor(shape.h/2),2);
  // Ordinary telescope replays restore their background when the SCR ends.
  if(telescope===3)rewards.drawShelf(screen);for(const a of animations)if(telescope===3||!a.done)a.draw(screen);draw("th",8,6,304,1);
}
function render() {
  if(roomTravel?.maze)roomTravel.effect.draw(screen,musicRoom);else if(roomTravel?.effect)roomTravel.effect.draw(screen,inside,resident);else if(scene==="outside")outside();else if(scene==='hollow')exterior.drawHollow(screen);else if(scene==="inside")inside();else if(scene==="music")musicRoom();else if(scene==='maze')maze.draw(screen);else if(scene==="theater")theater.draw(screen);else if(scene==="nature")nature.draw(screen);else if(scene==="boardgame")boardgame.draw(screen);else telescopeView();
  rewards.draw(screen);drawPreferences();drawStatusOverlay();
  if(pointerVisible&&!telescopeBusy()&&(!roomTravel||roomTravel.effect&&!roomTravel.effect.hidePointer)&&!(scene==='nature'&&nature.mode==='quiz'&&(nature.quiz.actorScript||nature.quiz.winAnimation&&!nature.quiz.winAnimation.done))&&!entering&&!(['inside','outside'].includes(scene)&&(room.environment||room.chirpUntil>tick||resident.busy&&!resident.clearingBalloon)||scene==='hollow'&&resident.ambientAnimation)&&!(scene==="theater"&&theater.hideCursor)) {
    const modal=preferences||statusOverlay,chalkCursor=!modal&&scene==="inside"&&chalk.tool>=0;
    const foreground=chalkCursor?(chalk.tool===6?0xffffffff:chalk.colors[chalk.tool]):!modal&&scene==='music'?(musicEditor.eraser?store.palette('modules',2200).rgba[12]:musicEditor.cursorColor):!modal&&scene==='inside'?(chalk.returnedColor??0xff55ffff):0xff55ffff;
    const eraserCursor=!modal&&scene==='music'&&musicEditor.eraser;
    const data=chalkCursor?bytes(ORIGINAL.raw[`th:CURS:${chalk.tool===6?4:3}`]):eraserCursor?bytes(ORIGINAL.raw['th:CURS:2']):!modal&&((scene==="theater"&&theater.busyCursor)||(scene==="inside"&&room.pendingEnvironment))?bytes(ORIGINAL.raw["th:CURS:1"]):ORIGINAL.cursor,x=Math.floor(pointer[0])-s16(data,eraserCursor?2:0),y=Math.floor(pointer[1])-s16(data,eraserCursor?0:2);
    for(let row=0;row<16;row++)for(let col=0;col<16;col++)if(!(u16(data,4+row*2)&(0x8000>>>col)))
      screen.rect(x+col,y+row,1,1,(u16(data,36+row*2)&(0x8000>>>col))?foreground:0xff000000);
  }
  ctx.putImageData(screen.image,0,0);const pad=$("chalk-pad");if(scene==="inside"&&pad)pad.getContext("2d").putImageData(chalk.bitmap.image,0,0);stats.frames++;dirty=false;
}
function keyAt(x,y) {
  return [...music.keys.filter(k=>BLACK.has(k.pitch)),...music.keys.filter(k=>!BLACK.has(k.pitch))].find(k=>{
    const[t,l,b,r]=k.rectangle;return x>=l&&x<r&&y>=t&&y<b;
  });
}
function point(event) {const r=canvas.getBoundingClientRect();return[(event.clientX-r.left)*320/r.width,(event.clientY-r.top)*200/r.height];}
function activate(x,y,owner,modifiers={}) {
  if(roomTravel){navigateScene(scene);return;}
  if(statusOverlay){statusOverlay=null;dirty=true;return;}
  if(preferences){clickPreferences(x,y);return;}
  if(rewards.active){rewards.click(x,y);return;}
  if(scene==='nature'&&nature.mode==='quiz'&&nature.quiz.interruptWait())return;
  if(scene==='telescope'&&interruptTelescope())return;
  if(['inside','outside','hollow'].includes(scene)&&(resident.interruptAudio()||room.interruptAudio()))return;
  if(scene==="outside") {if(resident.busy)return;if(resident.selected&&resident.begin(x,y))return;const result=exterior.click(x,y);if(result==='boy'||result==='girl')enter(result);else if(result==='ladder'){if(resident.selected||modifiers.ctrlKey)setScene('inside');}else if(result==='hollow')setScene('hollow');return;}
  if(scene==='hollow'){exterior.hollowClick(x,y);return;}
  if(scene==="inside") {
    if(resident.interruptFood())return;
    if(room.busy||resident.busy)return;
    audio.stopAll();
    if(resident.begin(x,y))return;
    if(room.open&&resident.hit([28,162,110,283],x,y)){room.toggle();return;}
    const cr=resident.rect();if(resident.hit([cr[0]+4,cr[1]+4,cr[2]-4,cr[3]-4],x,y)){resident.clickCharacter();return;}
    if(resident.hit([162,150,174,197],x,y)&&resident.pose!==0){resident.center();return;}
    if(x>=4&&x<41&&y>=27&&y<62){resident.speakStatus();return;}
    if(x>=160&&x<283&&y>=20&&y<40){if(!room.open)room.toggle();return;}
    if(x>=132&&x<154&&y>=21&&y<38){room.browse(x-132<38-y?-1:1);return;}
    if(x>=58&&x<134&&y>=24&&y<35){room.readCalendar();return;}
    if(x>=163&&x<283&&y>=40&&y<80){room.nextCloud();audio.start('digisnd:1044');return;}
    if(x>=92&&x<114&&y>=108&&y<118){tellTime();return;}
    if(x>=118&&x<145&&y>=129&&y<146){audio.start('digisnd:1013');return;}
    if(x>=21&&x<54&&y>=6&&y<27){room.interact('spider');return;}
    if(x>=237&&x<260&&y>=81&&y<94){room.interact('chirp');return;}
    if(x>=211&&x<283&&y>=81&&y<104){room.interact('nest');return;}
    if(x>=286&&x<318&&y>=15&&y<91){if(resident.pose===4)theaterSpeech(20001);else resident.action(31);return;}
    if(x>=2&&x<36&&y>=120&&y<156){if(resident.wakeTime)room.sayTime(resident.wakeTime,true);else room.say([11028]);return;}
    for(let i=17;i<=20;i++)if(resident.hit(resident.tables.objects[i].inside,x,y)){resident.fruit(i,x,y);return;}
    if(x>=242&&x<305&&y>=177){navigateScene('outside');return;}
    if(y>=92&&y<98){const tool=Math.floor((x-63)/12);if(tool>=0&&tool<7&&x<(tool===6?149:73+12*tool)){chalk.select(tool);return;}}
    if(chalk.tool>=0&&x>=52&&x<157&&y>=40&&y<97){chalk.begin(x,y);syncChalkTools();return;}
    if(x>=49&&x<59&&y>=86&&y<97){askChalk();return;}
    if(x>=60&&x<154&&y>=45&&y<92){chalkOpen=true;insidePanel();status("Choose a chalk color, then draw on the board or the enlarged pad.");return;}
    if(x>=138&&x<223&&y>=181){navigateScene("boardgame");return;}
    if(x>=7&&x<106&&y>=175)navigateScene("music");
    else if(resident.hit(ORIGINAL.theater.room_entrance,x,y))navigateScene("theater");
    else if(x>=122&&x<147&&y>=99&&y<119)navigateScene("nature");
    else if(x>=167&&x<228&&y>=102&&y<157)navigateScene("telescope");
    else if(resident.hit(resident.rect(),x,y)){resident.clickCharacter();}
    else status("Try the keyboard, theater curtain, or telescope.");
  } else if(scene==="music") {
    if(musicIdle.frame>=0)finishMusicIdle();
    if(musicEditor.titleEntry){musicEditor.acceptTitle();dirty=true;return;}
    if(musicPrint){navigateScene('music');return;}
    if(musicDialog){if(x>=7&&x<39&&y>=40&&y<80)answerMusic(true);else if(x>=43&&x<77&&y>=40&&y<80)answerMusic(false);return;}
    if(musicSelector.open){musicSelector.click(x,y);dirty=true;return;}
    if(musicEditor.click(x,y)){if(musicEditor.drag?.kind==='note'){const pitch=musicEditor.song[5+2*musicEditor.drag.index]&127;held.set(owner,{pitch,voice:playPitch(pitch)});}dirty=true;return;}
    const key=keyAt(x,y);if(key){noteDown(key.pitch,owner);return;}musicAuditionPitch=null;
    if(x>=54&&x<83&&y>=136&&y<158)toggleSong();
    else if(x>=307&&y<15)navigateScene("inside");
    else if(x<80&&y<108)auditionInstrument();
    else if(x>=305&&x<318&&y>=26&&y<35)showMusicContents(1);
    else if(musicEditor.contents&&x>=88&&x<300&&y>=27&&y<93){const col=x<194?0:1,row=Math.floor((y-27)/23);if(row<3&&y<47+23*row)selectMusicPage((musicEditor.contents-1)*6+col*3+row);}
    else if(x>=258&&x<281&&y>=1&&y<22&&musicEditor.contents)selectMusicPage(musicEditor.enabled?musicEditor.index[musicEditor.mode]:songId);
    else if(x>=284&&x<303&&y>=9&&y<26)turnMusicPage(x-284>y-9?1:-1);
    else if(x>=44&&x<91&&y>=115&&y<134){stopPlayback(true);tempo=music.tempo_thresholds.filter(boundary=>x>=boundary).length;$("tempo").value=tempo;currentMusicSong()[2]=tempo;if(musicEditor.enabled)musicEditor.save();dirty=true;}
    else if(x>=265&&x<304&&y>=140&&y<157)setMusicScore(!longScore);
    else if(x>=264&&x<305&&y>=161&&y<178)setMusicComposing(!musicEditor.enabled);
    else if(x>=235&&x<260&&y>=112&&y<138)eraseMusicSong(!!modifiers.ctrlKey);
    else if(x>=262&&x<285&&y>=112&&y<138){if(musicEditor.editable)askMusic('Create new song?',()=>musicEditor.randomize(tick));else if(!musicEditor.enabled)copyMusicSong();}
    else if(x>=98&&x<124&&y>=117&&y<138){currentMusicSong()[4]^=1;if(musicEditor.enabled)musicEditor.save();dirty=true;}
    else if(musicEditor.editable&&x>=113&&x<258&&y>=13&&y<26)musicEditor.beginTitle(tick);
    else if(x<42&&y>=113&&y<136){stopPlayback(true);releaseAll();musicSelector.show();}
    else if(x>=289&&y>=113&&y<138)printMusic();
    else if(x>=11&&x<51&&y>=141&&y<175)navigateScene('maze');
    else if(x>=54&&x<84&&y>=159&&y<181){repeatSong=!repeatSong;$('repeat-song').value=Number(repeatSong);dirty=true;}
    else if(x>=305&&y>=38&&y<95){const tab=Math.min(4,Math.floor((y-38)/12));selectMusicPage((musicEditor.enabled?[0,9,19,29,39]:[0,5,11,17,23])[tab]);}
    else status("Use the keys to play, or choose a song and press Play.");
  } else if(scene==="theater") {if(x>=304&&y<23){navigateScene("inside");return;}if(!theater.beginDrag(x,y))theater.click(x,y);dirty=true;}
  else if(scene==="nature"){if(x>=304&&y<23){navigateScene("inside");return;}if(!nature.beginDrag(x,y))nature.click(x,y,modifiers);dirty=true;}
  else if(scene==="boardgame"){if(x>=304&&y<23){navigateScene("inside");return;}boardgame.click(x,y);dirty=true;}
  else if(scene==='maze'){maze.click(x,y);dirty=true;}
  else if(scene==="telescope") {const[t,l,b,r]=ORIGINAL.telescope.rectangles[telescope];if(x<l||x>=r||y<t||y>=b)navigateScene("inside");else{startTelescopeAnimation(true);dirty=true;}}
}
canvas.addEventListener("contextmenu",event=>event.preventDefault());
canvas.addEventListener("pointerdown",async event=>{
  musicEditor.pointerMoved();
  event.preventDefault();canvas.focus();canvas.setPointerCapture(event.pointerId);const p=point(event),owner=`pointer:${event.pointerId}`;
  pointer=p;pointerVisible=event.pointerType!=="touch";dirty=true;
  pointers.set(event.pointerId,owner);await audio.unlock();if(pointers.has(event.pointerId))activate(...p,owner,event);
});
canvas.addEventListener("pointermove",event=>{
  musicEditor.pointerMoved();
  pointer=point(event);pointerVisible=event.pointerType!=="touch";dirty=true;
  if(preferences||statusOverlay)return;
  if((scene==='inside'||scene==='outside')&&resident.move(...pointer))return;
  if(scene==="inside"){pointer=chalk.move(...pointer,pointers.has(event.pointerId));return;}
  if(scene==="theater"&&pointers.has(event.pointerId)){theater.moveDrag(...pointer);return;}
  if(scene==="nature"&&pointers.has(event.pointerId)){nature.moveDrag(...pointer);return;}
  if(scene==='music'&&musicEditor.move(...pointer))return;
  if(scene!=="music"||!pointers.has(event.pointerId))return;
  const owner=pointers.get(event.pointerId),key=keyAt(...point(event));
  if(held.get(owner)?.pitch!==key?.pitch){noteUp(owner);if(key)noteDown(key.pitch,owner);}
});
for(const type of ["pointerup","pointercancel","lostpointercapture"])canvas.addEventListener(type,event=>{if(!pointers.has(event.pointerId))return;noteUp(`pointer:${event.pointerId}`);pointers.delete(event.pointerId);chalk.end();resident.end(type!=="pointerup");if(theater)theater.endDrag(type!=="pointerup");if(nature)nature.endDrag();musicEditor.end(type!=="pointerup");});
for(const pitch of WHITE) {
  const b=document.createElement("button");b.className="piano-key";b.dataset.pitch=pitch;b.textContent=NOTE_NAMES[pitch];
  b.setAttribute("aria-label",`${NOTE_NAMES[pitch]} key`);$("touch-keys").append(b);
}
for(const pitch of BLACK) {
  const b=document.createElement("button");b.className="piano-key black";b.dataset.pitch=pitch;b.textContent="♯";
  b.style.left=`${WHITE.filter(n=>n<pitch).length*10-2.75}%`;b.setAttribute("aria-label",`${NOTE_NAMES[pitch]} key`);$("touch-keys").append(b);
}
for(const b of $("touch-keys").querySelectorAll("button")) {
  b.addEventListener("pointerdown",async e=>{e.preventDefault();b.setPointerCapture(e.pointerId);b.dataset.pressed=String(e.pointerId);await audio.unlock();if(b.dataset.pressed===String(e.pointerId))noteDown(Number(b.dataset.pitch),`touch:${e.pointerId}`);});
  for(const type of ["pointerup","pointercancel","lostpointercapture"])b.addEventListener(type,e=>{delete b.dataset.pressed;noteUp(`touch:${e.pointerId}`);});
  b.addEventListener("keydown",async e=>{if((e.key===" "||e.key==="Enter")&&!e.repeat){e.preventDefault();b.dataset.keyHeld="yes";await audio.unlock();if(b.dataset.keyHeld)noteDown(Number(b.dataset.pitch),`button:${b.dataset.pitch}`);}});
  b.addEventListener("keyup",e=>{if(e.key===" "||e.key==="Enter"){e.preventDefault();delete b.dataset.keyHeld;noteUp(`button:${b.dataset.pitch}`);}});
  b.addEventListener("blur",()=>{delete b.dataset.keyHeld;noteUp(`button:${b.dataset.pitch}`);});
}
function keyboardPointer(){
  if(tick<pointerKeyDue)return;const dx=pointerKeys.has('ArrowRight')?1:pointerKeys.has('ArrowLeft')?-1:0,dy=pointerKeys.has('ArrowDown')||pointerKeys.has('Numpad5')?1:pointerKeys.has('ArrowUp')?-1:0;if(!dx&&!dy)return;
  pointer=[Math.max(0,Math.min(319,pointer[0]+dx)),Math.max(0,Math.min(199,pointer[1]+dy))];pointerVisible=true;pointerKeyDue=tick+(pointerShift?1:3+(pointerKeys.has('Space')?5:0));dirty=true;
  if(preferences||statusOverlay)return;const pressed=pointerKeys.has('Space')||pointerKeys.has('Enter');
  if((scene==='inside'||scene==='outside')&&resident.move(...pointer))return;
  if(scene==='inside')pointer=chalk.move(...pointer,pressed);else if(scene==='theater'&&pressed)theater.moveDrag(...pointer);else if(scene==='nature'&&pressed)nature.moveDrag(...pointer);
  else if(scene==='music'){musicEditor.pointerMoved();if(musicEditor.move(...pointer))return;if(pressed){const key=keyAt(...pointer);if(held.get('keyboard:pointer')?.pitch!==key?.pitch){noteUp('keyboard:pointer');if(key)noteDown(key.pitch,'keyboard:pointer');}}}
}
window.addEventListener("keydown",async event=>{
  if(roomTravel){event.preventDefault();navigateScene(scene);return;}
  pointerShift=event.shiftKey;
  const form=/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(event.target.tagName);
  if(!form&&!musicEditor.titleEntry&&['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Numpad5'].includes(event.code)){event.preventDefault();if(!pointerKeys.has(event.code)){pointerKeys.add(event.code);pointerKeyDue=tick;keyboardPointer();}return;}
  if(['Control','Alt','Shift','Meta'].includes(event.key))return;
  if(statusOverlay){event.preventDefault();statusOverlay=null;dirty=true;return;}
  if(event.ctrlKey&&['s','v'].includes(event.key.toLowerCase())){event.preventDefault();if(event.key.toLowerCase()==='s'){audio.enabled=!audio.enabled;$('sound').checked=audio.enabled;if(!audio.enabled)audio.stopAll();showStatusOverlay(`Sound is ${audio.enabled?'On':'Off'}`);}else showStatusOverlay('Version 1.1');return;}
  const nativeKey=event.key==='Escape'||event.key==='Enter'||event.code==='Space'||'SDGHJL;ZXCVBNM,./'.includes(event.key.toUpperCase())&&event.key.length===1;
  if(event.repeat)return;
  if(preferences){if(!nativeKey)return;if(form&&(event.key==='Enter'||event.code==='Space'))return;event.preventDefault();if(preferences.kind==='question'){clickPreferences(...pointer);return;}if(preferences.kind==='help')clickPreferences(...pointer);else if(event.key==='Escape'||event.key==='Enter')closePreferences();return;}
  if(event.key==='F1'){event.preventDefault();openHelp(event);return;}
  if(event.key==='F2'){event.preventDefault();openPreferences();return;}
  if(scene==='music'&&musicEditor.titleEntry){event.preventDefault();musicEditor.titleKey(event.key);return;}
  if(rewards.active){event.preventDefault();if(event.key==='Escape')rewards.dismiss();else rewards.interrupt();return;}
  if(nativeKey&&!form&&scene==='telescope'&&interruptTelescope()){event.preventDefault();return;}
  if(nativeKey&&!form&&['inside','outside','hollow'].includes(scene)&&(resident.interruptAudio()||room.interruptAudio())){event.preventDefault();return;}
  if(event.key==="Escape"){event.preventDefault();if(scene==='boardgame'&&boardgame.motion.busy)return;if(scene==='maze'){if(maze.chooser)maze.closeGuess();else navigateScene('music');}else if(scene!=="outside")navigateScene(scene==="inside"?"outside":"inside");return;}
  if(/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(event.target.tagName))return;
  if(event.repeat)return;
  if(event.key==='Enter'||event.code==='Space'||nativeKey&&scene!=='music'){event.preventDefault();pointerKeys.add(event.code);await audio.unlock();if(pointerKeys.has(event.code))activate(...pointer,'keyboard:pointer',event);return;}
  if(scene==="music") {
    if(musicDialog){if(nativeKey)activate(...pointer,'keyboard:pointer',event);return;}
    const key=music.keys.find(k=>k.keyboard===event.key.toUpperCase());
    if(key){event.preventDefault();const[t,l,b,r]=key.rectangle;pointer=[Math.floor((l+r)/2),Math.floor((t+b)/2)];pointerVisible=true;dirty=true;downKeys.add(event.code);await audio.unlock();if(downKeys.has(event.code))noteDown(key.pitch,`key:${event.code}`);}
  }
});
window.addEventListener("keyup",event=>{pointerShift=event.shiftKey;const activated=pointerKeys.has(event.code)&&!event.code.startsWith('Arrow')&&event.code!=='Numpad5';pointerKeys.delete(event.code);if(activated){noteUp('keyboard:pointer');chalk.end();resident.end();theater?.endDrag();nature?.endDrag();musicEditor.end();}downKeys.delete(event.code);noteUp(`key:${event.code}`);});
window.addEventListener("blur",()=>{releaseAll();if(theater)theater.save();});
window.addEventListener('pagehide',()=>{gameSave?.save();if(theater)theater.save();resident.save();});
document.addEventListener("visibilitychange",()=>{lastFrame=performance.now();clockRemainder=0;if(document.hidden){releaseAll();stopPlayback(true);}});
$("home").onclick=chooseFriend;$("back").onclick=()=>{if(scene==="nature"&&nature.mode==="quiz"){nature.leaveQuiz();return;}navigateScene(scene==='maze'?'music':scene==="inside"?"outside":"inside");};
$("preferences").onclick=openPreferences;$("help").onclick=()=>openHelp();
$("fullscreen").onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(_e){status("Full screen is unavailable in this browser.");}};
function setReadingSize(value){const size=Math.max(18,Math.min(30,Number(value)||22));$("text-size").value=size;document.documentElement.style.setProperty("--read-size",`${size}px`);return size;}
try{setReadingSize(localStorage.getItem('treehouse-reading-size-v1'));}catch(_error){setReadingSize(22);}
$("text-size").oninput=e=>{const size=setReadingSize(e.target.value);try{localStorage.setItem('treehouse-reading-size-v1',String(size));}catch(_error){}};
$("sound").onchange=async e=>{audio.enabled=e.target.checked;if(audio.enabled)await audio.unlock();else audio.stopAll();};
$("next-fact").onclick=()=>{if(scene==="nature"){nature.nextFact();return;}factIndex++;showFact();};
$("read-aloud").disabled=!("speechSynthesis"in window);
$("read-aloud").onclick=()=>{window.speechSynthesis.cancel();const voice=window.speechSynthesis.getVoices().find(v=>v.localService&&v.lang.startsWith("en"));if(!voice){status("No English voice is installed on this device. You can make the text larger below.");return;}const reading=scene==='inside'&&room.open?`${room.dateLabel}. ${room.story.heading}. ${room.story.body}`:`${$("heading").textContent} ${$("instructions").textContent} ${$("fact-card").hidden?"":$("fact").textContent}`;const phrase=new SpeechSynthesisUtterance(reading);phrase.voice=voice;phrase.rate=.85;window.speechSynthesis.speak(phrase);};
function serviceBalloon(){let dirty=false;
    if(scene==="inside"&&!room.busy&&!resident.busy&&!resident.drag&&!balloon.hidden&&(balloon.lifting?tick>=balloon.due:tick>balloon.due)){
      if(balloon.lifting){
        if(balloon.x<157&&balloon.x+29>52&&balloon.y<99&&balloon.y+38>38){balloon.y-=2;balloon.due=tick+2;dirty=true;}
        else{balloon.lifting=false;balloon.due=tick+48;}
      }else if(chalk.tool<0){
        const dx=Math.floor(pointer[0])-(balloon.x+14),dy=Math.min(Math.floor(pointer[1]),100)-(balloon.y+19),ax=Math.abs(dx),ay=Math.abs(dy);
        if(ax>=2)balloon.x+=Math.sign(dx)*(ax>ay?2:1);if(ay>=2)balloon.y+=Math.sign(dy)*(ay>=ax?2:1);balloon.due=tick+48;const object=resident.objects.find(o=>o.type===6);if(object){resident.objects.splice(resident.objects.indexOf(object),1);resident.objects.push(object);}dirty=true;
      }
    }
    return dirty;
}
function advance(count=1) {
  for(let i=0;i<count;i++) {
    tick++;
    keyboardPointer();
    if(roomTravel){updateRoomTravel();dirty=true;continue;}
    if(scene==='outside'&&!entering&&exterior.update(tick))dirty=true;
    if(statusOverlay){if(tick>=statusOverlay.due){statusOverlay=null;dirty=true;}continue;}
    if(preferences){if(preferences.kind==='question')dirty=true;if(tick>=preferences.due){if(preferences.closing)closePreferences();else if(tick===preferences.due)dirty=true;}continue;}
    if(rewards.active){if(rewards.update(tick))dirty=true;continue;}
    if(serviceBalloon())dirty=true;
    if(scene==="theater"&&theater.update(tick))dirty=true;
    // A closing curtain can begin room travel during this tick. Defer room
    // timers just as when travel was already active at the start of the tick.
    if(roomTravel){dirty=true;continue;}
    if(scene==="nature"&&nature.update(tick))dirty=true;
    if(scene==="boardgame"&&boardgame.update(tick))dirty=true;
    if(scene==='music'&&musicAuditionPitch!==null&&!held.size&&musicIdle.frame<0&&tick<=musicIdle.due&&tick>=musicAuditionDue){musicAuditionPitch=null;dirty=true;}
    if(scene==="music"&&musicSelector.update(tick))dirty=true;
    if(scene==='music'&&musicEditor.update(tick))dirty=true;
    if(scene==='music'&&!musicPrint&&(musicDialog||musicEditor.titleEntry))dirty=true;
    if(scene==='maze'&&maze.update(tick))dirty=true;
    if(scene==='inside'&&room.update(tick,resident.busy))dirty=true;
    if(scene==='inside'&&room.question&&room.height===room.target){
      if(room.question==='closing')room.question='clearing';
      if(room.question==='answered'){if(room.questionAccept)room.question='clear-board';else{room.question=null;room.blank=false;}dirty=true;}
      if(room.question==='clearing'||room.question==='clear-board'){
        const r=room.question==='clearing'?[28,162,110,283]:[38,52,99,157];
        if(!balloon.hidden&&balloon.x<r[3]&&balloon.x+29>r[1]&&balloon.y<r[2]+2&&balloon.y+38>r[0]-2){if(tick>=room.questionDue){balloon.y-=2;room.questionDue=tick+2;dirty=true;}}
        else if(room.question==='clearing'){room.blank=true;room.question='opening';room.slide(98);}
        else{room.question=null;room.blank=false;chalk.clear();dirty=true;}
      }else if(room.question==='opening'){room.question='asking';askQuestion('Erase Chalkboard?',()=>chalk.clear(),true);}
    }
    if(resident.update(tick))dirty=true;
    if(scene==="music"&&!held.size&&!musicSelector.open&&!musicDialog&&(musicIdle.frame<0?tick>musicIdle.due:tick>=musicIdle.due)){musicIdle.frame++;if(musicIdle.frame>=music.idle_frames.length)finishMusicIdle();else musicIdle.due=tick+4;dirty=true;}
    if(audition&&!audition.done){audition.update(tick);if(audition.done){audio.stop(auditionVoice);auditionVoice=null;}dirty=true;}
    for(const a of animations) {
      if(!a.done){a.update(tick);dirty=true;if(a.done){stats.animationsCompleted++;if(scene==='telescope'&&telescope<3)audio.stopAll();}}
      if(a.done&&a.tailWait&&tick>=a.soundDue){a.tailWait=false;audio.stopAll();dirty=true;}
    }
    if(transition&&transition())continue;
    if(songPlaying)advanceSong();
  }
}
function frame(now) {
  if(failed)return;
  try {
    if(!document.hidden) {
      clockRemainder+=Math.min(now-lastFrame,250)*TICK_HZ/1000;
      const count=Math.floor(clockRemainder);clockRemainder-=count;advance(count);
      if(dirty)render();
    }
    lastFrame=now;requestAnimationFrame(frame);
  }catch(error){failed=true;audio.stopAll();stats.errors.push(String(error));status(`The demo stopped: ${error.message}`);console.error(error);}
}
// Diagnostic API: deterministic engine stepping and native pixel export. It is
// used for verification, never for normal input or to replay emulator pictures.
window.treehouseDemo={get state(){return{scene,character,tick,entering,instrument,songId,songPlaying,recording,held:held.size,stats,nature:nature?{time:nature.time,attribute:nature.attribute,values:[...nature.values],category:nature.category,selected:nature.selected,counts:nature.objects.map(a=>a.length)}:null,theater:theater?{selection:[...theater.selection],order:[...theater.order],options:theater.options,category:theater.category,playing:theater.playing,sentence:theater.sentence(),validation:theater.validation(),performances:theater.performances}:null};},setScene,enter,advance,render,
  setPointer(x,y,visible=true){musicEditor.pointerMoved();pointer=[x,y];pointerVisible=visible;dirty=true;},
  pixels:()=>Array.from(screen.image.data),noteDown,noteUp,stopPlayback,toggleSong,store,screen,chalk,
  freeze(){failed=true;},resume(){failed=false;lastFrame=performance.now();requestAnimationFrame(frame);}};
gameSave=new GamePersistence(store);
setScene("outside");render();requestAnimationFrame(frame);
