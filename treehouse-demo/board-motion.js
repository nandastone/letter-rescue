"use strict";
// Blocking DOS routines become a tick-driven sequence, keeping input responsive
// while preserving the order of transfers and the original exchange decisions.
class BoardMotion {
  constructor(game){this.game=game;this.cancel();}
  cancel(){this.iterator=null;this.due=0;this.sprite=null;this.dashboard=null;this.exchangeFrame=null;this.panels=null;this.accepted=false;this.speaking=false;this.reminding=false;this.exchangeInterruptible=false;this.exchangeInterrupted=false;}
  get busy(){return this.iterator!==null;}
  start(sequence){this.iterator=sequence;this.due=this.game.tick;this.update(this.game.tick);}
  update(tick){
    if(!this.iterator||tick<this.due)return false;
    for(let guard=0;guard<100;guard++){
      const next=this.iterator.next();
      if(next.done){this.iterator=null;this.sprite=null;this.dashboard=null;this.exchangeFrame=null;this.game.changed();return true;}
      if(next.value>0){this.due=tick+next.value;return true;}
    }
    throw new Error("Board sequence did not yield");
  }
  *target(node,path){const g=this.game;g.nodeHint=node;yield 12;g.nodeHint=-1;g.path=path;g.nextEdge();}
  *continuePath(){yield 12;this.game.nextEdge();}
  *performDashboard(){
    const g=this.game,id=4100+20*g.role();this.dashboard=new Animation(g.store,"modules",id,id,{startTick:g.tick,onSound:g.speak});
    while(!this.dashboard.done){this.dashboard.update(g.tick);if(!this.dashboard.done)yield 1;}
    this.dashboard=null;
  }
  *postRoll(){
    const g=this.game;g.phase='blink';
    for(let i=0;i<3;i++){g.carHidden=true;yield 12;g.carHidden=false;yield 12;}
    g.phase='move';g.hintDue=g.tick+300;g.changed();
  }
  *robotTurn(){yield 60;yield* this.say(1011);this.game.robotPath();}
  *say(id){const ticks=this.game.speak(id)||0;this.speaking=true;if(ticks>0)yield ticks;this.speaking=false;}
  interruptSpeech(){if(!this.speaking)return;this.game.stopSpeak();this.due=this.game.tick;}
  interruptExchange(){if(this.exchangeInterruptible){this.exchangeInterrupted=true;this.due=this.game.tick;}}
  *reminder(kind,clicked=-1){const g=this.game;this.reminding=true;if(kind==='reward'){for(let panel=0;panel<2;panel++){g.offerHint=panel;g.speak(10052-panel);yield 12;g.offerHint=-1;}}else{for(const node of [...(clicked>=0?[clicked]:[]),...g.neighbours()]){g.nodeHint=node;yield 12;g.nodeHint=-1;}}this.reminding=false;g.hintDue=g.tick+300;}
  *number(n){
    const tens=[30,0,20,13,14,15,6,7,8,19],teens=[10,11,12,13,14,15,6,7,8,19];
    if(n>=100){yield* this.number(Math.floor(n/100));yield 5;yield* this.say(11029);n%=100;if(n){yield 5;yield* this.say(11150);yield 5;}}
    if(n){if(n>=10&&n<20){yield* this.say(11000+teens[n%10]);if(n>=13){yield 5;yield* this.say(11027);}}else{if(n>=20){yield* this.say(11000+tens[Math.floor(n/10)]);yield 5;yield* this.say(11022);yield 5;}yield* this.say(11000+n%10);if(n%10===8)yield* this.say(11021);}}yield 5;
  }
  *amount(value){
    if(value<0){yield* this.say(11167);yield 30;value=-value;}
    if(this.game.mode){yield* this.number(value);yield* this.say(value===1?11154:11155);return;}
    const dollars=Math.floor(value/100),cents=value%100;if(dollars){yield* this.number(dollars);yield* this.say(dollars===1?11156:11157);if(cents)yield* this.say(11150);}if(cents){yield* this.number(cents);yield* this.say(cents===1?11152:11153);}
  }
  *selection(){
    const g=this.game;g.phase='selection';g.offerStage='flash';g.speak(10052-g.chosen);g.changed();yield 12;g.offerStage='white';if(!g.mode)yield 1;
    if(g.mode){g.offerStage='bag';yield 30;}
    g.offerStage='revealed';if(!g.mode)yield 1;g.headerHidden=true;yield 30;g.headerHidden=false;g.setChoiceMessage();g.offerStage='feedback';g.changed();
    const value=g.rewards[g.chosen],other=g.rewards[1-g.chosen];if(value===other)yield* this.say(11151);else{yield* this.say(11163);yield 10;yield* this.say(value>other?11160:g.mode?11166:11158);yield 10;yield* this.say(g.mode?11155:11159);}yield 24;yield* this.amount(value);
    if(g.mode){g.finishChoice(false);yield* this.chipTransfer();}else yield* this.moneyCredit();
  }
  *landing(payment){
    const g=this.game;this.panels=0;g.headerHidden=true;yield 30;g.headerHidden=false;yield* this.say(payment?1027:1028);
    if(!payment){yield* this.deliver();return;}
    g.phase='payment';yield* this.amount(-g.paymentRequested);
    if(g.mode){g.startTransfer(g.paymentBefore,-Math.min(g.paymentBefore,g.paymentRequested),false);yield* this.chipTransfer();}
    else yield* this.moneyDebit(g.paymentRequested,g.paymentBefore);
  }
  *ending(){
    const g=this.game;if(g.winner<0&&g.loser<0)return;g.ending=true;g.endingTitle='';g.phase='ending';g.headerHidden=true;yield 30;
    if(g.winner>=0){yield* this.say(1005);g.headerHidden=false;g.endingTitle='This player WON!';yield* this.say(11164);if(g.balances[g.player]>g.goal())yield* this.say(11161);yield* this.amount(g.goal());}
    else{g.headerHidden=false;g.endingTitle='This player LOST!';}
    g.ending=false;g.phase='result';g.remaining=-1;g.hintDue=g.tick;g.hintStep=0;g.changed();
  }
  *deliver(payment=false){
    const g=this.game;g.phase=payment?"payment":"delivery";this.panels=0;g.changed();
    // Overlay3:3A1B, two-pixel clock wait, four horizontal pixels per step.
    for(const panel of payment?[g.mode]:g.mode?[1]:[0,1]){
      const clip=panel?[98,226,194,320]:[19,226,102,320],y=clip[0]+11*panel+10;
      for(let x=320;x>=232;x-=4){this.sprite={id:payment?4301:4302,palette:4300,x,y,clip};yield 2;}
      if(payment){g.paymentHand={id:4301,palette:4300,x:232,y,clip};this.sprite=null;this.panels=null;return;}
      this.panels=g.mode?2:panel+1;g.speak(1024);
      for(let x=228;x<=320;x+=4){this.sprite={id:4302,palette:4300,x,y,clip};yield 2;}
      this.sprite=null;
    }
    // Overlay 3:2E16 clears the reminder timer after delivering the offers.
    this.panels=null;g.phase="reward";g.hintDue=g.tick;g.changed();
  }
  *travel(id,from,to,delay=2,alternate=id){
    // Resident 6DA9: Manhattan line, error starts dx/2 (or -1 for vertical).
    let [x,y]=from;const [tx,ty]=to,dx=Math.abs(tx-x),dy=Math.abs(ty-y),sx=Math.sign(tx-x),sy=Math.sign(ty-y);
    let error=dx?Math.floor(dx/2):-1,step=0;
    while(true){const end=x===tx&&y===ty;
      if(end||step%8===0){this.sprite={id:step%16===0?id:alternate,palette:4400,x,y};yield delay;}
      if(end)break;if(error>=0){x+=sx;error-=dy;}else{y+=sy;error+=dx;}step++;
    }
    this.sprite=null;
  }
  *moneyCredit(){
    const g=this.game,r=g.tables.money_rects[8+g.chosen];
    g.phase="credit";g.speak(10035);g.changed();
    yield* this.travel(4414,[r[1]+25,r[0]+24],[204,48],4);
    g.speak(1025);
    g.finishChoice();
    yield* this.ending();
    // Overlay 3's reward routine returns to the roll state after credit.
    // Winning endings also do this; ordinary credits must clear it too.
    g.remaining=-1;
  }
  *moneyDebit(payment,before){
    const g=this.game,r=g.tables.money_rects[8];g.phase='payment';g.balances[g.player]=before;g.changed();
    if(payment>before){yield 60;payment=before;}
    g.rewards=[before?-payment:-g.paymentRequested];let left=payment;g.rewardCoins=[g.tables.coin_values.map(v=>{const n=Math.floor(left/v);left%=v;return n;})];
    if(before){yield* this.deliver(true);g.phase='payment';g.balances[g.player]=before-payment;yield 60;g.speak(10035);yield* this.travel(4414,[204,48],[r[1]+25,r[0]+24],4);g.speak(1024);g.paymentCoinsVisible=true;}
    g.loser=g.paymentLoser??-1;g.phase='result';g.remaining=-1;g.hintDue=g.tick+300;yield* this.ending();g.changed();
  }
  *chipTransfer(){
    const g=this.game,t=g.transfer;if(t.sign<0||Object.is(t.sign,-0))yield* this.deliver(true);g.phase="transfer";g.changed();
    while(t.ops.length){
      const d=t.ops[0],unit=10**(2-d),stack=g.tables.chip_rects[1+d];
      if(t.sign<0&&t.digits[d]===0){
        let higher=d-1;while(higher>=0&&t.digits[higher]===0)higher--;
        if(higher<0)throw new Error("Chip payment exceeds available chips");
        yield* this.exchange("borrow",higher);continue;
      }
      if(t.sign>0){
        t.ops.shift();const panel=g.tables.chip_rects[8+g.chosen],cell=t.ops.length;
        yield* this.travel(4420+d,[panel[1]+13*(cell%3),panel[0]+13*Math.floor(cell/3)],[stack[1],41]);g.speak(1023);yield 20;
        t.digits[d]++;g.balances[g.player]+=unit;g.speak(1025);
        if(d>0&&t.digits[d]===10){yield* this.exchange("carry",d);}
      }else{
        t.ops.shift();t.digits[d]--;g.balances[g.player]-=unit;g.speak(1025);yield 20;
        const panel=g.tables.chip_rects[8],cell=t.paid||0;t.paid=cell+1;
        yield* this.travel(4420+d,[stack[1],41],[panel[1]+13*(cell%3),panel[0]+13*Math.floor(cell/3)]);g.paidChips.push(d);g.speak(1023);yield 20;
      }
    }
    g.winner=t.winner;g.loser=t.loser;g.transfer=null;g.phase="result";g.remaining=-1;g.hintDue=g.tick+300;
    yield* this.ending();
  }
  *exchange(kind,digit){
    const g=this.game,t=g.transfer,stack=g.tables.chip_rects[1+digit],carry=kind==="carry";
    const records=[[8,9,10,21,10,9,8],[11,12,13,20,13,12,11],[8,9,10,21],[11,12,13,20],[3,21,10,9,8,9,10,21,3],[2,20,13,12,11,12,13,20,2],[3,21,10,9,8],[2,20,13,12,11]];
    const hint=carry?2-digit:5-digit,commit=hint+2;
    const rect=carry?[stack[2]-20,stack[1],stack[2],stack[3]]:[stack[0]-4,stack[1],stack[0]+16,stack[3]];
    g.exchange={kind,digit};g.phase="exchange";this.accepted=false;g.changed();
    while(!this.accepted){
      g.exchange.flash=true;yield 6;g.exchange.flash=false;g.speak(1026);
      this.exchangeInterrupted=false;this.exchangeInterruptible=true;
      for(const shape of records[hint]){if(this.accepted||this.exchangeInterrupted)break;this.exchangeFrame={shape:4400+shape,rect};yield 10;}
      this.exchangeInterruptible=false;
      this.exchangeFrame=null;for(let i=0;i<60&&!this.accepted;i++)yield 1;
    }
    g.phase="transfer";g.changed();g.speak(1026);
    for(const shape of records[commit]){this.exchangeFrame={shape:4400+shape,rect};yield 10;}
    this.exchangeFrame=null;g.exchange=null;
    if(carry){
      const target=g.tables.chip_rects[digit];t.digits[digit]=0;
      yield* this.travel(digit===2?4421:4420,[stack[1],57],[target[1],41]);g.speak(1023);yield 20;t.digits[digit-1]++;g.speak(1025);
      if(digit>1&&t.digits[digit-1]===10)yield* this.exchange("carry",digit-1);
    }else{
      const target=g.tables.chip_rects[2+digit];t.digits[digit]--;
      yield* this.travel(digit===1?4408:4411,[stack[1],stack[0]-4],[target[1],53]);t.digits[digit+1]+=10;yield 20;
    }
  }
  draw(surface){
    const g=this.game;if(this.dashboard)this.dashboard.draw(surface);
    if(this.exchangeFrame)g.centered(surface,this.exchangeFrame.shape,this.exchangeFrame.rect,4400,0xffffffff);
    if(this.sprite){const s=this.sprite;surface.draw(g.store,"modules",s.id,s.palette,s.x,s.y,10,s.clip);}
  }
}
