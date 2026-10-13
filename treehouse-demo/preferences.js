"use strict";
function openPreferences(){
  if(preferences||statusOverlay)return;
  if(roomTravel||entering||rewards.active||resident.busy||room.busy||songPlaying||held.size||musicDialog||musicEditor.titleEntry||maze?.busy&&scene==='maze'||theater?.playing&&scene==='theater'||nature?.quiz.busy&&scene==='nature'&&nature.mode==='quiz'||boardgame?.motion.busy&&scene==='boardgame'){status('Finish this action, then open Settings.');return;}
  chalk.select(-1);releaseAll();const visible=pointerVisible;pointerVisible=false;render();pointerVisible=visible;
  const labels={};for(const id of ['chapter','heading','instructions','caption'])labels[id]=$(id).textContent;
  preferences={background:screen.clone(),nodes:[...$('controls').childNodes],labels,fact:$('fact-card').hidden,keys:$('touch-keys').hidden,flash:-1,due:0};
  $('chapter').textContent='SETTINGS';$('heading').textContent='Make yourself at home.';$('instructions').textContent='Choose how to play. Your settings and creations are saved on this device.';$('fact-card').hidden=true;$('touch-keys').hidden=true;
  preferencesPanel();dirty=true;
}
function preferencesPanel(){
  const p=gameSave.preferences;
  $('controls').replaceChildren(
    button(`Sound: ${audio.enabled?'on':'off'}`,()=>togglePreference(0)),
    button(`Printing: ${p.printing?'on':'off'}`,()=>togglePreference(1)),
    button(`Music maze: ${p.advanced?'advanced':'beginner'}`,()=>togglePreference(3)),
    button('Save game file',()=>downloadGameFile(gameSave.exportData(),'STATUS.DAT')),
    button('Load game file',()=>chooseGameFile('status')),
    button('Save songbooks',()=>downloadGameFile(musicEditor.exportData(),'SONGS.DAT')),
    button('Load songbooks',()=>chooseGameFile('songs')),
    button('Done',closePreferences,true));
}
function togglePreference(row){
  if(!preferences)return;const p=gameSave.preferences;
  if(row===0){audio.enabled=!audio.enabled;p.sound=audio.enabled;$('sound').checked=audio.enabled;if(!audio.enabled)audio.stopAll();}
  else if(row===1)p.printing=!p.printing;else if(row===2)p.printer=1-p.printer;else if(row===3){p.advanced=!p.advanced;if(maze){maze.initialAdvanced=p.advanced;maze.hard=p.advanced;}}else if(row===4)p.speed=!p.speed;
  preferences.flash=row;preferences.due=tick+12;preferencesPanel();dirty=true;
}
function closePreferences(){
  if(!preferences)return;const old=preferences;preferences=null;
  $('controls').replaceChildren(...old.nodes);for(const [id,value]of Object.entries(old.labels))$(id).textContent=value;$('fact-card').hidden=old.fact;$('touch-keys').hidden=old.keys;
  gameSave.save();
  // A nature confirmation returns directly to exploration, without a room event.
  if(!(old.kind==='question'&&scene==='nature'&&nature.mode==='explore'))resident.scheduleAmbient();
  musicIdle.due=tick+600;status(old.kind==='help'?'Help closed.':old.kind==='question'?'':'Settings saved.');dirty=true;
}
function drawPreferences(){
  if(!preferences)return;if(preferences.kind==='help'){drawHelp();return;}if(preferences.kind==='question'){drawQuestion();return;}const colors=modalColors();screen.restore(preferences.background);screen.rect(32,43,256,109,0xff000000);screen.rect(33,44,254,107,colors.white);
  const p=gameSave.preferences,font=store.data.heading_font,blue=colors.blue,center=(label,y,color)=>{const width=[...label].reduce((n,c)=>n+(font[c.charCodeAt(0)]?.[0]||4)+1,0);screen.text(store,label,160-Math.floor(width/2),y,color,font,1);};
  center('PREFERENCES',47,blue);
  const rows=[audio.enabled?'Sound is ON/off':'Sound is on/OFF',p.printing?'Printing is ON/off':'Printing is on/OFF','Printer: Not Selected',p.advanced?'Music Game Level: beginner/ADVANCED':'Music Game Level: BEGINNER/advanced',p.speed?'Speed Optimization is ON/off':'Speed Optimization is on/OFF'];
  rows.forEach((label,i)=>center(label,63+14*i,preferences.flash===i&&tick<preferences.due?colors.red:0xff000000));
  for(const [t,l,b,r]of [[138,243,148,283],[137,244,149,282]])screen.rect(l,t,r-l,b-t,0xff000000);for(const [t,l,b,r]of [[137,242,147,282],[136,243,148,281]])screen.rect(l,t,r-l,b-t,blue);const label='Done',width=[...label].reduce((n,c)=>n+font[c.charCodeAt(0)][0]+1,0);screen.text(store,label,262-Math.floor(width/2),138,0xff000000,font,1);
}
function clickPreferences(x,y){
  if(preferences.kind==='question'){const[t,l,b,r]=preferences.room?[47,178,87,212]:[126,16,166,50];answerQuestion(!preferences.yes||x>=l&&x<r&&y>=t&&y<b);return;}
  if(preferences.kind==='help'){const[t,l,b,r]=preferences.layout.rectangle;if(x>=l&&x<r&&y>=t&&y<b)finishHelp();return;}
  if(x>=242&&x<282&&y>=136&&y<148){closePreferences();return;}
  if(x>=34&&x<286&&y>=61&&y<131)togglePreference(Math.floor((y-61)/14));
}
function askNature(message,yes){
  if(preferences||nature?.eraseTask)return;askQuestion(message,yes);
}
function askChalk(){
  if(preferences||room.busy||resident.busy)return;chalk.select(-1);room.question=room.height>28?'closing':'clearing';room.pendingDate=null;room.target=28;room.blank=false;room.due=tick+2;room.questionDue=tick;dirty=true;
}
function askQuestion(message,yes,inRoom=false){
  const visible=pointerVisible;pointerVisible=false;render();pointerVisible=visible;
  const labels={};for(const id of ['chapter','heading','instructions','caption'])labels[id]=$(id).textContent;
  preferences={kind:'question',room:inRoom,message,yes,start:tick,background:screen.clone(),nodes:[...$('controls').childNodes],labels,fact:$('fact-card').hidden,keys:$('touch-keys').hidden};
  $('instructions').textContent=message;$('fact-card').hidden=true;$('controls').replaceChildren(...(yes?[button('Yes',()=>answerQuestion(true),true),button('No',()=>answerQuestion(false))]:[button('OK',()=>answerQuestion(true),true)]));dirty=true;
}
function answerQuestion(accept){const p=preferences;if(p?.kind!=='question')return;closePreferences();if(p.room){room.question='answered';room.questionAccept=accept;room.target=28;room.due=tick+2;}else if(accept)p.yes?.();dirty=true;}
function drawQuestion(){
  const p=preferences,font=store.data.font,width=text=>[...text].reduce((n,c)=>n+(font[c.charCodeAt(0)]?.[0]||0),0),lines=[];let rest=p.message;
  while(rest){let n=0,w=0,last=0;for(;n<rest.length;n++){w+=width(rest[n]);if(w>116)break;if(rest[n]===' '||rest[n]==='-'||rest[n+1]===' ')last=n+1;}const count=n===rest.length?n:last||Math.max(1,n);lines.push(rest.slice(0,count));rest=rest.slice(count).replace(/^ /,'');}
  screen.restore(p.background);
  if(p.room){screen.rect(168,29,110,58,0xffffffff);screen.text(store,p.message,223-Math.floor(width(p.message)/2),33);const phase=Math.floor((tick-p.start)/12);screen.draw(store,'th',86+(phase&1),80,178,47,2);screen.draw(store,'th',88+[0,1,2,1][phase&3],80,234,47,2);for(const[label,x,color]of [['Yes',182,0xff00aa00],['No',238,0xff0000aa]]){screen.rect(x+2,77,24,9,0xff000000);screen.rect(x+1,78,26,7,0xff000000);screen.rect(x+1,76,24,9,color);screen.rect(x,77,26,7,color);screen.text(store,label,x+13-Math.floor(width(label)/2),77);}return;}
  screen.rect(6,98,118,68,0xffffffff);lines.forEach((line,i)=>screen.text(store,line,65-Math.floor(width(line)/2),112-5*lines.length+10*i));
  const phase=Math.floor((tick-p.start)/12),face=(id,x)=>screen.draw(store,'th',id,80,x,126,2),buttonFace=(label,x,color)=>{screen.rect(x+2,156,24,9,0xff000000);screen.rect(x+1,157,26,7,0xff000000);screen.rect(x+1,155,24,9,color);screen.rect(x,156,26,7,color);screen.text(store,label,x+13-Math.floor(width(label)/2),156);};
  if(p.yes){face(86+(phase&1),16);face(88+[0,1,2,1][phase&3],80);buttonFace('Yes',20,0xff00aa00);buttonFace('No',84,0xff0000aa);}else{face(86,48);buttonFace('OK',52,0xff0000aa);}
}
function printNature(){if(!gameSave.preferences.printing){status('Printing is turned off in Settings.');return;}askNature('Print this Scene?',()=>{const visible=pointerVisible;pointerVisible=false;render();window.print();pointerVisible=visible;dirty=true;});}
function modalColors(){const p=scene==='theater'?store.palette('modules',3000).rgba:null;return{blue:p?p[12]:0xffff5555,white:p?p[1]:0xffffffff,red:p?p[10]:0xff5555ff};}
function helpContext(){
  if(scene==='music')return musicSelector.open?(musicSelector.category<0?6:7):musicEditor.enabled?15:0;
  if(scene==='maze')return maze.largeIntro||['win','arrival'].includes(maze.phase)?17:8;
  if(scene==='theater')return theater.options?13:theater.mixUp?(theater.propsEnabled?20:22):theater.propsEnabled?21:2;
  if(scene==='boardgame'){const g=boardgame;return g.options?10:g.winner>=0||g.loser>=0?23:g.exchange?25:g.phase==='reward'?(g.mode?24:16):3;}
  if(scene==='nature'){const q=nature.quiz;return nature.mode!=='quiz'?1:q.options?11:q.winner>=0?28:q.phase!=='question'?26:q.help[q.role()]?27:9;}
  return resident.selected?19:18;
}
function openHelp(event={}){
  if(statusOverlay||preferences||roomTravel||entering||rewards.active||resident.busy||room.busy||songPlaying||held.size||musicDialog||musicEditor.titleEntry||scene==='maze'&&maze.busy||scene==='theater'&&theater.playing||scene==='nature'&&nature.mode==='quiz'&&nature.quiz.busy||scene==='boardgame'&&boardgame.motion.busy&&!boardgame.exchange)return;
  const context=event.ctrlKey&&event.altKey&&pointer[0]<2&&pointer[1]<2?29:helpContext(),layout=ORIGINAL.help.find(h=>h.context===context);
  chalk.select(-1);releaseAll();const visible=pointerVisible;pointerVisible=false;render();pointerVisible=visible;
  const labels={};for(const id of ['chapter','heading','instructions','caption'])labels[id]=$(id).textContent;
  preferences={kind:'help',layout,background:screen.clone(),nodes:[...$('controls').childNodes],labels,fact:$('fact-card').hidden,keys:$('touch-keys').hidden,due:0};
  $('chapter').textContent='HELP';$('heading').textContent=layout.title;$('instructions').textContent=layout.body.replace(/\r/g,'\n');$('fact-card').hidden=true;$('touch-keys').hidden=true;$('controls').replaceChildren(button('Done',finishHelp,true));dirty=true;
}
function finishHelp(){if(!preferences||preferences.kind!=='help')return;if(preferences.closing){closePreferences();return;}preferences.closing=true;preferences.due=tick+20;dirty=true;}
function drawHelp(){
  const h=preferences.layout,[t,l,b,r]=h.rectangle,c=modalColors(),font=store.data.heading_font;screen.restore(preferences.background);screen.rect(l,t,r-l,b-t,0xff000000);screen.rect(l+1,t+1,r-l-2,b-t-2,c.white);
  const centered=(text,x,y,color)=>{const width=[...text].reduce((n,ch)=>n+(font[ch.charCodeAt(0)]?.[0]||4)+1,0);screen.text(store,text,x-Math.floor(width/2),y,color,font,1);};
  centered(h.title,160,h.title_glyph_top,c.blue);h.body_lines.forEach((line,i)=>screen.text(store,line.replace(/\r/g,''),h.body_x,h.body_glyph_top+i*h.body_line_step,0xff000000));
  const bt=b-16,bot=b-4;for(const[y,x,yy,xx]of [[bt+2,243,bot,283],[bt+1,244,bot+1,282]])screen.rect(x,y,xx-x,yy-y,0xff000000);for(const[y,x,yy,xx]of [[bt+1,242,bot-1,282],[bt,243,bot,281]])screen.rect(x,y,xx-x,yy-y,preferences.closing?c.red:c.blue);centered('Done',262,bt+2,0xff000000);
}
function showStatusOverlay(label){
  const visible=pointerVisible;pointerVisible=false;render();pointerVisible=visible;statusOverlay={label,background:screen.clone(),due:tick+180};status(label);dirty=true;
}
function drawStatusOverlay(){if(!statusOverlay)return;const c=modalColors(),font=store.data.heading_font,label=statusOverlay.label,width=[...label].reduce((n,ch)=>n+font[ch.charCodeAt(0)][0]+1,0);screen.restore(statusOverlay.background);screen.rect(108,176,104,16,c.red);screen.rect(109,177,102,14,c.white);screen.text(store,label,160-Math.floor(width/2),180,0xff000000,font,1);}
function downloadGameFile(data,name){const url=URL.createObjectURL(new Blob([data],{type:'application/octet-stream'})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function chooseGameFile(kind){
  const input=document.createElement('input');input.type='file';input.accept='.dat';input.onchange=async()=>{if(!input.files[0])return;try{
    const data=new Uint8Array(await input.files[0].arrayBuffer());
    if(kind==='songs'){musicEditor.importData(data);status('Both songbooks loaded.');}
    else{const warnings=gameSave.importData(data);closePreferences();setScene('outside');status(warnings.length?'Game loaded. Unsupported values were kept in the file and safely reset for play.':'Game loaded. Choose a friend to begin.');}
  }catch(error){status(error.message);}};input.click();
}
