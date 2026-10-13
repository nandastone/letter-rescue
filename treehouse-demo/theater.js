"use strict";
// Theater data and control flow recovered from DOS v1.1 overlay 4.
// This class owns the activity state; the app supplies readable controls/audio.
class TheaterActivity {
  constructor(store,{speak=()=>0,stopSound=()=>{},changed=()=>{},announce=()=>{}}={}) {
    this.store=store;this.tables=store.data.theater;
    this.speak=speak;this.stopSound=stopSound;this.changed=changed;this.announce=announce;
    this.selection=[-1,-1,-1,-1];this.order=[0,1,2,3];this.category=-1;
    this.options=true;this.mixUp=false;this.propsEnabled=false;
    this.tick=0;this.preview=null;this.actorAnimation=null;this.playing=false;
    this.sequence=[];this.waitUntil=0;this.presenting=-1;this.weatherStart=null;
    this.drag=null;this.actorDrag=Array.from({length:7},()=>[0,0]);
    this.props=Array.from({length:6},()=>[]);this.performances=0;
    this.curtain=3;this.curtainStart=null;this.director=0;this.phase="idle";
    this.presentation=null;this.presentationDue=0;this.stageSelection=null;this.exitReady=false;
    this.validPlay=true;this.phaseStart=0;this.actorTail=0;this.feedback=0;this.previousValidation=0;this.tokenSequence=null;this.tokenSprite=null;this.tokenDue=0;this.correctNoticeUntil=null;this.textSurface=new Surface();
    this.restore();
  }
  savedState(){return {version:1,mixUp:this.mixUp,propsEnabled:this.propsEnabled,selection:this.selection.slice(),order:this.order.slice(),actorDrag:this.actorDrag.map(p=>p.slice()),props:this.props.map(list=>list.map(p=>({...p}))),previousValidation:this.previousValidation};}
  save(){try{localStorage.setItem('treehouse-theater-v1',JSON.stringify(this.savedState()));}catch(_error){this.announce('Your play is ready. This browser could not save it after closing.');}}
  restore(){try{const value=JSON.parse(localStorage.getItem('treehouse-theater-v1'));if(!value||value.version!==1)return;const ints=(a,n,min,max)=>Array.isArray(a)&&a.length===n&&a.every(v=>Number.isInteger(v)&&v>=min&&v<=max);if(typeof value.mixUp!=='boolean'||typeof value.propsEnabled!=='boolean'||!ints(value.selection,4,-1,100)||value.selection.some((v,c)=>v>=this.choices(c).length)||!ints(value.order,4,0,3)||new Set(value.order).size!==4||!Array.isArray(value.actorDrag)||value.actorDrag.length!==7||!value.actorDrag.every(p=>ints(p,2,-320,320))||!Array.isArray(value.props)||value.props.length!==6||!Number.isInteger(value.previousValidation)||value.previousValidation<0||value.previousValidation>6)return;
      for(let place=0;place<6;place++){const list=value.props[place],palette=this.tables.prop_group[place]?3175:3145,first=palette+this.tables.prop_first[place];if(!Array.isArray(list)||list.length>20||list.some(p=>!p||!Number.isInteger(p.id)||p.id<first||p.id>=first+this.tables.prop_count[place]||p.palette!==palette||!Number.isInteger(p.x)||!Number.isInteger(p.y)||p.x<0||p.x>=320||p.y<0||p.y>=200))return;}
      for(const key of ['mixUp','propsEnabled','selection','order','actorDrag','props','previousValidation'])this[key]=value[key];
    }catch(_error){}}
  choices(category) {
    if(category===4){const p=Math.max(0,this.selection[2]),count=this.tables.prop_count[p];return Array.from({length:count},(_,i)=>`Decoration ${i+1}`);}
    return this.store.data.strings[`modules:${3000+10*category}`].map(s=>s.trim());
  }
  runPresentation(sequence){this.presentation=sequence;this.presentationDue=this.tick;this.update(this.tick);this.changed();}
  *moveCurtain(open){
    this.curtainMoving=true;this.speak(10032);
    for(const stage of open?[1,2,3]:[2,1,0]){this.curtain=stage;yield 8;}
    this.stopSound(10032);this.curtainMoving=false;
  }
  *curtainChange(change){yield* this.moveCurtain(false);change();yield* this.moveCurtain(true);}
  enter(){this.curtain=0;this.runPresentation(this.moveCurtain(true));}
  leave(done){if(this.presentation?.leaving)return;this.stop();const self=this;const sequence=(function*(){yield* self.moveCurtain(false);self.exitReady=true;done();})();sequence.leaving=true;this.runPresentation(sequence);}
  setOption(name,value){if(this[name]!==value){this[name]=value;this.speak(1008);}this.changed();}
  *openEditor(clickTicks){if(clickTicks>0)yield clickTicks;yield* this.curtainChange(()=>{this.stageOptions=false;});this.stageOptions=null;this.openingEditor=false;}
  start() {const clickTicks=this.speak(1008);this.stageOptions=this.options;this.openingEditor=true;this.options=false;this.category=-1;this.runPresentation(this.openEditor(clickTicks));this.save();this.changed();}
  showChoices(category,feedback=true) {
    if(this.options||this.playing)return;
    if(category===4&&(!this.propsEnabled||this.selection[2]<0)){this.announce("Choose a place before adding decorations.");return;}
    if(feedback)this.speak(1008);
    if(!this.feedback)this.director=0;this.feedback=0;this.successFeedback=false;this.previewCategory=-1;this.presenting=-1;this.category=category;this.changed();
  }
  choose(category,index,{fromNotebook=false}={}) {
    if(this.options)this.start();
    const previous=this.selection.slice();
    this.stop();this.feedback=0;this.successFeedback=false;this.category=category;
    if(category===4){this.addProp(index);return;}
    if(index< -1 || index>=this.choices(category).length)throw new Error("Invalid theater choice");
    this.selection[category]=index;
    if(category===0)this.actorDrag=Array.from({length:7},()=>[0,0]);
    if(index>=0&&index!==previous[category]){this.stageSelection=previous;this.runPresentation(this.presentChoice(category,previous,fromNotebook));}
    this.changed();
  }
  *presentChoice(category,previous,fromNotebook){
    // Overlay 404C: a new Mix Up token travels from the notebook to its rail.
    if(this.mixUp&&previous[category]<0&&!fromNotebook){
      const a=this.tables.ui_rects[8+category],b=this.tables.ui_rects[23+this.order.indexOf(category)];
      const x=Math.floor((a[1]+a[3])/2)-10,y=Math.floor((a[0]+a[2])/2)-10;
      yield* this.travelToken(category,[x,y],[b[1],b[0]]);
    }
    if(category>=2)yield* this.curtainChange(()=>{this.stageSelection=null;});
    else this.stageSelection=null;
    this.previewPart(category);
  }
  phrase(category,selection=this.selection) {return selection[category]>=0?this.choices(category)[selection[category]]:"";}
  sentence(selection=this.selection) {
    let sentence=(this.stageOrder||this.order).map(c=>this.phrase(c,selection)).filter(Boolean).join(" ");
    if(selection[0]>=0&&selection[1]>=0&&sentence)sentence=sentence[0].toUpperCase()+sentence.slice(1)+".";
    return sentence;
  }
  validation() {
    if(this.selection[0]<0&&this.selection[1]<0)return 2;
    if(this.selection[0]<0)return 3;if(this.selection[1]<0)return 4;
    const present=this.order.filter(c=>this.selection[c]>=0),subject=present.indexOf(0),action=present.indexOf(1);
    if(subject>action)return 5;if(action!==subject+1)return 6;return 0;
  }
  movePart(category,direction) {
    if(!this.mixUp||this.playing)return;
    const index=this.order.indexOf(category),target=index+direction;if(target<0||target>3)return;
    [this.order[index],this.order[target]]=[this.order[target],this.order[index]];this.changed();
  }
  correctedOrder(code=this.validation()) {
    const result=[...this.order],subject=result.indexOf(0),action=result.indexOf(1),swap=(a,b)=>{[result[a],result[b]]=[result[b],result[a]];};
    if(action>0&&this.selection[result[action-1]]<0)swap(action-1,subject);
    else if(subject<3&&this.selection[result[subject+1]]<0)swap(subject+1,action);
    else if(code===5){for(let i=action;i<subject;i++)result[i]=result[i+1];result[subject]=1;}
    else if(code===6){for(let i=action;i>subject+1;i--)result[i]=result[i-1];result[subject+1]=1;}
    return result;
  }
  correct() {
    if(!this.mixUp||this.playing||this.tokenSequence)return;
    const code=this.validation();this.previousValidation=code;
    if(code===0){this.correctNoticeUntil=this.tick+120;this.changed();return;}
    if(code<5){this.feedback=code;this.category=-1;}
    else{this.order=this.correctedOrder(code);this.feedback=0;this.previousValidation=0;}
    this.changed();
  }
  *moveToken(category,from,to){
    if(this.selection[category]<0)return;
    const a=this.tables.ui_rects[23+from],b=this.tables.ui_rects[23+to];yield* this.travelToken(category,[a[1],a[0]],[b[1],b[0]]);
  }
  *travelToken(category,from,to){
    // Resident 6DA9 publishes every eight Manhattan steps, then waits four ticks.
    let [x,y]=from;const [tx,ty]=to,dx=Math.abs(tx-x),dy=Math.abs(ty-y),sx=Math.sign(tx-x),sy=Math.sign(ty-y);
    let error=dx?Math.floor(dx/2):-1,step=0;this.speak(10035);
    while(true){const end=x===tx&&y===ty;
      if(end||step%8===0){this.tokenSprite={category,x,y};yield 4;}
      if(end)break;if(error>=0){x+=sx;error-=dy;}else{y+=sy;error+=dx;}step++;
    }
    this.tokenSprite=null;
  }
  *swapTokens(from,to,dragged=false){
    const a=this.order[from],b=this.order[to];
    // Overlay 0F88..1004 and 3F44..3FD8 repaint the sentence after both tokens.
    this.stageOrder=[...this.order];
    if(!dragged)yield* this.moveToken(a,from,to);
    [this.order[from],this.order[to]]=[b,a];yield* this.moveToken(b,to,from);this.stageOrder=null;this.changed();
  }
  *shuffleTokens(){
    this.feedback=0;for(let i=0;i<5;i++){const a=gameplayRandom.pick(4);let b;do{b=gameplayRandom.pick(4);}while(a===b);yield* this.swapTokens(a,b);}
    this.previousValidation=this.validation();
  }
  shuffle(){if(!this.mixUp||this.playing||this.tokenSequence)return;this.tokenSequence=this.shuffleTokens();this.tokenDue=this.tick;this.update(this.tick);}
  makeAnimation(id,palette,origin=null) {
    const a=new Animation(this.store,"modules",id,palette,{startTick:this.tick,origin});a.update(this.tick);return a;
  }
  previewPart(category){
    const choice=this.selection[category];if(choice<0)return;
    const duration=this.speak(3000+10*category+choice);this.previewCategory=category;this.previewUntil=this.tick+Math.max(60,12+24*Math.ceil(Math.max(0,duration-12)/24));this.phaseStart=this.tick;this.presenting=category;
    if(category===1)this.preview=this.makeAnimation(3050+choice,3050);
    if(category===3){this.previewBlinkUntil=this.previewUntil;this.previewUntil+=20;}
  }
  translation() {
    const selected=this.stageSelection||this.selection,actor=selected[0],place=selected[2],base=this.tables.actor_origins_by_place[place+1][actor],drag=this.actorDrag[place+1];
    return[base[0]+drag[0],base[1]+drag[1]];
  }
  actorRect() {
    const actor=(this.stageSelection||this.selection)[0];if(actor<0)return null;
    const b=this.tables.actor_bounds[actor],offset=this.translation();
    return[b[0]+offset[0],b[1]+offset[1],b[2]+offset[0],b[3]+offset[1]];
  }
  play() {
    if(this.tokenSequence)return false;
    const code=this.validation();
    const previous=this.previousValidation;this.stop();this.previousValidation=code;this.successFeedback=!!previous&&code===0;this.feedback=this.successFeedback?(previous===3||previous===4?1:0):0;if(this.successFeedback)this.category=-1;this.validPlay=code===0;this.playing=true;this.sequence=this.order.filter(c=>this.selection[c]>=0);
    this.phase="clap";this.director=1;this.waitUntil=this.tick+16;this.speak(1009);this.changed();return this.validPlay;
  }
  presentNext() {
    if(!this.sequence.length){this.presenting=-1;this.weatherStart=null;this.phase=this.validPlay?"tail":"invalid";this.waitUntil=this.validPlay?Math.max(this.tick,this.actorTail):this.tick+30;this.director=this.validPlay?2:3;if(this.validPlay&&this.waitUntil<=this.tick)this.finish();return;}
    const category=this.sequence.shift(),choice=this.selection[category];this.presenting=category;
    this.phase="phrase";this.phaseStart=this.tick;const duration=this.speak(3000+category*10+choice);
    this.waitUntil=this.tick+duration;
    if(this.validPlay&&(category===0||category===2))this.waitUntil=this.tick+Math.max(60,12+24*Math.ceil(Math.max(0,duration-12)/24));
    if(this.validPlay&&category===1){const group=3200+100*this.selection[0],id=group+choice,b=this.store.data.scripts[`modules:${id}`].bounds,t=this.translation();this.actorAnimation=this.makeAnimation(id,group,[b[1]+t[1],b[0]+t[0]]);}
    if(category===3){if(this.validPlay){this.weatherStart=this.tick;const row=this.tables.time_shapes[choice];this.waitUntil=Math.max(this.waitUntil,this.tick+(row[2]-1)*row[3]);}this.waitUntil+=20;}
    this.changed();
  }
  stop() {this.playing=false;this.sequence=[];this.presenting=-1;this.previewCategory=-1;this.actorAnimation=null;this.weatherStart=null;this.preview=null;this.tokenSequence=null;this.tokenSprite=null;this.stageOrder=null;this.phase="idle";this.director=0;this.actorTail=0;this.presentation=null;this.stageSelection=null;this.stageOptions=null;this.openingEditor=false;this.curtainMoving=false;this.curtain=3;this.exitReady=false;}
  get busyCursor(){return this.curtainMoving||this.playing&&this.weatherStart!==null;}
  // Both actor playback (2765) and the small preview (1F0C) use the resident
  // SCR wrapper, which hides the cursor until script cleanup completes.
  get hideCursor(){return [this.actorAnimation,this.preview].some(a=>a&&!a.done);}
  finish(){
    this.playing=false;this.actorAnimation=null;this.phase="idle";this.performances++;
    if(this.validPlay){this.director=0;this.announce("The end! Change a word and put on another show.");}
    else{this.feedback=this.validation();this.category=-1;this.speak(1030);this.announce({2:"Choose who and what they do to make a sentence.",3:"Choose who or what does the action.",4:"Choose what your actor does.",5:"Put who or what before the action.",6:"Keep who or what right next to the action."}[this.feedback]);}
    this.changed();
  }
  update(tick) {
    this.tick=tick;let changed=false;
    if(this.presentation&&tick>=this.presentationDue){const sequence=this.presentation,next=sequence.next();if(this.presentation===sequence){if(next.done)this.presentation=null;else this.presentationDue=tick+next.value;}changed=true;}
    if(this.previewCategory>=0){changed=true;if(tick>=this.previewUntil){this.previewCategory=-1;this.presenting=-1;}}
    if(this.correctNoticeUntil!==null&&tick>=this.correctNoticeUntil){this.correctNoticeUntil=null;changed=true;}
    if(this.drag?.type==='token'&&!this.drag.active&&tick-this.drag.since>=15){this.drag.active=true;this.moveDrag(...this.drag.pointer);changed=true;}
    if(this.tokenSequence&&tick>=this.tokenDue){const next=this.tokenSequence.next();if(next.done){this.tokenSequence=null;this.tokenSprite=null;this.changed();}else this.tokenDue=tick+next.value;changed=true;}
    for(const a of [this.actorAnimation,this.preview])if(a&&!a.done){a.update(tick);changed=true;}
    if(this.curtainStart!==null){const stage=Math.min(3,Math.floor((tick-this.curtainStart)/8));this.curtain=stage;if(stage===3)this.curtainStart=null;changed=true;}
    if(this.weatherStart!==null){const time=this.selection[3],row=this.tables.time_shapes[time];if(tick-this.weatherStart>=(row[2]-1)*row[3])this.weatherStart=null;changed=true;}
    if(this.playing){changed=true;
      if(tick>=this.waitUntil){
        if(this.phase==="clap"){this.phase="pause";this.director=0;this.waitUntil=tick+32;}
        else if(this.phase==="pause"){this.director=this.validPlay?2:0;this.presentNext();}
        else if(this.phase==="phrase"&&(!this.actorAnimation||this.actorAnimation.done)&&this.weatherStart===null){if(this.validPlay&&this.presenting===1)this.actorTail=tick+120;this.presentNext();}
        else if(this.phase==="tail"||this.phase==="invalid")this.finish();
      }
    }
    return changed;
  }
  addProp(index,position=null) {
    const place=this.selection[2];if(place<0){this.announce("Choose a place first.");return;}
    if(this.props[place].length>=20){this.announce("This stage has 20 decorations. Remove one to add another.");return;}
    this.speak(1008);
    const palette=this.tables.prop_group[place]===0?3145:3175,id=palette+this.tables.prop_first[place]+index;
    const shape=this.store.shape("modules",id),p={id,palette,x:position?Math.floor(position[0])-Math.floor(shape.w/2):160,y:position?Math.floor(position[1])-Math.floor(shape.h/2):115};
    this.props[place].push(p);this.changed();return p;
  }
  removeLastProp() {if(this.selection[2]>=0)this.props[this.selection[2]].pop();this.changed();}
  hit(rect,x,y){return x>=rect[1]&&x<rect[3]&&y>=rect[0]&&y<rect[2];}
  beginDrag(x,y) {
    if(this.options||this.playing||this.tokenSequence)return false;
    if(this.mixUp){
      for(let i=0;i<4;i++){
        const category=this.order[i],r=this.tables.ui_rects[23+i];
        if(this.selection[category]>=0&&this.hit(r,x,y)){this.showChoices(category,false);this.drag={type:'token',category,from:i,notebook:false,since:this.tick,start:[x,y],pointer:[x,y],origin:[r[1],r[0]],x:r[1],y:r[0],active:false};return true;}
        const b=this.tables.ui_rects[8+i];if(this.selection[i]<0&&this.hit(b,x,y)){this.showChoices(i);const origin=[Math.floor((b[1]+b[3])/2)-10,Math.floor((b[0]+b[2])/2)-10];this.drag={type:'token',category:i,from:this.order.indexOf(i),notebook:true,since:this.tick,start:[x,y],pointer:[x,y],origin,x:origin[0],y:origin[1],active:false};return true;}
      }
    }
    const place=this.selection[2];
    if(place>=0)for(const p of this.props[place]){const s=this.store.shape("modules",p.id);if(x>=p.x&&x<p.x+s.w&&y>=p.y&&y<p.y+s.h){this.drag={type:"prop",item:p,start:[x,y],origin:[p.x,p.y]};return true;}}
    const rect=this.actorRect();if(rect&&this.hit(rect,x,y)){this.drag={type:"actor",start:[x,y],origin:[...this.actorDrag[place+1]],rect,since:this.tick,moved:false};return true;}
    return false;
  }
  moveDrag(x,y) {
    if(!this.drag)return false;const d=this.drag,dx=Math.round(x-d.start[0]),dy=Math.round(y-d.start[1]);
    if(d.type==='token'){d.pointer=[x,y];if(this.tick-d.since<15)return false;d.active=true;if(Math.abs(dx)>2||Math.abs(dy)>2){d.x=Math.max(2,Math.min(297,d.origin[0]+dx));d.y=Math.max(2,Math.min(178,d.origin[1]+dy));}return true;}
    if(d.type==="prop"){const s=this.store.shape("modules",d.item.id);d.item.x=Math.max(0,Math.min(320-s.w,d.origin[0]+dx));d.item.y=Math.max(0,Math.min(200-s.h,d.origin[1]+dy));}
    else {if(this.tick-d.since<15)return false;d.moved||=Math.abs(dx)>=2||Math.abs(dy)>=2;const b=d.rect;this.actorDrag[this.selection[2]+1]=[d.origin[0]+Math.max(74-b[0],Math.min(165-b[2],dy)),d.origin[1]+Math.max(103-b[1],Math.min(261-b[3],dx))];}
    return true;
  }
  endDrag(cancelled=false) {
    const d=this.drag;if(!d)return;this.drag=null;
    if(d.type==='token'){
      if(!cancelled){
        if(!d.active){if(!d.notebook)this.previewPart(d.category);}
        else if(!d.notebook&&d.pointer[0]<67){this.choose(d.category,-1);this.previousValidation=0;}
        else{const target=this.tables.ui_rects.slice(23,27).findIndex(r=>this.hit(r,...d.pointer));if(target>=0){if(d.notebook){[this.order[d.from],this.order[target]]=[this.order[target],this.order[d.from]];this.choose(d.category,gameplayRandom.pick(this.choices(d.category).length),{fromNotebook:true});}else if(target!==d.from){this.tokenSequence=this.swapTokens(d.from,target,true);this.tokenDue=this.tick;this.update(this.tick);}}}
      }
      this.changed();return;
    }
    if(d.type==="actor") {if(!cancelled&&!d.moved)this.speak(3000+this.selection[0]);}
    else {
      const p=d.item,s=this.store.shape("modules",p.id),list=this.props[this.selection[2]],index=list.indexOf(p);
      if(index>=0)list.splice(index,1);
      if(p.x+s.w>103&&p.x<261&&p.y+s.h>53&&p.y<165){p.x=Math.max(103,Math.min(261-s.w,p.x));p.y=Math.max(53,Math.min(165-s.h,p.y));list.push(p);}
      else this.announce("Decoration removed. Choose another from Props.");
    }
    this.changed();
  }
  choiceBounds() {
    if(this.category<0)return[];const count=this.choices(this.category).length;
    if(this.category===0){let x=73;return Array.from({length:8},(_,i)=>{const shape=this.store.shape("modules",3981+i),b=[15,x,42,x+shape.w];x+=shape.w+5;return b;});}
    const width=Math.floor(221/count);return Array.from({length:count},(_,i)=>[15,73+width*i,42,73+width*(i+1)]);
  }
  click(x,y) {
    if(this.options){if(x>=184&&x<192&&y>=81&&y<89)this.setOption('mixUp',!this.mixUp);else if(x>=184&&x<192&&y>=97&&y<105)this.setOption('propsEnabled',!this.propsEnabled);else if(x>=182&&x<241&&y>=130&&y<150)this.start();this.changed();return;}
    if(this.hit(this.tables.ui_rects[1],x,y)){this.stop();this.options=true;this.changed();return;}
    if(this.playing){this.stop();this.changed();return;}
    if(this.tokenSequence)return;
    if(this.mixUp&&this.hit(this.tables.ui_rects[21],x,y)){this.shuffle();return;}
    if(this.mixUp&&this.hit(this.tables.ui_rects[22],x,y)){this.correct();return;}
    for(let c=0;c<4;c++){if(this.hit(this.tables.ui_rects[8+c],x,y)){this.showChoices(c);return;}if(this.hit(this.tables.ui_rects[12+c],x,y)){this.announce(this.store.data.strings["modules:3050"][c]);return;}}
    const choices=this.choiceBounds();for(let i=0;i<choices.length;i++)if(this.hit(choices[i],x,y)){
      if(this.category===4){const p=this.addProp(i,[x,y]);if(p)this.drag={type:"prop",item:p,start:[x,y],origin:[p.x,p.y]};}
      else this.choose(this.category,i);return;}
    if(this.hit(this.tables.ui_rects[7],x,y)){this.play();return;}
    if(this.hit(this.tables.ui_rects[18],x,y)&&this.selection[1]>=0){this.preview=this.makeAnimation(3050+this.selection[1],3050);this.changed();return;}
    if(this.propsEnabled&&x<62&&y>=163&&y<178){this.showChoices(4);return;}
    this.announce("Choose words from the notebook, then click the director to perform your sentence.");
  }
  draw(surface) {
    const s=this.store,t=this.tables;
    const selected=this.stageSelection||this.selection;
    const options=this.stageOptions??this.options;
    const draw=(id,palette,x,y,mode=10)=>surface.draw(s,"modules",id,palette,x,y,mode);
    const mask=(id,x,y,color=0xff000000)=>surface.blit(s.shape("modules",id),new Uint32Array(256).fill(color),x,y,10);
    draw(3041,3040,0,0,2);
    if(!options){
      const place=selected[2],time=selected[3];
      if(place>=0){const id=3100+3*place+(time<0?0:t.time_background_variant[time]);
        if(((this.playing&&this.validPlay&&this.presenting===2)||this.previewCategory===2)&&Math.floor((this.tick-this.phaseStart)/12)%2===0){
          const palette=s.palette("modules",id);if(!palette.bright)palette.bright=Uint32Array.from(palette.colors,([r,g,b],i)=>{
            const bright=c=>{const n=Math.min(63,Math.round(c*63/255)+6);return(n<<2)|(n>>4);};
            return i?(0xff000000|bright(b)<<16|bright(g)<<8|bright(r))>>>0:palette.rgba[0];});
          surface.blit(s.shape("modules",3101+3*place),palette.bright,96,51,10);
        }else draw(3101+3*place,id,96,51,10);}
      if(time>=0){const row=t.time_shapes[time],pos=t.time_positions_by_place[Math.max(0,place)][time];let frame=0;
        if(this.weatherStart!==null)frame=1+Math.floor((this.tick-this.weatherStart)/row[3]);if(!(this.previewCategory===3&&this.tick<this.previewBlinkUntil&&Math.floor((this.tick-this.phaseStart)/12)%2===0))draw(3120+row[1]+frame,3120,pos[1],pos[0]);}
      if(place>=0)for(const p of this.props[place])draw(p.id,p.palette,p.x,p.y);
      const hidden=((this.playing&&this.validPlay&&this.presenting===0)||this.previewCategory===0)&&Math.floor((this.tick-this.phaseStart)/12)%2===0;
      if(!hidden){if(this.actorAnimation)this.actorAnimation.draw(surface);
        else if(selected[0]>=0){const a=selected[0],b=this.actorRect(),off=t.actor_shape_offsets[a];draw(3201+100*a,3200+100*a,b[1]+off[1],b[0]+off[0]);}}
    }
    const curtain=t.curtain_shapes[this.curtain],pos=t.curtain_positions[this.curtain];
    draw(3040+curtain[0],3040,pos[1],pos[0]);if(curtain[1])draw(3040+curtain[1],3040,pos[3],pos[2]);
    draw(3049,3040,259,73);
    for(let c=0;c<4;c++)draw(3003+c+(this.mixUp&&this.selection[c]>=0?4:0),3000,27,30+32*c);
    for(const[id,x,y]of [[3014,20,181],[3015,39,180],[3016,299,24],[3022,304,1],[3023,1,181]])draw(id,3000,x,y);
    if(this.category>=0&&this.category<4){const b=t.ui_rects[12+this.category];surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],s.palette("modules",3000).rgba[[6,12,14,10][this.category]]);}
    for(const[id,x,y]of [[3025,16,53],[3026,19,85],[3027,27,117],[3028,28,149]])mask(id,x,y);
    if(options){draw(3039,3034,112,77);draw(3001,3000,182,79);
      for(const [enabled,y]of [[this.mixUp,81],[this.propsEnabled,97]])if(enabled)surface.blit(s.shape("th",9),new Uint32Array(256).fill(0xffffffff),184,y,10);}
    else if(!this.openingEditor)draw(3035+this.director,3034,61,155);
    if(this.propsEnabled){draw(3024,3000,1,163);draw(3011,3000,24,163);}
    const drawActionPreview=()=>{if(selected[1]>=0){if(this.preview&&!this.preview.done)this.preview.draw(surface);else {const a=selected[1],id=3050+t.action_preview_shapes[a],shape=s.shape("modules",id),off=t.action_preview_offsets[a];draw(id,3050,285-Math.floor(shape.w/2)+off[1],109-Math.floor(shape.h/2)+off[0]);}}};
    drawActionPreview();
    const measure=text=>[...text].reduce((sum,c)=>sum+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);
    const lines=[];let remaining=this.sentence(selected),offset=0;
    while(remaining){let end=remaining.length;while(end>0&&measure(remaining.slice(0,end))>200)end--;
      // Overlay 2CD0 starts before the fitted count, excluding an overflowing separator.
      if(end<remaining.length){const space=remaining.lastIndexOf(" ",end-1);if(space>0)end=space;}
      lines.push({value:remaining.slice(0,end),offset});offset+=end+1;remaining=remaining.slice(Math.max(1,end)).trimStart();}
    const line=this.textSurface;line.pixels.set(surface.pixels);
    let phraseStart=0,range=null;
    for(const c of this.stageOrder||this.order){const phrase=this.phrase(c,selected);if(!phrase)continue;if(c===this.presenting)range=[phraseStart,phraseStart+phrase.length+1];phraseStart+=phrase.length+1;}
    // Original measures line two after the separator, then renders the restored space (0x2e65..0x2eef).
    lines.slice(0,2).forEach(({value,offset},i)=>{
      const text=(i?" ":"")+value,start=offset-(i?1:0),x=100+Math.floor((200-measure(value))/2),y=(lines.length>1?176:180)+i*10;
      if(range){const from=Math.max(0,range[0]-start),to=Math.min(text.length,range[1]-start);if(to>from)line.text(s,text.slice(from,to),x+measure(text.slice(0,from))+1,y,s.palette("modules",3000).rgba[[6,12,14,10][this.presenting]]);}
      line.text(s,text,x,y);
    });
    for(let y=176;y<195;y++)for(let x=100;x<300;x++)surface.pixels[y*320+x]=line.pixels[y*320+x];
    if(this.mixUp){draw(3012,3000,105,49);draw(3013,3000,243,47);draw(3002,3000,129,43);
      for(let i=0;i<4;i++){const c=this.order[i];if(this.selection[c]<0||this.tokenSprite?.category===c||(this.drag?.type==='token'&&this.drag.active&&this.drag.category===c))continue;const b=t.ui_rects[23+i],shape=s.shape("modules",3003+c);if(this.presenting===c)surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],s.palette("modules",3000).rgba[[6,12,14,10][c]]);draw(3003+c,3000,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),Math.floor((b[0]+b[2])/2)-Math.floor(shape.h/2));}}
    if(this.feedback||this.successFeedback){
      const message=s.data.strings["modules:3070"][this.feedback];
      surface.text(s,message,183-Math.floor(measure(message)/2),20);
      const icons={2:[[3018,135],[3019,178]],3:[[3018,149]],4:[[3019,149]],5:[[3018,138],[3019,213]]};
      if(!this.successFeedback)for(const [id,x]of icons[this.feedback]||[])draw(id,3000,x,18);
      if(this.feedback===5||this.feedback===6){const corrected=this.correctedOrder(this.feedback);for(let i=0;i<4;i++){const c=corrected[i];if(this.selection[c]<0)continue;const b=t.ui_rects[23+i],shape=s.shape("modules",3018+c);draw(3018+c,3000,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),Math.floor((b[0]+b[2])/2)-23-Math.floor(shape.h/2));}}
    }
    if(this.category>=0&&this.correctNoticeUntil===null){
      const names=s.data.strings["modules:3060"],name=names[this.category];
      const width=[...name].reduce((n,c)=>n+(s.data.heading_font[c.charCodeAt(0)]?.[0]||3)+1,0);surface.text(s,name,188-Math.floor(width/2),4,0xff000000,s.data.heading_font,1);
      const boxes=this.choiceBounds();
      for(let i=0;i<boxes.length;i++){
        const b=boxes[i];let id,palette,x,y;
        if(this.category===0){id=3981+i;palette=3980;x=b[1]+2;y=42-s.shape("modules",id).h;}
        else if(this.category===1){id=3085+i;palette=3050;[y,x]=t.action_icon_positions[i];}
        else if(this.category===2){id=3102+3*i;palette=3100+3*i;const shape=s.shape("modules",id);x=Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2);y=28-Math.floor(shape.h/2);}
        else if(this.category===3){id=3120+t.time_shapes[i][0];palette=3120;const shape=s.shape("modules",id);x=Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2);y=28-Math.floor(shape.h/2);}
        else {const p=this.selection[2];palette=t.prop_group[p]?3175:3145;id=palette+t.prop_first[p]+i;const shape=s.shape("modules",id);x=Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2);y=28-Math.floor(shape.h/2);}
        draw(id,palette,x,y,this.category===2?2:10);
      }
    }
    if(this.correctNoticeUntil!==null){const message=s.data.strings['modules:3070'][7];surface.text(s,message,183-Math.floor(measure(message)/2),20);}
    if(this.tokenSprite)draw(3003+this.tokenSprite.category,3000,this.tokenSprite.x,this.tokenSprite.y);
    if(this.drag?.type==='token'&&this.drag.active)draw(3003+this.drag.category,3000,this.drag.x,this.drag.y);
    // 158F/16AD draw each curtain stage over the prepared scene, including
    // its rail and options. These stay behind the curtain until it reopens.
    if(this.curtainMoving){
      draw(3040+curtain[0],3040,pos[1],pos[0]);if(curtain[1])draw(3040+curtain[1],3040,pos[3],pos[2]);draw(3049,3040,259,73);
      // 14E0 redraws the action card (1E76); scene changes also repaint the
      // director (2453) after each curtain stage. Initial editor opening does not.
      if(!options&&!this.openingEditor){
        drawActionPreview();
        // The director's saved background is captured after open curtains
        // (143E..145C), so restore those pixels as well as the room backdrop.
        const r=t.ui_rects[7],opened=t.curtain_shapes[3],p=t.curtain_positions[3];
        surface.draw(s,"modules",3041,3040,0,0,2,r);
        surface.draw(s,"modules",3040+opened[0],3040,p[1],p[0],10,r);
        if(opened[1])surface.draw(s,"modules",3040+opened[1],3040,p[3],p[2],10,r);
        draw(3035+this.director,3034,61,155);
      }
    }
  }
}
