"use strict";
// Overlay 3's directed road game. Tables and amount formulas are recovered
// from DOS 1.1; the browser owns input, retained state and original-resource draws.
class BoardGame {
  constructor(store,{changed=()=>{},speak=()=>{},stopSpeak=()=>{},character=()=>"boy"}={}) {
    this.store=store;this.tables=store.data.boardgame;this.changed=changed;this.speak=speak;this.stopSpeak=stopSpeak;this.character=character;
    this.mode=0;this.opponent=2;this.levels=[0,0];this.options=true;this.played=false;this.optionsBackground=null;this.hintRed=false;this.hintStep=0;this.hintDue=300;this.tick=0;this.phase="ready";
    this.player=0;this.nodes=[7,15];this.directions=[0,2];this.balances=[10,10];this.types=[...this.tables.node_types];
    this.motion=new BoardMotion(this);this.paymentHand=null;this.paymentCoinsVisible=false;this.paidChips=[];
    this.remaining=-1;this.first=true;this.winner=-1;this.loser=-1;this.rewards=[];this.rewardCoins=[];this.path=[];this.moving=null;this.notice="Choose a game and a goal.";this.message="";this.rollFrames=[];this.rollDue=null;
  }
  selectGame(mode=this.mode,opponent=this.opponent){this.savedLevels??=Array(6).fill(0);this.savedLevels[3*this.mode]=this.levels[0];this.savedLevels[3*this.mode+this.opponent]=this.levels[1];this.mode=mode;this.opponent=opponent;this.levels=[this.savedLevels[3*mode],this.savedLevels[3*mode+opponent]];this.changed();}
  get seed(){return gameplayRandom.seed;}
  set seed(value){gameplayRandom.reset(value);}
  random(max){return gameplayRandom.int(max);}
  role(){return this.player===0?0:this.opponent;}
  level(){return this.levels[this.player];}
  goal(player=this.player){return this.tables.goals[this.levels[player]];}
  amount(n){return this.mode?`${n} ${n===1?"chip":"chips"}`:`$${(n/100).toFixed(2)}`;}
  playerName(){return this.player===0?"You":this.opponent===2?"The robot":"Your friend";}
  neighbours(node=this.nodes[this.player]){return this.tables.adjacency[node].filter(n=>n>=0);}
  newBoard(){this.resolvedNodeIcons={};this.types=[...this.tables.node_types];let n=0;while(n<3){const i=this.random(23);if(this.types[i]!==23){this.types[i]=23;n++;}}}
  prepareGame(){
    this.motion.cancel();this.offerHint=-1;this.nodeHint=-1;this.offerStage=null;this.headerHidden=false;this.ending=false;this.carHidden=false;this.paymentHand=null;this.paymentCoinsVisible=false;this.paidChips=[];
    this.optionsBackground=null;this.hintRed=false;this.hintStep=0;this.hintDue=this.tick+300;this.first=true;this.player=this.opponent===2?0:this.random(1);this.winner=-1;this.loser=-1;this.remaining=-1;this.phase="ready";this.rewards=[];this.message="";this.path=[];this.moving=null;this.rollDue=null;this.transfer=null;this.exchange=null;
    for(let p=0;p<2;p++){let node;do{node=this.random(23);}while(this.tables.starting_node_exclusions[node]);this.nodes[p]=node;const ds=this.tables.adjacency[node].map((n,d)=>n>=0?d:-1).filter(d=>d>=0);this.directions[p]=ds.find(d=>d!==1)??ds[0];this.balances[p]=this.tables.starting_balances[this.mode][this.levels[p]];}
    this.newBoard();this.notice=`${this.playerName()} ${this.player===0?"start":"starts"} with ${this.amount(this.balances[this.player])}. Roll to begin.`;
  }
  // Overlay 3 initializes and draws a game before opening its options panel.
  enter(){this.prepareGame();this.options=true;this.played=false;this.changed();}
  start(){if(this.opponent===2)this.levels[1]=this.levels[0];this.prepareGame();this.options=false;this.played=true;this.phase="intro";this.motion.start(this.introduction());this.changed();}
  *introduction(){yield* this.motion.performDashboard();this.phase="ready";}
  stopReminder(){if(this.motion.reminding){this.motion.cancel();this.offerHint=-1;this.nodeHint=-1;this.hintDue=this.tick+300;}}
  roll(){
    this.stopReminder();
    if(this.motion.busy||this.options||this.moving||this.phase==="rolling"||this.phase==="move"||this.phase==="reward"||this.phase==="exchange")return;
    this.speak(1045);
    if(this.winner>=0||this.loser>=0){this.award?.();return;}
    if(!this.first){this.player=1-this.player;this.newBoard();this.rewards=[];this.rewardCoins=[];this.message="";this.remaining=-1;this.phase="intro";this.motion.start(this.turnIntroduction());return;}this.first=false;this.beginRoll();
  }
  *turnIntroduction(){yield* this.motion.performDashboard();this.beginRoll();}
  beginRoll(){
    this.offerHint=-1;this.nodeHint=-1;this.offerStage=null;this.headerHidden=false;this.ending=false;this.paymentHand=null;this.paidChips=[];this.hintRed=false;this.hintStep=0;this.rewards=[];this.rewardCoins=[];this.message="";this.phase="rolling";
    const choices=this.tables.roll_values[this.level()].slice(0,this.tables.roll_counts[this.level()]);
    this.rollResult=choices[this.random(choices.length-1)];this.rollFrames=[];
    let previous=-1;
    for(let i=0;i<7;i++){let value;do{value=this.mode?choices[this.random(choices.length-1)]:1+this.random(4);}while(value===previous||(i===6&&value===this.rollResult));this.rollFrames.push(value);previous=value;}
    this.rollFrames.push(this.rollResult);this.rollIndex=0;this.remaining=this.rollFrames[0];this.rollDue=this.tick+6;this.speak(1045);this.notice="Rolling…";this.changed();
  }
  findPath(target,steps=this.remaining,node=this.nodes[this.player]){
    if(steps===0)return node===target?[]:null;
    for(const next of this.neighbours(node)){const path=this.findPath(target,steps-1,next);if(path)return[next,...path];}
    return null;
  }
  move(target){
    this.stopReminder();
    if(this.phase!=="move"||this.moving||this.motion.busy||this.role()===2)return false;
    const path=this.neighbours().includes(target)?[target]:this.findPath(target);
    if(!path?.length){this.notice=`Follow an arrow. You have ${this.remaining} ${this.remaining===1?"move":"moves"} left.`;this.motion.start(this.motion.reminder("move",target));this.changed();return false;}
    this.hintDue=this.tick+300;this.motion.start(this.motion.target(target,path));return true;
  }
  robotPath(){
    let node=this.nodes[this.player];this.path=[];
    for(let i=0;i<this.remaining;i++){
      if(i===this.remaining-1){const choices=this.neighbours(node);node=choices.reduce((best,n)=>this.types[n]<this.types[best]?n:best,choices[0]);}
      else{
        // Overlay 3:0308 retries all four directions until a road exists.
        // Rejected directions still consume the shared random sequence.
        const roads=this.tables.adjacency[node];let next;
        do{next=roads[this.random(3)];}while(next<0);
        node=next;
      }
      this.path.push(node);
    }
    this.nextEdge();
  }
  center(node){const[t,l,b,r]=this.tables.node_rects[node];return[(l+r)/2,(t+b)/2];}
  nextEdge(){
    if(!this.path.length)return;
    const from=this.nodes[this.player],to=this.path.shift(),direction=this.tables.adjacency[from].indexOf(to);
    if(direction<0)throw new Error("Road path contains a missing edge");
    this.directions[this.player]=direction;const a=this.center(from),b=this.center(to);
    this.speak(1020+this.player);this.moving={from,to,x:a[0],y:a[1],tx:b[0],ty:b[1],due:this.tick+3};this.changed();
  }
  amounts(type){
    const level=this.level(),r=n=>this.random(n);let a,d;
    if(type===26){const specs=this.mode?[[4,4,2],[8,9,2],[37,58,2]]:[[5,8,4],[10,15,4],[50,75,4]],v=specs[level];a=-Math.floor((v[0]+r(v[1]))/v[2]);
      // Overlay 3:37C4 consumes the pair-direction draw even for a payment.
      r(1);return[a];}
    const specs=this.mode?(type===23?[[10,3],[21,4],[99,41]]:[[4,4],[8,9],[37,58]]):(type===23?[[12,3],[24,6],[114,51]]:[[5,6],[10,13],[47,78]]);
    const v=specs[level];a=v[0]+r(v[1]);d=1+r((type===23?[1,4,9]:[1,2,4])[level]);return[a,(a+(r(1)?d:-d))||1];
  }
  coins(amount){return this.tables.coin_values.map((value,i)=>{let n=Math.floor(amount/value);if(i<3&&n>0&&this.random(1))n--;amount-=n*value;return n;});}
  land(){
    this.offerHint=-1;this.nodeHint=-1;this.offerStage=null;this.headerHidden=false;this.ending=false;this.paymentHand=null;this.paymentCoinsVisible=false;this.paidChips=[];
    const node=this.nodes[this.player];let type=this.types[node];const mystery=type===25;if(mystery){this.resolvedNodeIcons??={};this.resolvedNodeIcons[node]=25;type=this.random(1)?24:26;this.types[node]=type;}
    this.rewards=this.amounts(type);const phrases=this.store.data.strings[`modules:${3987+type}`]||[];this.message=phrases.length?phrases[this.random(phrases.length-1)]:"";
    // The original prepares payment coins before replacing them with the
    // greedy payment display. That preparation still consumes random draws.
    if(type===26&&!this.mode){this.coins(-this.rewards[0]);
      // Resolving a mystery node leaves the unused amount delta at zero
      // (overlay 3:1CE8, resident 3BA6's unsigned remainder argument).
      // Both prepared amounts therefore equal the payment. Direct payment
      // nodes retain a separate cursor-allocation dependency still under study.
      if(mystery)this.coins(-this.rewards[0]);}
    if(type===26){const payment=-this.rewards[0],balance=this.balances[this.player];this.paymentRequested=payment;this.paymentBefore=balance;this.balances[this.player]=balance;this.phase="payment";this.paymentLoser=payment>balance?this.player:-1;this.loser=-1;this.notice=`${this.message} Pay ${this.amount(Math.min(payment,balance))}. ${this.loser>=0?"This player lost. Choose a prize for the other player.":"Roll for the next turn."}`;}
    else{this.rewardCoins=this.mode?[]:this.rewards.map(n=>this.coins(n));this.phase="delivery";this.notice=`${this.message} Choose which amount ${this.player===0?"you collect":"the other player collects"}.`;}
    this.motion.start(this.motion.landing(type===26));
    this.hintDue=this.tick+300;this.changed();
  }
  choose(index){
    this.stopReminder();
    if(this.phase!=="reward"||this.motion.busy||index<0||index>1)return;
    this.chosen=index;this.creditBefore=this.balances[this.player];this.motion.start(this.motion.selection());this.changed();
  }
  setChoiceMessage(){
    const value=this.rewards[this.chosen],other=this.rewards[1-this.chosen];
    const comparison=value===other?"the same amount":value>other?"more":this.mode?"fewer":"less";
    // Original resident strings at DS:0DF8..0E55.
    this.message=value===other?"Both were the SAME.":`You picked ${comparison.toUpperCase()} ${this.mode?"chips":"money"}${value>other?"!":"."}`;
  }
  finishChoice(animate=true){
    const value=this.rewards[this.chosen],before=this.creditBefore;this.balances[this.player]=before+value;this.phase="result";
    if(this.balances[this.player]>=this.goal())this.winner=this.player;
    this.hintDue=this.tick+300;this.notice=`${this.message} ${this.playerName()} collected ${this.amount(value)}. ${this.winner>=0?"This player won! Choose a prize.":"Roll for the next turn."}`;if(this.mode)this.startTransfer(before,value,animate);this.changed();
  }
  startTransfer(before,amount,animate=true){
    const magnitude=Math.abs(amount),ops=[];for(let d=2;d>=0;d--){const unit=10**(2-d),count=Math.floor(magnitude/unit)%(d===0?1000:10);for(let i=0;i<count;i++)ops.push(d);}
    this.transfer={before,digits:[Math.floor(before/100),Math.floor(before%100/10),before%10],ops,sign:Math.sign(amount),winner:this.winner,loser:amount<=0?(this.paymentLoser??this.loser):this.loser};
    this.winner=-1;this.loser=-1;this.balances[this.player]=before;if(animate)this.motion.start(this.motion.chipTransfer());
  }
  advanceTransfer(){
    const t=this.transfer;this.exchange=null;
    while(t.ops.length){const d=t.ops[0];
      if(t.sign<0&&t.digits[d]===0){let higher=d-1;while(higher>=0&&t.digits[higher]===0)higher--;if(higher<0)throw new Error("Chip payment exceeds available chips");this.exchange={kind:"borrow",digit:higher};break;}
      t.ops.shift();t.digits[d]+=t.sign;this.balances[this.player]+=t.sign*10**(2-d);
      if(t.sign>0&&d>0&&t.digits[d]===10){this.exchange={kind:"carry",digit:d};break;}
    }
    if(this.exchange)this.phase="exchange";else{this.winner=t.winner;this.loser=t.loser;this.transfer=null;this.phase="result";}
  }
  exchangeChips(){
    if(this.motion.busy){if(this.phase==="exchange")this.motion.accepted=true;return;}
    if(!this.exchange||!this.transfer)return;const e=this.exchange,t=this.transfer;
    if(e.kind==="carry"){t.digits[e.digit]=0;t.digits[e.digit-1]++;if(e.digit>1&&t.digits[e.digit-1]===10){this.exchange={kind:"carry",digit:e.digit-1};this.changed();return;}}
    else{t.digits[e.digit]--;t.digits[e.digit+1]+=10;}
    this.advanceTransfer();this.changed();
  }
  exchangeText(){const units=["hundred","ten","one"],e=this.exchange;return e.kind==="carry"?`Trade ten ${e.digit===2?"ones":"tens"} for one ${units[e.digit-1]}.`:`Trade one ${units[e.digit]} for ten ${e.digit===0?"tens":"ones"}.`;}
  update(tick){
    this.tick=tick;if(this.options)return false;
    if(this.motion.busy)return this.motion.update(tick);
    if((this.phase==="ready"||this.phase==="result")&&tick>=this.hintDue){this.hintRed=this.hintStep%2===0;this.hintStep++;this.hintDue=tick+12;if(this.hintStep===6){this.hintStep=0;this.hintDue=tick+300;}return true;}
    if((this.phase==="reward"||this.phase==="move"&&!this.moving)&&tick>=this.hintDue){this.motion.start(this.motion.reminder(this.phase));return true;}
    if(this.phase==="rolling"&&tick>=this.rollDue){
      this.rollIndex++;
      if(this.rollIndex<8){this.remaining=this.rollFrames[this.rollIndex];this.rollDue=tick+6+this.rollIndex;this.speak(1045);}
      else{this.remaining=this.rollResult;this.rollDue=null;this.phase="move";this.notice=`${this.playerName()}: move ${this.remaining} spaces along the arrows.`;if(this.role()===2)this.motion.start(this.motion.robotTurn());else this.motion.start(this.motion.postRoll());this.changed();}return true;
    }
    if(this.moving&&tick>=this.moving.due){const m=this.moving;
      if(!m.arrived){m.x+=Math.sign(m.tx-m.x)*Math.min(2,Math.abs(m.tx-m.x));m.y+=Math.sign(m.ty-m.y)*Math.min(2,Math.abs(m.ty-m.y));m.due=tick+3;if(m.x!==m.tx||m.y!==m.ty)return true;m.arrived=true;this.stopSpeak();if(this.role()!==2){m.due=tick+12;return true;}}
      this.nodes[this.player]=m.to;this.remaining--;this.speak(1045);this.moving=null;this.hintDue=tick+300;
      if(this.remaining===0){this.path=[];this.land();}else if(this.path.length){if(this.role()===2)this.nextEdge();else this.motion.start(this.motion.continuePath());}else this.changed();return true;
    }
    return this.phase==="exchange"&&tick%6===0;
  }
  hit(rect,x,y){return x>=rect[1]&&x<rect[3]&&y>=rect[0]&&y<rect[2];}
  showOptions(){this.stopReminder();if(this.motion.busy||this.moving||this.phase==='rolling')return;this.options=true;this.changed();}
  click(x,y){
    this.stopReminder();
    if(this.motion.busy){this.motion.interruptSpeech();if(this.phase==='exchange'){this.motion.interruptExchange();if(this.hit(this.tables.chip_rects[1+this.exchange.digit],x,y))this.exchangeChips();}return;}
    const t=this.tables;
    if(this.options){const i=t.options_rects.findIndex(r=>this.hit(r,x,y));
      if(i===17){this.start();return;}if(i===1||i===2)this.selectGame(i-1);
      else if(i===3||i===4)this.selectGame(this.mode,i-2);else if(i>=5&&i<=7)this.levels[0]=i-5;else if(i>=8&&i<=10)this.levels[1]=i-8;this.changed();return;}
    if(this.hit(t.game_rects[2],x,y)){this.roll();return;}
    if(this.hit(t.game_rects[1],x,y)&&this.winner<0&&this.loser<0){this.motion.start(this.motion.performDashboard());return;}
    if(this.hit(t.game_rects[5],x,y)){this.speak(1012);return;}
    const rects=this.mode?t.chip_rects:t.money_rects;
    if(this.hit(rects[0],x,y)){this.showOptions();return;}
    if(this.phase==="exchange"){if(this.hit(rects[1+this.exchange.digit],x,y))this.exchangeChips();return;}
    if(this.phase==="reward"){if(this.hit(rects[8],x,y))this.choose(0);else if(this.hit(rects[9],x,y))this.choose(1);return;}
    let node=t.node_rects.findIndex(r=>this.hit(r,x,y));if(node>=24)node=t.extra_node_map[node-24];if(node>=0)this.move(node);
  }
  draw(surface){
    if(this.options){if(!this.optionsBackground){const mode=this.mode;if(!this.played)this.mode=0;this.drawBoard(surface);this.mode=mode;this.optionsBackground=surface.clone();}else surface.restore(this.optionsBackground);this.drawOptions(surface);}
    else{this.optionsBackground=null;this.drawBoard(surface);}
  }
  fill(surface,rect,color){surface.rect(rect[1],rect[0],rect[3]-rect[1],rect[2]-rect[0],color);}
  centered(surface,id,rect,palette=4400,background=null,archive="modules"){
    if(background!==null)this.fill(surface,rect,background);const shape=this.store.shape(archive,id);
    surface.draw(this.store,archive,id,palette,Math.floor((rect[1]+rect[3])/2)-Math.floor(shape.w/2),Math.floor((rect[0]+rect[2])/2)-Math.floor(shape.h/2));
  }
  width(value){return [...value].reduce((n,c)=>n+(this.store.data.font[c.charCodeAt(0)]?.[0]||4),0);}
  label(surface,value,rect,align="center",vertical="center",color=0xff000000){
    const lines=[];for(let remaining of String(value).split(/\r?\n|\r/)){
      while(this.width(remaining)>rect[3]-rect[1]){let width=0,end=0,legal=0;while(end<remaining.length){const ch=remaining[end];width+=this.width(ch);if(width>rect[3]-rect[1])break;end++;if(ch==='-'||(align==='right'?ch!==' '&&remaining[end]===' ':ch===' '||remaining[end]===' '))legal=end;}const n=legal||Math.max(1,end);lines.push(remaining.slice(0,n));remaining=remaining.slice(n);}lines.push(remaining);
    }
    let y=vertical==="top"?rect[0]:vertical==="bottom"?rect[2]-lines.length*10+1:rect[0]+Math.ceil((rect[2]-rect[0])/2)-Math.ceil(lines.length*10/2);
    for(const line of lines){const x=align==="left"?rect[1]:align==="right"?rect[3]-this.width(line):Math.floor((rect[1]+rect[3])/2)-Math.floor(this.width(line)/2);surface.text(this.store,line,x,y,color,this.store.data.font,0,rect);y+=10;}
  }
  drawBoard(surface){
    const t=this.tables,rects=[...t.game_rects.slice(0,6),...(this.mode?t.chip_rects:t.money_rects)],role=this.role(),dashboard=4200+10*role;
    const draw=(id,pal,x,y,mode=10)=>surface.draw(this.store,"modules",id,pal,x,y,mode);
    surface.clear(this.store.palette("modules",4000).rgba[13]);draw(4001,4000,2,83,2);draw(dashboard+1,dashboard,0,0,2);
    if(this.mode){draw(4002,4000,221,8);draw(4004,4000,221,73);this.fill(surface,[75,226,87,299],this.winner>=0&&!this.ending?0xff5555ff:0xffffffff);for(let i=0;i<3;i++)this.centered(surface,4420+i,rects[16+i]);}
    else{this.fill(surface,[64,144,75,209],this.winner>=0&&!this.ending?0xff5555ff:0xffffffff);draw(4003,4000,137,14);draw(4005,4000,221,73,2);}
    const balance=this.balances[this.player],digits=this.transfer?.digits||[Math.floor(balance/100),Math.floor(balance%100/10),balance%10];
    for(let i=0;i<3;i++){
      const r=rects[7+i];if(this.mode)this.fill(surface,[r[0]+1,r[1]-(i===0?6:5),r[2],r[3]+(i===2?6:5)],this.exchange?.flash&&this.exchange.digit===i?0xff5555ff:0xffffffff);for(let j=0;j<digits[i];j++)draw((this.mode?4402:4405)+i,4400,r[1],r[2]-2-j*2);
      if(i===2||(this.mode?balance>=10**(2-i):i>0||balance>=100))this.label(surface,String(digits[i]),rects[11+i]);
    }
    draw(this.headerHidden?4007:4006,4000,111,0);
    const goal=this.mode?`Game Goal: ${this.goal()} Chips`:`Game Goal: ${this.store.data.strings["modules:4000"][this.level()]}`;
    if(!this.headerHidden)this.label(surface,this.ending?this.endingTitle:this.winner>=0?"This player WON!":this.loser>=0?"This player LOST!":this.message||goal,rects[4]);
    surface.draw(this.store,"th",8,6,304,1);draw(4401,4400,rects[6][1],rects[6][0]);
    for(let i=0;i<24;i++)this.centered(surface,4400+(this.resolvedNodeIcons?.[i]??this.types[i]),t.node_rects[i]);
    if(this.nodeHint>=0){this.centered(surface,4427,t.node_rects[this.nodeHint]);this.centered(surface,4400+(this.resolvedNodeIcons?.[this.nodeHint]??this.types[this.nodeHint]),t.node_rects[this.nodeHint]);}
    if(!this.ending&&(this.winner>=0||this.loser>=0))this.centered(surface,922,rects[2],900,this.hintRed?0xff5555ff:0xffffffff,'th');
    else if(this.remaining<0||this.phase==="result"&&!this.ending)this.centered(surface,4425,rects[2],4400,this.hintRed?0xff5555ff:0xffffffff);
    else if(this.remaining>0)this.centered(surface,4007+this.remaining,rects[2],4000,0xffffffff);
    else this.fill(surface,rects[2],0xffffffff);
    if((!this.options||this.played)&&!this.carHidden){
      const direction=this.directions[this.player],id=4442+(direction===1?1:direction===3?2:0)+3*role,shape=this.store.shape("modules",id),c=this.moving?[this.moving.x,this.moving.y]:this.center(this.nodes[this.player]);
      let car=shape;if(direction===0){const pixels=new Uint8Array(shape.pixels.length);for(let y=0;y<shape.h;y++)for(let x=0;x<shape.w;x++)pixels[y*shape.w+x]=shape.pixels[y*shape.w+shape.w-1-x];car={...shape,pixels};}
      surface.blit(car,this.store.palette("modules",4400).rgba,Math.floor(c[0])-Math.floor(shape.w/2),Math.floor(c[1])-Math.floor(shape.h/2));
      // The one-shot dashboard performance returns to the retained dashboard image.
      // Its transient poses will be stepped separately from this stable compositor.
    }
    if(this.rewards.length)this.drawRewards(surface,rects);
    this.motion.draw(surface);

  }
  drawRewards(surface,rects){
    const revealed=["result","exchange","credit","transfer","ending"].includes(this.phase)||["revealed","feedback"].includes(this.offerStage),payment=this.rewards.length===1;
    for(let panel=0;panel<this.rewards.length;panel++){
      if(!payment&&this.motion.panels!==null&&panel>=this.motion.panels)continue;
      const r=rects[14+panel],amount=Math.abs(this.rewards[panel]),selected=revealed&&!payment&&panel===this.chosen;
      this.fill(surface,r,(this.offerStage==='flash'&&panel===this.chosen||this.offerHint===panel)?0xff5555ff:revealed&&!payment&&!selected?0xffaaaaaa:0xffffffff);
      if(payment&&this.paymentHand){const h=this.paymentHand;surface.draw(this.store,'modules',h.id,h.palette,h.x,h.y,10,h.clip);}
      if(payment&&this.mode){for(let i=0;i<this.paidChips.length;i++)surface.draw(this.store,'modules',4420+this.paidChips[i],4400,r[1]+13*(i%3),r[0]+13*Math.floor(i/3));this.label(surface,'Pay '+(this.paymentRequested??amount),[r[0],r[1]+4,r[2],r[3]-4],'right','bottom');continue;}
      if(!this.mode){let cell=0;const coins=this.rewardCoins[panel]||this.tables.coin_values.map((v,i)=>{const previous=this.tables.coin_values.slice(0,i).reduce((a,v)=>a%v,amount);return Math.floor(previous/v);});
        if(!payment||this.paymentCoinsVisible||this.phase==='result')for(let d=0;d<6;d++)for(let j=0;j<coins[d];j++){const x=r[1]+1+20*(cell%4),y=r[0]+17*Math.floor(cell/4);this.centered(surface,4430+d+(selected&&this.phase!=="selection"?6:0),[y,x,y+17,x+20]);cell++;}
        const shownAmount=payment?(this.paymentRequested??amount):amount,value=shownAmount>=100?`$ ${Math.floor(shownAmount/100)}.${String(shownAmount%100).padStart(2,"0")}`:`${shownAmount} ${shownAmount===1?"Cent":"Cents"}`;
        this.label(surface,payment?"Pay "+value:revealed?value:"???",[r[0],r[1]+4,r[2],r[3]-4],"center","bottom");
      }else{
        if(panel===0||revealed){let cell=0;const digits=selected&&this.phase!=="selection"?(this.transfer?[0,1,2].map(d=>this.transfer.ops.filter(op=>op===d).length):[0,0,0]):[Math.floor(amount/100),Math.floor(amount%100/10),amount%10];for(let d=0;d<3;d++)for(let j=0;j<digits[d];j++){surface.draw(this.store,"modules",4420+d,4400,r[1]+13*(cell%3),r[0]+13*Math.floor(cell/3));cell++;}}
        else this.centered(surface,this.offerStage==='bag'?4415:4414,[r[0]+20,r[1],r[2]-40,r[3]],4400,this.offerStage==='bag'?0xffffffff:null);
        const before=this.transfer?.before??(this.offerStage||this.phase==="credit"?this.creditBefore:this.balances[this.player]-(revealed&&!payment?this.rewards[this.chosen]:0)),sum=before+this.rewards[panel];
        this.label(surface,`${panel===0||revealed?amount:"???"}\r${panel===1||revealed?sum:"???"}`,[r[2]-19,r[1]+4,r[2]+1,r[3]-4],"right","top");
        surface.text(this.store,"+",r[1]+2,178);surface.rect(r[1]+2,185,36,1,0xff000000);
      }
    }
    if(!payment&&this.motion.panels!==0)surface.draw(this.store,"modules",4429,4400,this.mode?263:260,this.mode?128:101,2);
  }
  drawOptions(surface){
    const t=this.tables.options_rects,pal=this.store.palette("modules",4050).rgba,bg=pal[7];
    surface.draw(this.store,"modules",4051,4050,27,12);
    this.centered(surface,20201,t[22],20200,null,this.character());
    const mark=(i,on)=>{this.fill(surface,t[i],pal[1]);if(on)surface.blit(this.store.shape("th",9),[0,pal[5]],t[i][1],t[i][0]);};
    mark(1,this.mode===0);mark(2,this.mode===1);this.centered(surface,4416+this.mode,t[18],4400,bg);
    mark(3,this.opponent===1);mark(4,this.opponent===2);
    if(this.opponent===2)this.fill(surface,t[21],bg);else this.centered(surface,22201,t[23],22200,null,"th");
    const group=this.opponent===1?22200:24200;this.centered(surface,group+2,t[24],group,bg,"th");
    for(let p=0;p<(this.opponent===1?2:1);p++){
      for(let i=0;i<3;i++){mark(5+p*3+i,this.levels[p]===i);this.fill(surface,t[11+p*3+i],bg);this.label(surface,this.store.data.strings[`modules:${4000+this.mode}`][i],t[11+p*3+i],"left","top");}
      const icon=[31,30,28,19,20,18][3*this.mode+this.levels[p]];this.centered(surface,4400+icon,t[19+p],4400,bg);
    }
  }
}
