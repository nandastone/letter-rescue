"use strict";
// Animal-identification rules and original board art, recovered from overlay 2.
class NatureQuiz {
  constructor(nature,{character=()=>"boy",speak=()=>{},stopSound=()=>{},leave=()=>{}}={}){
    this.nature=nature;this.store=nature.store;this.tables=nature.tables;
    this.character=character;this.speak=speak;this.stopSound=stopSound;this.leave=leave;
    this.options=true;this.opponent=2;this.help=[false,false,true];this.tick=0;
    this.cards=[[],[]];this.secret=[0,0];this.remaining=[255,255];this.asked=[0,0];
    this.player=1;this.available=[];this.phase="ready";this.guessing=false;this.selected=-1;
    this.selectedAttribute=-1;this.answer="";this.notice="";this.winner=-1;this.robotDue=null;this.winStage=null;this.winAnimation=null;this.background=new Surface();this.explanation="";
  }
  changed(){this.nature.changed();}
  get busy(){return !!this.task;}
  run(task){this.sampleEnd=null;this.task=task;this.taskDue=this.tick;this.stepTask();this.changed();}
  stepTask(){
    if(!this.task||this.tick<this.taskDue)return false;
    // PCM ends between PIT interrupts. A following countdown starts from the
    // game counter at that instant, not the next browser update's rounded tick.
    const completedAt=this.sampleEnd??this.tick;this.sampleEnd=null;
    const n=this.task.next();
    if(n.done){this.task=null;this.changed();}
    else if(n.value?.audioTicks){this.sampleEnd=this.tick+n.value.audioTicks;this.taskDue=this.sampleEnd;}
    else this.taskDue=Math.floor(completedAt)+Math.max(1,n.value||1);
    return true;
  }
  *perform(index,divider=true){this.scriptIndex=index;const role=this.role(),group=20100+2000*role;this.divider=divider;this.actorScript=new Animation(this.store,role===0?this.character():'th',group+index,group,{startTick:this.tick,onSound:this.speak});while(!this.actorScript.done){this.actorScript.update(this.tick);if(this.questionThreshold&&this.actorScript.frameUpdates>this.questionThreshold){this.questionHidden=this.selectedAttribute;this.questionThreshold=0;}if(!this.actorScript.done)yield 1;}if(divider)this.stopSound();if(index<8)this.answerActor=this.actorScript;this.actorScript=null;this.divider=false;this.scriptIndex=null;}
  resetHint(){this.hintDue=this.tick+300;}
  stopReminder(){if(this.reminding){this.task=null;this.reminding=false;this.reminderHidden=-1;this.hintCard=-1;this.hintControl=false;this.guessHint=false;}this.resetHint();}
  *reminder(explicit=false){this.reminding=true;if(this.phase==='ready'||this.phase==='answered'||this.phase==='won'){if(explicit)this.speak(1017);this.hintControl=true;yield 8;this.hintControl=false;}else if(this.guessing){for(let i=0;i<8;i++)if(this.remaining[this.player]&(1<<i)){this.hintCard=i;this.speak(1050+this.nature.random(6));yield 6;this.hintCard=-1;}}else{for(const i of [...this.available].sort((a,b)=>a-b)){this.reminderHidden=i;yield 18;this.reminderHidden=-1;this.speak(1008);yield 6;}this.guessHint=true;yield 24;this.guessHint=false;}this.reminding=false;this.resetHint();}
  *robotThink(){this.robotSpoken=true;yield this.speak(1011)||1;this.robotDue=this.tick;}
  cleanup(){this.hintDue=this.tick;this.selected=-1;this.visibleQuestions=[];this.questionHidden=-1;this.questionThreshold=0;this.phase='answered';this.guessing=false;this.robotDue=null;this.changed();}
  *enterTurn(){this.visibleQuestions=[];this.displayPlayer=null;this.displayCards=null;while(this.available.length<3){if(this.questionMask===255)this.questionMask=0;let i=this.nature.random(8);while(this.questionMask&(1<<i))i=(i+1)%8;this.questionMask|=1<<i;if(this.available.includes(i))continue;this.available.push(i);yield 30;this.visibleQuestions.push(i);this.speak(1008);}this.visibleQuestions=null;this.resetHint();this.robotDue=this.role()===2||this.remaining[this.player]===(1<<this.secret[this.player])?this.tick+60:null;}
  *enterGuess(){this.selected=-1;this.explanation='';this.speak(10048);this.visibleQuestions=[];yield* this.perform(8);this.guessing=true;this.waiting=true;this.hintDue=this.tick;this.robotDue=this.role()===2||this.remaining[this.player]===(1<<this.secret[this.player])?this.tick+60:null;}
  *question(attribute){const id=this.cards[this.player][this.secret[this.player]],value=this.attributes(id)[attribute];this.speak(10048);this.questionThreshold=[[17,17,17],[11,11,12],[10,9,11],[9,9,10],[13,11,12],[13,13,14],[11,11,12],[11,9,12]][attribute][this.role()];yield* this.perform(attribute);this.answer=this.nature.strings(5200+attribute)[value];this.answerDisplay=true;this.asked[this.player]|=1<<attribute;this.speak(1008);yield 36;if(this.help[this.role()])for(let i=0;i<8;i++)if((this.remaining[this.player]&(1<<i))&&this.attributes(this.cards[this.player][i])[attribute]!==value){yield* this.changeCandidate(i,false);yield 18;}yield 60;this.cleanup();this.notice=`${this.playerName()}: ${this.answer}. Roll for the next turn.`;}
  *wrongGuess(index){this.selected=-1;yield* this.perform(11,false);if(this.help[this.role()])yield* this.changeCandidate(index,false);this.speak(10048);yield* this.perform(9);this.waiting=false;yield 60;this.cleanup();this.notice="That wasn't the secret animal. Roll for the next turn.";}
  *revealOther(player){this.displayPlayer=this.player;this.player=player;if(!(this.revealed&(1<<player))){this.winStage='other-shrub';this.otherReveal=player;this.winAnimation=new Animation(this.store,'modules',5600+player,5600,{startTick:this.tick,onSound:this.speak});while(!this.winAnimation.done){this.winAnimation.update(this.tick);yield 1;}this.revealed|=1<<player;this.winPhase=1;this.winAnimation=null;this.otherReveal=null;}this.winStage='done';this.displayPlayer=null;this.selected=-1;this.explanation='';this.changed();}
  inspectWinner(player){this.stopReminder();if(this.winner<0||this.busy||this.winAnimation&&!this.winAnimation.done)return;this.run(this.revealOther(player));}
  drawTurnActor(surface){if(this.answerDisplay&&this.answerActor){this.answerActor.draw(surface);return;}const role=this.role(),archive=role===0?this.character():'th',group=20100+2000*role,key=archive+':'+group;if(this.turnActorKey!==key){this.turnActorKey=key;this.turnActor=new Animation(this.store,archive,group,group);while(!this.turnActor.frameUpdates)this.turnActor.step(0);this.turnActor.done=true;}this.turnActor.draw(surface);}
  names(){return this.nature.strings(5300).slice(0,8);}
  role(){return this.player===0?0:this.opponent;}
  playerName(){return this.player===0?"You":this.opponent===2?"The robot":"Your friend";}
  attributes(id){const a=this.tables.animals[id];return[...a.attributes,a.active_time];}
  start(){
    this.stopReminder();this.robotSpoken=false;    this.task=null;this.candidateWait=false;this.leadWait=false;this.actorScript=null;this.displayPlayer=null;this.displayCards=null;this.answerDisplay=false;this.visibleQuestions=null;this.waiting=false;this.revealed=0;this.winPhase=0;this.questionHidden=-1;this.cards=[[],[]];this.remaining=[255,255];this.asked=[0,0];this.winner=-1;this.options=false;this.winStage=null;this.winAnimation=null;this.explanation="";
    for(let player=0;player<2;player++){
      const seen=new Set();while(this.cards[player].length<8){const id=this.nature.random(92),key=this.attributes(id).join(',');if(seen.has(key))continue;seen.add(key);this.cards[player].push(id);}
      this.secret[player]=this.nature.random(8);
    }
    this.player=this.nature.random(2);if(this.opponent===2)this.player=1;this.phase="ready";this.available=[];this.selected=-1;this.selectedAttribute=-1;this.answer="";this.notice="Roll the die to begin.";this.guessing=false;this.robotDue=null;this.changed();
  }
  roll(){this.stopReminder();
    if(this.busy||this.options)return false;if(this.phase==="question")return this.reject();
    this.run(this.beginTurn());return true;
  }
  *beginTurn(){
    this.leadWait=true;this.hintControl=true;this.speak(1017);yield 8;this.hintControl=false;yield 60;this.leadWait=false;if(this.winner>=0){this.award?.();return;}
    this.displayPlayer=this.player;this.displayCards=this.phase!=='ready';this.player=1-this.player;this.answerDisplay=false;this.selected=-1;this.selectedAttribute=-1;this.answer="";this.guessing=false;this.explanation="";
    this.questionMask=this.asked[this.player];this.available=[];
    this.phase="question";this.notice=`${this.playerName()}: choose a question or make a guess.`;
    this.robotDue=null;yield* this.enterTurn();
  }
  ask(attribute){this.stopReminder();if(this.busy||this.guessing||this.phase!=='question'||!this.available.includes(attribute))return false;this.selected=-1;this.selectedAttribute=attribute;this.explanation='';this.robotDue=null;this.run(this.question(attribute));return true;}
  toggleGuess(){this.stopReminder();if(this.busy||this.options)return;if(this.phase!=='question'||this.guessing||this.role()===2)return this.reject();this.notice='Choose the animal you think is the secret animal.';this.run(this.enterGuess());}
  choose(index){this.stopReminder();
    if(this.busy||this.options||!this.cards[this.player].length)return;if(this.phase==="ready")return this.reject();
    if(this.guessing){this.guess(index);return;}
    this.selected=index;this.explanation="";this.selectedAttribute=-1;const id=this.cards[this.player][index];this.notice=this.nature.name(id);this.changed();
  }
  guess(index){this.stopReminder();
    if(this.busy||this.phase!=="question")return false;if(!(this.remaining[this.player]&(1<<index)))return this.reject();
    this.selected=-1;this.guessing=false;this.visibleQuestions=[];
    if(index===this.secret[this.player]){this.winner=this.player;this.phase="won";this.notice=`${this.playerName()} found the secret animal: ${this.nature.name(this.cards[this.player][index])}!`;this.robotDue=null;
      this.revealed=1<<this.player;this.winPhase=2;this.speak(1005);this.winStage="shrub";this.winAnimation=new Animation(this.store,"modules",5600+this.player,5600,{startTick:this.tick,onSound:this.speak});this.winAnimation.update(this.tick);}
    else{this.run(this.wrongGuess(index));}
    this.changed();return this.winner===this.player;
  }
  *changeCandidate(index,keep){if(keep)this.remaining[this.player]|=1<<index;else this.remaining[this.player]&=~(1<<index);const duration=this.speak(1006,keep?16537:8269,{fractional:true});this.changed();if(duration){this.candidateWait=true;yield {audioTicks:duration};}this.candidateWait=false;this.stopSound();}
  interruptWait(){if(!this.candidateWait&&!this.leadWait)return false;if(this.candidateWait){this.stopSound();this.sampleEnd=this.tick;}this.taskDue=this.tick;this.stepTask();return true;}
  reject(){if(!this.busy&&!this.options)this.run(this.reminder(true));return false;}
  crossOut(index){this.stopReminder();if(this.interruptWait()||this.busy||this.options||this.winner>=0)return;if(this.phase==="ready"||this.role()===2||this.help[this.role()])return this.reject();this.run((function*(){yield* this.changeCandidate(index,!(this.remaining[this.player]&(1<<index)));if(this.phase==="question"&&this.remaining[this.player]===(1<<this.secret[this.player]))this.robotDue=this.tick+60;}).call(this));}
  inspectAttribute(index){this.stopReminder();if(this.busy||this.explanation&&this.selectedAttribute===index)return;this.selected=-1;this.selectedAttribute=index;this.speak(1008);this.explanation=this.nature.strings(5310)[index];this.changed();}
  update(tick){this.tick=tick;if(this.stepTask()){
    // Overlay 391D clears the reminder timer after answer cleanup. The main
    // loop immediately flashes the die for eight ticks (3C9F -> 3E27).
    if(!this.busy&&!this.options&&this.phase==='answered'&&tick>=this.hintDue)this.run(this.reminder());
    return true;
  }if(this.busy)return false;
    if(this.winAnimation&&!this.winAnimation.done){this.winAnimation.update(tick);if(this.winAnimation.done){
      if(this.winStage==="shrub"||this.winStage==="celebrate"){const celebrate=this.winStage==="shrub";this.waiting=false;this.winStage=celebrate?"celebrate":"retreat";const role=this.role(),group=20100+2000*role;this.winAnimation=new Animation(this.store,role===0?this.character():"th",group+(celebrate?10:9),group,{startTick:tick,onSound:this.speak});this.winAnimation.update(tick);}
      else{this.stopSound();this.winStage='cleanup';this.run((function*(){yield 60;this.winStage='done';}).call(this));}
      this.changed();}return true;}
    if(this.robotDue===null){if(!this.options&&tick>=this.hintDue&&(!this.winAnimation||this.winAnimation.done)){this.run(this.reminder());return true;}return false;}if(tick<this.robotDue)return false;this.robotDue=null;
    if(this.phase!=="question")return false;
    if(this.role()===2&&!this.robotSpoken){this.run(this.robotThink());return true;}this.robotSpoken=false;
    const remaining=Array.from({length:8},(_,i)=>i).filter(i=>this.remaining[this.player]&(1<<i));
    if(this.remaining[this.player]===(1<<this.secret[this.player])||this.guessing||!this.available.length){if(!this.guessing)this.run(this.enterGuess());else this.guess(this.secret[this.player]);}
    else{let attribute;do{attribute=this.nature.random(8);}while(!this.available.includes(attribute));this.ask(attribute);}return true;
  }
  click(x,y){if(this.interruptWait())return;this.stopReminder();if(this.busy||this.winAnimation&&!this.winAnimation.done)return;const hit=b=>this.nature.hit(b,x,y),r=this.tables.quiz_rectangles,o=this.tables.quiz_options;
    if(this.options){if(hit(o[1])){this.leave();return;}if(hit(o[3]))this.opponent=1;else if(hit(o[4]))this.opponent=2;else if(hit(o[5]))this.help[0]=!this.help[0];else if(hit(o[6])&&this.opponent===1)this.help[1]=!this.help[1];else if(hit(o[10])){this.start();return;}this.changed();return;}
    if(hit(r[38])){if(this.selected>=0||this.explanation){this.selected=-1;this.selectedAttribute=-1;this.explanation='';this.changed();}else this.reject();return;}
    if(this.winner>=0){const shrub=this.tables.reveal_rectangles.findIndex(b=>hit(b));if(shrub>=0){this.inspectWinner(shrub);return;}}
    if(hit(r[9])){this.leave();return;}if(hit(r[11])){this.options=true;this.robotDue=null;this.changed();return;}
    for(let i=0;i<8;i++){if(hit(r[1+i])){this.inspectAttribute(i);return;}if(hit(r[12+i])){if(this.role()!==2)this.ask(i);return;}
      if(hit(r[20+i])){if(this.role()!==2||this.phase==='won')this.choose(i);return;}if(hit(r[28+i])){this.crossOut(i);return;}}
    if(hit(r[36])){this.roll();}else if(hit(r[37]))this.toggleGuess();
  }
  draw(surface){
    const shown=this.displayPlayer??this.player,s=this.store,r=this.tables.quiz_rectangles,ui=s.palette("modules",5650).rgba;
    const draw=(id,pal,x,y,mode=10,archive="modules")=>surface.draw(s,archive,id,pal,x,y,mode);
    const fill=(b,color)=>surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],color);
    const center=(id,b,pal=5650,color=null,archive="modules")=>{if(color!==null)fill(b,color);const shape=s.shape(archive,id);draw(id,pal,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),Math.floor((b[0]+b[2])/2)-Math.floor(shape.h/2),10,archive);};
    const width=text=>[...text].reduce((n,c)=>n+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);
    const text=(value,x,y)=>surface.text(s,value,x,y);
    draw(5402,5400,0,0,2);
    for(let i=0;i<8;i++)center(5651+i,r[1+i],5650,ui[2]);
    draw(5609,5600,171,3);
    for(let i=0;i<2;i++){if(this.phase==='won'&&(((this.revealed??(1<<this.winner))&(1<<i))||i===this.otherReveal))continue;const b=this.tables.reveal_rectangles[i];draw(5601,5600,b[1]+1,b[0]);}
    if(this.phase==="won"){
      if(this.winStage==='other-shrub')this.winAnimation.draw(surface);
      if(this.winStage==="shrub"){this.winAnimation.draw(surface);const role=this.role(),archive=role===0?this.character():'th',group=20100+2000*role,[x,y]=role===0?[238,this.character()==='girl'?112:115]:role===1?[231,139]:[229,137];draw(group+(role===2?2:1),group,x,y,10,archive);}
      else{
        // Original restores the saved guess-animation rectangle after SCR5600.
        const role=this.winner===0?0:this.opponent,restore=this.tables.guess_restore_rectangles[role===0&&this.character()==="girl"?3:role];this.background.pixels.set(surface.pixels);
        const b=this.tables.reveal_rectangles[this.winner];draw(5608,5600,b[1]+1,b[0]+26);
        for(let y=restore[0];y<restore[2];y++)for(let x=restore[1];x<restore[3];x++)surface.pixels[y*320+x]=this.background.pixels[y*320+x];
        const a=this.tables.animals[this.cards[this.winner][this.secret[this.winner]]],shape=s.shape("modules",a.large);draw(a.large,a.palette,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),b[0]);
      }
    }
    if(this.phase==='won'&&this.revealed===3){const player=1-this.winner,b=this.tables.reveal_rectangles[player],a=this.tables.animals[this.cards[player][this.secret[player]]],shape=s.shape('modules',a.large);draw(5608,5600,b[1]+1,b[0]+26);draw(a.large,a.palette,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),b[0]);}
    draw(5665,5650,284,1);draw(5664,5650,265,1);draw(8,6,304,1,10,"th");
    if(this.phase==="ready"||this.phase==="answered"){draw(5669,5650,137,8,2);center(this.hintControl?5668:5667,[12,141,29,158],5650,0xffffffff);}
    if(this.phase!=="ready"&&!this.options){
      if(this.displayCards!==false)for(let i=0;i<8;i++){const a=this.tables.animals[this.cards[shown][i]];center(a.small,r[20+i],a.palette,this.hintCard===i?0xff5555ff:(this.remaining[shown]&(1<<i))?0xffffffff:0xffaaaaaa);center((this.remaining[shown]&(1<<i))?5662:5663,r[28+i],5650,s.palette("modules",5400).rgba[6]);}
      for(const i of this.visibleQuestions??this.available){if(i===this.reminderHidden)continue;const n=this.tables.question_shapes[i],b=r[12+i];if(n){fill(b,0xffffffff);draw(5600+n,5600,b[1],b[0]);}const[y,x]=this.tables.question_positions[i];if(i!==this.questionHidden)draw(5651+i,5650,x,y);}
      if(this.phase==="question"){
        this.drawTurnActor(surface);
        if(!this.busy||this.reminding||this.robotSpoken||this.scriptIndex===8){draw(5669,5650,137,82,2);center(5666,[86,141,103,158],5650,this.guessHint||this.guessing||this.waiting||this.scriptIndex===8?0xff5555ff:0xffffffff);}
      }
      for(let i=0;i<8;i++)if((this.phase==='won'&&this.winStage!=='shrub')||this.asked[shown]&(1<<i))text(this.nature.strings(5200+i)[this.attributes(this.cards[shown][this.secret[shown]])[i]],30,7+14*i);
      if(this.selected>=0){
        const id=this.cards[shown][this.selected],a=this.tables.animals[id],font=s.data.heading_font;
        fill(r[38],0xffffffff);const heading=this.nature.strings(5208+a.active_time)[a.category];
        const headingWidth=[...heading].reduce((n,c)=>n+(font[c.charCodeAt(0)]?.[0]||3)+1,0);
        surface.text(s,heading,79-Math.floor(headingWidth/2),7,0xff000000,font,1);
        const name=this.nature.name(id);text(name,79-Math.floor(width(name)/2),21);center(a.large,[30,30,77,128],a.palette);
        [...this.available].sort((a,b)=>a-b).forEach((attribute,row)=>{const value=this.nature.strings(5200+attribute)[this.attributes(id)[attribute]];text(value,79-Math.floor(width(value)/2),77+14*row);});
      }
      if((this.phase==="answered"||this.answerDisplay)&&this.answer){const x=86-Math.floor(width(this.answer)/2);text(this.answer,x,126);draw(5662,5650,x-12,125);}
      if(this.phase==="won"&&this.winStage!=="shrub"){
        if(['cleanup','done','other-shrub'].includes(this.winStage)){draw(5669,5650,137,8,2);center(922,[12,141,29,158],900,this.hintControl?0xff5555ff:0xffffffff,'th');}
        if(this.selected<0&&!this.explanation){const name=this.nature.name(this.cards[shown][this.secret[shown]]);text(name,86-Math.floor(width(name)/2),126);}
        if(this.winStage==='celebrate'||this.winStage==='retreat'){if(this.winStage==='retreat')fill([42,134,80,167],0xffffffff);this.winAnimation.draw(surface);if(this.winStage==='retreat')draw(5403,5400,166,41);}
      }
    }
      if(this.explanation&&!this.options){
        fill(r[38],0xffffffff);center(5651+this.selectedAttribute,r[1+this.selectedAttribute],5650,ui[8]);
        const heading=this.names()[this.selectedAttribute];text(heading,79-Math.floor(width(heading)/2),6);
        let line="",y=17;for(const word of this.explanation.split(" ")){const trial=line?line+" "+word:word;if(width(trial)>98){surface.text(s,line,30,y,0xff000000,s.data.font,0,[17,30,116,128]);y+=10;line=word;}else line=trial;}surface.text(s,line,30,y,0xff000000,s.data.font,0,[17,30,116,128]);
      }
    if(this.actorScript){if(this.divider)fill([42,134,80,167],0xffffffff);this.actorScript.draw(surface);if(this.divider)draw(5403,5400,166,41);}
    if(this.waiting&&!this.actorScript&&this.phase!=='won'){const role=this.role(),archive=role===0?this.character():'th',group=20100+2000*role,[x,y]=role===0?[238,this.character()==='girl'?112:115]:role===1?[231,139]:[229,137];fill([42,134,80,167],0xffffffff);draw(group+(role===2?2:1),group,x,y,10,archive);}
    if(this.options){
      const o=this.tables.quiz_options,bg=0xffc3ebff;
      draw(5404,5400,6,3,2);draw(5405,5400,34,49,2);
      center(this.opponent===2?24202:22201,o[2],this.opponent===2?24200:22200,bg,"th");
      center(20201,o[7],20200,bg,this.character());
      if(this.opponent===1){draw(5405,5400,34,67,2);center(22201,o[8],22200,bg,"th");}
      for(const [enabled,index]of [[this.opponent===1,3],[this.opponent===2,4],[this.help[0],5],[this.opponent===1&&this.help[1],6]])if(enabled)surface.blit(s.shape("th",9),new Uint32Array(256).fill(0xff5555ff),o[index][1],o[index][0],10);
    }
  }
}
