"use strict";
// Resident character/object state. SCR scripts supply the original movement,
// sound cues, and callbacks; all rectangles use top,left,bottom,right order.
class RoomCharacter {
  constructor(store,{character,scene,room,balloon,roomIdle=()=>false,sound,stopSound=()=>{},changed,announce}){
    Object.assign(this,{store,character,scene,room,balloon,roomIdle,sound,stopSound,changed,announce});this.tables=store.data.room;
    this.tick=0;this.pose=0;this.hunger=1+gameplayRandom.int(2);this.fatigue=1+gameplayRandom.int(2);this.ambientEnabled=true;this.selected=false;this.ambientDue=Infinity;this.longDue=Infinity;this.outsideCycle=0;this.hungerDue=7200;this.fatigueDue=14400;
    this.active=null;this.actionPreparation=null;this.queue=[];this.after=null;this.drag=null;this.wakeTime=null;this.objects=[];this.objectMotion=null;
    for(const type of [9,20,8,10,6])this.create(type);this.restore();
  }
  get sex(){return this.character()==='girl'?1:0;}
  get busy(){return !!(this.active||this.actionPreparation||this.queue.length||this.objectMotion||this.objectTask||this.ambientAnimation||this.drag?.released);}
  rect(){const r=this.tables.poses[this.pose].slice();if(!this.sex)r[0]+=this.pose===3?5:this.pose<3?4:0;return r;}
  hit(r,x,y){return x>=r[1]&&x<r[3]&&y>=r[0]&&y<r[2];}
  bounds(object){return object.type===6?[this.balloon.y,this.balloon.x,this.balloon.y+38,this.balloon.x+29]:object.rect;}
  setBounds(object,r){if(object.type===6){this.balloon.x=r[1];this.balloon.y=r[0];}object.rect=r.slice();}
  create(type,inside=true){let object=this.objects.find(o=>o.type===type);if(!object){if(this.objects.length>=21)return null;object={type,state:1,inside,rect:[],due:0};this.objects.push(object);}object.state=1;object.hidden=false;object.foodFrame=undefined;object.nestMirror=false;object.inFrontOfCharacter=false;object.inside=inside;object.rect=this.tables.objects[type][inside?'inside':'outside'].slice();if(type===6)this.balloon.hidden=false;this.resetObjectTimer(object);this.changed();return object;}
  resetObjectTimer(object){const type=object.type;object.due=this.tick;if(type===6){object.due+=48;this.balloon.due=object.due;}if(type===11)object.due=this.tick+(6+gameplayRandom.int(10))*60;if(type===16)object.due=this.tick+(120+gameplayRandom.int(60))*60;
    // Original B8A3 also postpones ambient events for every non-balloon object.
    // Its random draw is shared with the next activity's deal (BC43).
    if(type!==6)this.scheduleAmbient();}
  remove(object){const i=this.objects.indexOf(object);if(i>=0)this.objects.splice(i,1);if(object.type===6)this.balloon.hidden=true;this.changed();}
  save(){try{localStorage.setItem('treehouse-room-objects-v1',JSON.stringify({version:1,objects:this.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:this.bounds(o),due:0}))}));}catch(_error){}}
  restore(){try{const v=JSON.parse(localStorage.getItem('treehouse-room-objects-v1'));if(v?.version!==1||!Array.isArray(v.objects)||v.objects.length>21||v.objects.some(o=>!o||!Number.isInteger(o.type)||o.type<0||o.type>20||!Number.isInteger(o.state)||o.state<0||o.state>20||typeof o.inside!=='boolean'||!Array.isArray(o.rect)||o.rect.length!==4||o.rect.some(n=>!Number.isInteger(n)||n< -400||n>600)))return;this.objects=v.objects.filter(o=>o.type!==15&&!(o.type===7&&o.state===5));for(const o of this.objects){o.state=[6,7,14].includes(o.type)?Math.max(1,Math.min(o.type===6?3:4,o.state)):1;o.due=0;}if(!this.objects.some(o=>o.type===8))this.create(8);const balloon=this.objects.find(o=>o.type===6);this.balloon.hidden=!balloon;if(balloon)this.setBounds(balloon,balloon.rect);}catch(_error){}}
  need(name,value){this[name]=Math.max(1,Math.min(5,value));this[name+'Due']=this.tick+(name==='hunger'?7200:14400);this.changed();}
  action(action,after=null){this.queue.push({action,after});this.startNext();this.changed();}
  startNext(){
    if(this.active||this.actionPreparation||!this.queue.length)return;
    const entry=this.queue.shift(),action=entry.action,exempt=this.tables.exempt[action],variant=exempt?0:this.pose===1?200:this.pose===2?100:0,id=20500+action+variant,script=this.store.data.scripts[`${this.character()}:${id}`];
    let origin=null;
    if(exempt&&(this.pose===1||this.pose===2))origin=[script.bounds[1]+(this.pose===1?59:-132),script.bounds[0]+(this.pose===1?-3:4)];
    const bounds=script.bounds.slice();
    if(origin){const dx=origin[0]-bounds[1],dy=origin[1]-bounds[0];bounds[0]+=dy;bounds[2]+=dy;bounds[1]+=dx;bounds[3]+=dx;}
    // Main 43AC..43D7 clears the relocated script rectangle before playback.
    // Keep this separate from the object generator: a released object may
    // offer itself to the child while its placement generator is returning.
    this.actionPreparation={task:this.clearBalloon(bounds),due:this.tick,entry,id,origin};
    this.stepActionPreparation();
  }
  stepActionPreparation(){
    const pending=this.actionPreparation;if(!pending||this.tick<pending.due)return false;
    const next=pending.task.next();
    if(!next.done){pending.due=this.tick+next.value;this.changed();return true;}
    this.actionPreparation=null;
    const {entry,id,origin}=pending;
    this.active=new Animation(this.store,this.character(),id,20500,{startTick:this.tick,origin,onSound:id=>{this.active.soundDue=this.tick+(this.sound(id)||0);},onCallback:(slot,arg)=>{if(slot===0)this.callback(arg);}});
    this.active.soundDue=this.tick;this.active.action=entry.action;this.after=entry.after;this.applyPose(entry.action);this.active.update(this.tick);this.changed();return true;
  }
  callback(arg){if(arg<=3){const o=this.create(17+arg),r=o.rect,w=r[3]-r[1],h=r[2]-r[0],left=arg===this.sex?94:245;o.rect=[146-h,left,146,left+w];if(arg!==this.sex){o.rect[0]-=4;o.rect[2]-=4;}}
    else if(arg===4)this.create(8);else if(arg===5){const o=this.create(8,false);o.rect=[182,122,196,134];}
    else if(arg===6&&this.objects.length)this.remove(this.objects.at(-1));else if(arg===7&&this.objects.length){const o=this.objects.at(-1);if(--o.state<=0)this.remove(o);}
    else if(arg===8){const o=this.create(5),dx=this.pose===1?59:this.pose===2?-132:0,dy=this.pose===1?-3:this.pose===2?4:0;o.rect=[142+dy,162+dx,153+dy,185+dx];o.inFrontOfCharacter=true;}
    else if(arg===9){const bird=this.objects.find(o=>o.type===15);if(bird)bird.state++;}this.changed();}
  applyPose(action){if([6,7,8,9,14,28].includes(action)&&action-this.sex!==6)this.pose=1;else if(action===16)this.pose=2;else if(action===18||action===20)this.pose=4;else if(action===19)this.pose=3;else if([21,22,29,30].includes(action))this.pose=0;}
  // Original action wrapper 392B schedules ambient events at 39B4 on return.
  finishAction(){const after=this.after;this.after=null;this.active=null;this.scheduleAmbient();if(after)after();this.startNext();this.changed();}
  clickCharacter(){if(this.busy)return;if(this.pose===4){this.action(20);return;}if(this.fatigue>=4){this.action(16);return;}if(this.hunger>=4){if(this.pose===2)this.action(29);this.action(14);return;}this.action(23);}
  center(){if(this.pose===1)this.action(30);else if(this.pose===2)this.action(29);}
  sleep(){const date=this.room.now();date.setMinutes(date.getMinutes()+(date.getSeconds()<=30?2:3));date.setSeconds(0,0);this.wakeTime=date;this.action(18,()=>{this.room.sayTime(this.wakeTime,true);this.need('fatigue',1);this.announce(`Nap time. Wake up at ${this.wakeTime.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}.`);});}
  wake(interrupted=false,after=null){if(this.pose!==4){if(after)after();return;}const finish=()=>{this.pose=0;this.wakeTime=null;this.need('fatigue',interrupted?4:1);if(after)after();};if(this.scene()!=='inside'){this.create(8);finish();}else this.action(interrupted?22:21,finish);}
  offer(object){if(this.pose===4)return false;const type=object.type,food=()=>{this.need('hunger',1);this.need('fatigue',this.fatigue+1);};if(type>=17){this.remove(object);if(this.hunger>1)this.action(type-16,()=>{this.need('hunger',this.hunger-2);this.need('fatigue',this.fatigue+1);});else this.action(type-11);}
    else if(type===8){this.remove(object);if(this.fatigue>=4)this.sleep();else this.action(17);}
    // Main 94D2 recreates the magnifying glass after action 24, then rejoins
    // ordinary placement at 96C5 using the released rectangle. Placement also
    // resets the object/ambient timer; returning at the default prize position
    // loses both that placement and its shared random draw.
    else if(type===2){const released=this.bounds(object).slice();this.remove(object);this.action(24,()=>{const returned=this.create(2);this.setBounds(returned,released);this.runObject(this.placeObject(returned),{resetAmbient:false});});}
    else if(type===3||type===4){this.remove(object);this.action(type===3?26:27,food);}
    else if(type===5){this.remove(object);this.action(25,()=>{const o=this.objects.find(o=>o.type===5);if(o)this.runObject(this.departure(o),{resetAmbient:false});});}
    else if(type===11){this.remove(object);if(this.hunger===5)this.action(5,()=>{this.need('hunger',4);this.need('fatigue',this.fatigue+1);});else this.action(10,()=>{let pile=this.objects.find(o=>o.type===14);if(pile)pile.state=Math.min(4,pile.state+1);else this.create(14,false);});}
    else if(type===12){const bird=this.objects.some(o=>o.type===15);this.remove(object);this.action(bird?12:11,()=>{if(!bird)this.create(13,false);else this.runObject(this.feedNest([218,95],true));});}else return false;return true;}
  begin(x,y){if(this.busy)return false;const inside=this.scene()==='inside',object=[...this.objects].reverse().find(o=>o.inside===inside&&this.hit(this.bounds(o),x,y));if(!object)return false;const clickOnly=[0,9,10,14,15,16].includes(object.type)||(!inside&&object.type===1)||(object.type===7&&object.state===5),r=this.bounds(object);this.objects.splice(this.objects.indexOf(object),1);this.objects.push(object);this.drag={object,rect:r.slice(),start:[x,y],point:[x,y],since:this.tick,moved:false,clickOnly};return true;}
  dispatchPress(d){this.drag=null;this.clickObject(d.object,d.start);if(d.released&&this.drag?.newlyCreated)this.end();}
  fruit(type,x,y){const o=this.create(type);this.drag={object:o,rect:o.rect.slice(),start:[x,y],point:[x,y],since:this.tick,moved:false};}
  move(x,y){const d=this.drag;if(!d)return false;if(d.released)return true;d.point=[x,y];if(d.clickOnly)return true;if(this.tick-d.since<15)return true;d.moved||=Math.abs(x-d.start[0])>=2||Math.abs(y-d.start[1])>=2;if(d.moved){const dx=Math.round(x-d.start[0]),dy=Math.round(y-d.start[1]);this.setBounds(d.object,[d.rect[0]+dy,d.rect[1]+dx,d.rect[2]+dy,d.rect[3]+dx]);this.changed();}return true;}
  // 9141 waits 15 ticks before dragging; 67F2 starts a second 15-tick
  // click window. Once both expire, release places even a stationary object.
  end(cancel=false){const d=this.drag;if(!d)return;this.drag=null;if(cancel){this.setBounds(d.object,d.rect);this.changed();return;}if(!d.moved&&(d.clickOnly||this.tick-d.since<30)){if(d.clickOnly){d.released=true;d.due=this.tick+1;this.drag=d;}else this.clickObject(d.object);return;}this.runObject(this.releaseDrag(d),{resetAmbient:false});this.save();this.changed();}
  // The original clears the released rectangle before recreating the object
  // (9323/9344). Balloon movement is visible and takes two ticks per step.
  *releaseDrag(d){let object=d.object;const r=this.bounds(object).slice();if(object.type!==6){const type=object.type,inside=object.inside;this.remove(object);yield* this.clearBalloon(r);object=this.create(type,inside);this.setBounds(object,r);}if(this.scene()==='inside'&&this.hit(this.rect(),...d.point)&&this.offer(object))return;yield* this.placeObject(object);}
  *clearBalloon(r){const b=this.balloon;if(this.scene()!=='inside'||b.hidden)return;this.clearingBalloon=true;while(b.x<r[3]&&b.x+29>r[1]&&b.y<r[2]+2&&b.y+38>r[0]-2){b.y-=2;const object=this.objects.find(o=>o.type===6);if(object){this.objects.splice(this.objects.indexOf(object),1);this.objects.push(object);}yield 2;}this.clearingBalloon=false;}
  place(object){this.runObject(this.placeObject(object),{resetAmbient:false});}
  *placeObject(object){const r=this.bounds(object).slice(),inside=this.scene()==='inside',x=Math.floor((r[1]+r[3])/2),y=r[2],surfaces=this.tables.surfaces[Number(inside)];let index=surfaces.findIndex((b,i)=>!(inside&&(i===5||(this.room.open&&i<3)))&&this.hit(b,x,y));if(!inside&&index===0)index=1;if(index<0){this.setBounds(object,this.tables.objects[object.type][inside?'inside':'outside']);return;}yield* this.settlePlacement(object,index,inside,r);}
  *settlePlacement(object,index,inside,r){const bottom=this.tables.surfaces[Number(inside)][index][2],h=r[2]-r[0],target=[bottom-h,r[1],bottom,r[3]];if(!inside&&index===1?170>r[0]:bottom>r[2])yield* this.fall(object,r,target,inside&&index===9,!inside&&index===1?[50,170]:null);else this.setBounds(object,target);this.resetObjectTimer(object);
    if(inside&&index===0&&(object.type===5||object.type===12)){yield* this.nestConsume(object);return;}
    if(inside&&index===9){object.inside=false;if([3,4,17,18,19,20].includes(object.type)){this.remove(object);this.create(16,false);return;}if(object.type===12){this.remove(object);if(!this.objects.some(o=>o.type===13))this.create(13,false);return;}if(object.type===11){this.remove(object);let pile=this.objects.find(o=>o.type===14);if(pile)pile.state=Math.min(4,pile.state+1);else this.create(14,false);return;}if(object.type===7){object.state=5;this.sound(1034);}this.setBounds(object,this.tables.objects[object.type].outside);return;}
    if(!inside&&index===2){if(object.type===13){this.remove(object);if(!this.objects.some(o=>o.type===12))this.create(12);return;}object.inside=true;this.setBounds(object,this.tables.objects[object.type].inside);return;}
    if(!inside&&index===1){const type=object.type;this.remove(object);if(type!==2&&type!==8)this.sound(10002);this.playAmbient(type===2?1004:type===8?1003:1005,1000);}
  }
  *fall(o,from,to,straight=false,destination=null){const t=this.tables.objects[o.type],id=this.store.palette('th',t.palette).first+t.states[o.state%10]-1,delta=to[0]-from[0],end=destination||[to[1],to[0]];o.hidden=true;if(o.type===1&&delta>36&&!straight){const p1=[from[1]-40,from[0]+Math.trunc(delta/4)],p2=[p1[0]+80,p1[1]+Math.trunc(delta/2)];yield* this.flight([from[1],from[0]],p1,[id,id],t.palette,{step:6,delay:3});yield* this.flight(p1,p2,[id,id],t.palette,{step:6,delay:3,mirror:true});yield* this.flight(p2,end,[id,id],t.palette,{step:6,delay:3});}else{if(delta>50)this.sound(10021);yield* this.flight([from[1],from[0]],end,[id,id],t.palette,{step:6,delay:1});}o.hidden=false;this.setBounds(o,to);if(o.type===7&&delta>60){o.state=5;this.sound(1034);}}
  *chirp(){this.room.interact('chirp');while(this.room.busy)yield 1;}
  *nestConsume(o){yield* this.chirp();o.hidden=true;yield* this.chirp();this.remove(o);}
  *feedNest(from,fromOffer=false){this.room.target=28;while(this.room.height>28)yield 2;yield* this.chirp();if(fromOffer){yield* this.birdFlight(from,[200,86],true);from=[200,86];}yield* this.birdFlight(from,[222,74],true);const bird=this.create(15);bird.state=2;bird.nestMirror=true;bird.rect=[70,222,90,247];yield* this.chirp();bird.state=1;const worm=this.create(12);worm.rect=[74,240,86,257];worm.nestMirror=true;yield* this.nestConsume(worm);this.sound(12025);yield* this.birdFlight([222,74],[312,48],false,[0,0,200,283]);}
  runObject(task,{resetAmbient=true}={}){this.objectResetsAmbient=resetAmbient;this.objectTask=task;this.objectDue=this.tick;this.stepObject();}
  stepObject(){if(!this.objectTask||this.tick<this.objectDue)return false;const next=this.objectTask.next();if(next.done){this.objectTask=null;this.objectSprite=null;if(this.objectResetsAmbient)this.scheduleAmbient();this.save();}else this.objectDue=this.tick+next.value;this.changed();return true;}
  mirrored(shape){const pixels=new Uint8Array(shape.pixels.length);for(let y=0;y<shape.h;y++)for(let x=0;x<shape.w;x++)pixels[y*shape.w+x]=shape.pixels[y*shape.w+shape.w-1-x];return {...shape,pixels};}
  *flight(from,to,ids,palette,{step=16,delay=10,mirror=false,clip=null}={}){
    let [x,y]=from;const [tx,ty]=to,dx=Math.abs(tx-x),dy=Math.abs(ty-y),sx=Math.sign(tx-x),sy=Math.sign(ty-y);let error=dx?Math.floor(dx/2):-1,n=0;
    for(;;){const end=x===tx&&y===ty;if(end||n%step===0){let shape=this.store.shape('th',ids[n%(2*step)===0?0:1]);if(mirror)shape=this.mirrored(shape);this.objectSprite={shape,palette,x,y,clip};yield delay;}if(end)break;if(error>=0){x+=sx;error-=dy;}else{y+=sy;error+=dx;}n++;}this.objectSprite=null;
  }
  *departure(o){
    if(o.type===0){this.sound(1031);for(let n=0;n<3;n++){o.state++;yield 30;}this.sound(1036);o.state++;}
    if(o.type===5){o.state=2;yield 30;this.sound(1022);}
    if(o.type===1)this.sound(1018);
    const r=this.bounds(o),ids=o.type===0?[886,887]:o.type===1?[889,889]:[897,898],shape=this.store.shape('th',ids[0]),from=[Math.floor((r[1]+r[3])/2)-Math.floor(shape.w/2),Math.floor((r[0]+r[2])/2)-Math.floor(shape.h/2)],right=r[1]<160;
    if(right&&this.scene()==='inside'){this.room.target=28;while(this.room.height>28)yield 2;}
    o.hidden=o.type!==0;yield* this.flight(from,right?[312,48]:[-30,88],ids,870,{mirror:right,clip:right&&this.scene()==='inside'?[0,0,200,283]:null});this.remove(o);this.stopSound();
  }
  *highlight(o){this.objects.splice(this.objects.indexOf(o),1);this.objects.push(o);for(let n=0;n<3;n++){o.hidden=true;yield 12;o.hidden=false;yield 12;}}
  *nuts(bag){let nut=this.objects.find(o=>o.type===11);if(nut){yield* this.highlight(nut);return;}bag.state=2;this.sound(1014);nut=this.create(11);yield 4;for(const [i,r]of [[152,271,161,283],[146,255,155,267],[153,244,162,256],[162,237,171,249],[178,232,187,244]].entries()){nut.rect=r;if(i===2)this.sound(10038);yield 4;}bag.state=1;}
  *basket(o,point=null){const worm=this.objects.find(v=>v.type===12);if(worm){yield* this.highlight(worm);return;}if(o.state===1){this.sound(1001);for(let n=0;n<3;n++){o.state++;yield 8;}this.sound(1010);for(let n=0;n<3;n++){o.state=o.state===4?3:4;yield 8;}yield* this.summonBird();}else{o.state=1;const w=this.create(12);w.rect=[160,6,172,23];if(point)this.drag={object:w,rect:w.rect.slice(),start:point.slice(),point:point.slice(),since:this.tick,moved:false,newlyCreated:true};}}
  *birdFlight(from,to,carrying=false,clip=null,removeExisting=true){const base=(to[1]>from[1]?950:946)+2*Number(carrying);const bird=this.objects.find(o=>o.type===15);if(bird&&removeExisting)this.remove(bird);yield* this.flight(from,to,[base,base+1],930,{step:10,delay:8,mirror:to[0]>from[0],clip});this.scheduleAmbient();}
  *perchedBirdDeparture(){this.room.target=28;while(this.room.height>28&&this.scene()==='inside')yield 2;yield* this.birdFlight([218,95],[132,32],false,[0,163,200,320]);}
  *summonBird(){if(this.objects.some(o=>o.type===15))return;this.room.target=28;while(this.room.height>28)yield 2;yield* this.birdFlight([312,48],[218,95],false,[0,0,200,283]);const bird=this.create(15);bird.rect=[95,218,115,243];}
  *takeWorm(o){const inside=this.scene()==='inside',r=o.rect,to=[r[1]+2,r[0]-6],bird=this.objects.find(v=>v.type===15),from=inside?(bird?[218,95]:[312,48]):[350,10];yield* this.birdFlight(from,to);this.remove(o);const b=this.create(15,inside);b.state=2;b.rect=[to[1],to[0],to[1]+20,to[0]+25];yield 20;if(!inside||this.room.open||gameplayRandom.int(1))yield* this.birdFlight(to,[-30,88],true);else yield* this.feedNest(to);}
  *worm(o){this.sound(1010);for(let n=0;n<2;n++){o.state++;yield 12;o.state--;yield 12;}if(this.scene()==='inside'){this.room.target=28;while(this.room.height>28)yield 2;}this.sound(12025);if(this.objects.some(v=>v.type===15)||this.scene()==='outside')yield* this.takeWorm(o);else yield* this.summonBird();}
  scheduleAmbient(){this.ambientDue=this.tick+(20+gameplayRandom.int(10))*60;}
  // BB48 refreshes the indoor nut timer and the short ambient deadline too.
  scheduleLong(){this.longDue=this.tick+(120+gameplayRandom.int(60))*60;const nut=this.scene()==='inside'&&this.objects.find(o=>o.type===11);if(nut){nut.due=this.tick+(6+gameplayRandom.int(10))*60;this.scheduleAmbient();}this.scheduleAmbient();}
  enterScene(){this.selected=true;if(this.scene()==='outside'){this.windowDue=this.tick+10800;this.outsideCycle=0;this.pondAnimation=null;}this.scheduleAmbient();this.scheduleLong();for(const o of this.objects)if(o.inside===(this.scene()==='inside')){if(o.type===11)o.due=this.tick+(6+gameplayRandom.int(10))*60;if(o.type===16)o.due=this.tick+(120+gameplayRandom.int(60))*60;if(o.type!==6)this.scheduleAmbient();}}
  *naturalWake(){yield this.sound(11028)||1;this.wake();}
  windowStatus(){if(this.busy)return;if(this.pose===4){this.runObject((function*(){for(let i=0;i<2;i++){yield this.sound(10123)||1;yield 30;}this.stopSound();}).call(this));return;}const pillow=this.objects.some(o=>o.type===8&&o.inside);let variant=7;if(this.fatigue>=4){variant=pillow?(this.fatigue===4?3:4):2;this.fatigueDue=this.tick+3600;}else if(this.hunger>=4){variant=this.hunger===4?5:6;this.hungerDue=this.tick+3600;}this.runObject(this.windowScene(variant));}
  *windowScene(variant){for(const id of [20400,20400+variant,20401]){this.windowAnimation=new Animation(this.store,this.character(),id,20400,{startTick:this.tick,onSound:sound=>{if(id!==20400&&id!==20401)this.windowAnimation.soundDue=this.tick+(this.sound(sound)||0);}});this.windowAnimation.soundDue=this.tick;while(!this.windowAnimation.done){this.windowAnimation.update(this.tick);if(!this.windowAnimation.done)yield 1;}if(this.windowAnimation.soundDue>this.tick)yield this.windowAnimation.soundDue-this.tick;this.stopSound();}this.windowAnimation=null;this.windowDue=this.tick+10800;}
  speakStatus(){if(this.pose===4){this.room.sayTime(this.wakeTime,true);return;}let sound=this.hunger>=4?11053:this.fatigue>=4?11054:0;if(sound)this.room.say([11050,[5],sound]);else{const choice=gameplayRandom.int(3);if(choice<2)this.room.say([11050,[5],11051+choice]);else if(choice===2)this.room.say([11055+gameplayRandom.int(1)]);else{const queue=[];for(let i=0;i<3;i++)queue.push({sound:11057+gameplayRandom.int(4),mouth:false},[30]);queue.push(11062);this.room.say(queue);}}this.scheduleAmbient();}
  *flyby(){const inside=this.scene()==='inside';let from=inside?[312,48]:[350,10],to=[-30,88],clip=inside?[0,0,200,283]:null;if(inside){if(!gameplayRandom.int(1)){const point=[[132,32],[312,48],[-30,88]][gameplayRandom.int(2)];yield* this.feedNest(point);return;}if(gameplayRandom.int(1)){to=[132,32];clip=[0,163,200,283];}}if(gameplayRandom.int(1))[from,to]=[to,from];yield* this.birdFlight(from,to,false,clip,false);}
  // Original 883B chooses an activity; its handler schedules the next event
  // on completion. Scheduling here as well consumes a second random draw.
  ambient(){const inside=this.scene()==='inside';let choice=gameplayRandom.int(7);if(inside){if(this.room.open)choice=7;if(choice<2){const worm=this.objects.find(o=>o.type===12),bird=this.objects.find(o=>o.type===15);if(worm)this.runObject(this.worm(worm),{resetAmbient:false});else if(bird)this.clickObject(bird);else this.runObject(this.flyby());}else if(choice<4)this.room.interact('chirp');else if(choice<6)this.room.interact('nest');else if(choice===6)this.room.interact('spider');else if(this.pose!==4)this.speakStatus();}else if(choice<4){this.playAmbient(1000+this.outsideCycle,1000);this.outsideCycle=(this.outsideCycle+1)%3;}else if(choice<6){const worm=this.objects.find(o=>o.type===13);this.runObject(worm?this.takeWorm(worm):this.flyby());}else if(choice===6)this.playAmbient(1060,1060);}
  *consumeFood(food){this.consuming=food;this.sound(10017);yield 480;this.stopSound();this.remove(food);this.consuming=null;}
  // Resident 419D retains the final display while 577E waits on its sound.
  // Input consumes only that wait; the SCR itself continues to completion.
  interruptAudio(){
    for(const animation of [this.active,this.ambientAnimation])if(animation?.done&&this.tick<animation.soundDue){this.stopSound();animation.soundDue=this.tick;this.update(this.tick);return true;}
    if(this.windowAnimation?.done&&this.tick<this.windowAnimation.soundDue){this.stopSound();this.windowAnimation.soundDue=this.tick;this.objectDue=this.tick;this.stepObject();return true;}
    return false;
  }
  interruptFood(){if(!this.consuming)return false;this.objectDue=this.tick;this.stepObject();return true;}
  serviceEnvironment(){if(!this.ambientEnabled||!this.selected||!['inside','outside'].includes(this.scene())||!this.ambientAllowed?.())return false;const inside=this.scene()==='inside';if(this.tick>this.ambientDue){this.ambient();return true;}const food=this.objects.find(o=>o.type===16&&this.tick>o.due);if(food){if(inside)this.runObject(this.consumeFood(food),{resetAmbient:false});else this.playAmbient(1300,1300,food,0,{resetAmbient:false});return true;}if(this.tick>this.longDue){const pile=this.objects.find(o=>o.type===14);if(pile){this.consumePile(pile);return true;}this.scheduleLong();}return false;}
  consumePile(pile){if(this.scene()==='inside'){if(--pile.state===0)this.remove(pile);this.sound(10037);this.scheduleLong();}else this.playAmbient(1402,1400,pile,0,{resetAmbient:false,complete:()=>this.scheduleLong()});}
  playAmbient(id,palette,object=null,initialSoundTicks=0,{resetAmbient=true,complete=null}={}){this.ambientComplete=complete;this.ambientResetsAmbient=resetAmbient;if(object){this.objects.splice(this.objects.indexOf(object),1);this.objects.push(object);}this.ambientAnimation=new Animation(this.store,'th',id,palette,{startTick:this.tick,onSound:sound=>{this.ambientAnimation.soundDue=this.tick+(this.sound(sound)||0);},onCallback:(slot,arg)=>{if(id===1300){if(object)object.foodFrame=arg<4?6-arg:0;}else if(slot===0)this.callback(arg);}});if(id>=1000&&id<=1002)this.pondAnimation=this.ambientAnimation;this.ambientAnimation.soundDue=this.tick+initialSoundTicks;this.ambientObject=object;this.ambientAnimation.update(this.tick);this.changed();}
  clickObject(o,point=null){if(this.busy)return;const type=o.type;if([0,1,5].includes(type))this.runObject(this.departure(o),{resetAmbient:false});else if(type===6){this.sound(10011);o.state++;if(o.state>=4)this.remove(o);}else if(type===7){if(o.state!==5)o.state=o.state%4+1;this.sound(1007);}else if(type===2){this.sound(10028);this.objectMotion={object:o,frames:[2,3,4,1],index:0,due:this.tick,delay:8};}else if(type===9)this.runObject(this.nuts(o),{resetAmbient:false});else if(type===10)this.runObject(this.basket(o,point),{resetAmbient:false});else if(type===12||type===13)this.runObject(this.worm(o),{resetAmbient:false});else if(type===14)this.consumePile(o);else if(type===15){this.sound(12025);this.runObject(this.perchedBirdDeparture(),{resetAmbient:false});}else if(type===16){if(this.scene()==='inside')this.runObject(this.consumeFood(o),{resetAmbient:false});else this.playAmbient(1300,1300,o,0,{resetAmbient:false});}this.save();this.changed();}
  update(tick){this.tick=tick;let changed=!!(this.drag?.newlyCreated&&tick-this.drag.since===15);if(this.drag?.clickOnly&&(this.drag.released?tick>=this.drag.due:tick-this.drag.since>=15)){this.dispatchPress(this.drag);changed=true;}changed=this.stepObject()||changed;changed=this.stepActionPreparation()||changed;if(this.ambientAnimation){this.ambientAnimation.update(tick);changed=true;if(this.ambientAnimation.done&&(this.ambientAnimation.id===1300||tick>=this.ambientAnimation.soundDue)){this.stopSound();if(this.ambientAnimation.id===1300&&this.ambientObject)this.remove(this.ambientObject);this.ambientAnimation=null;this.ambientObject=null;if(this.ambientResetsAmbient)this.scheduleAmbient();const complete=this.ambientComplete;this.ambientComplete=null;complete?.();}}if(this.active&&!this.objectTask){this.active.update(tick);changed=true;if(this.active.done&&tick>=this.active.soundDue){this.stopSound();this.finishAction();}}const m=this.objectMotion;if(m&&tick>=m.due){m.object.state=m.frames[m.index++];m.due=tick+m.delay;if(m.index===m.frames.length)this.objectMotion=null;changed=true;}
    if(this.busy||this.drag||this.room.busy||this.room.speech.length||this.room.tick<this.room.speechDue)return changed;if(this.scene()==='inside'){if(this.roomIdle())changed=true;if(this.room.updateCloud())changed=true;}if(this.pose===4&&this.wakeTime&&this.room.now()>=this.wakeTime){this.runObject(this.naturalWake());return true;}
    if(this.scene()==='outside'){
      if(!this.selected)return changed;
      if(this.pose!==4){changed=this.updateNeeds(tick)||changed;if(this.busy)return changed;}
      return this.serviceEnvironment()||changed;
    }
    if(this.scene()!=='inside')return changed;
    const nut=this.objects.find(o=>o.type===11&&o.inside&&o.due&&tick>o.due&&o.rect[0]>=178&&o.rect[1]>=226&&o.rect[2]<=187&&o.rect[3]<=250);if(nut){this.playAmbient(1403,1400,nut);return true;}if(this.serviceEnvironment())return true;if(this.pose===4)return changed;
    return this.updateNeeds(tick)||changed;
  }
  // Room rebuild calls 575D/579B after the return effect. Original signed
  // low-word comparisons give urgent needs at least ten seconds of breathing room.
  postponeWarnings(tick){for(const name of ['hunger','fatigue'])if(this[name]>=3&&((this[name+'Due']-tick)<<16>>16)<600)this[name+'Due']=tick+600;}
  updateNeeds(tick){let changed=false;
    for(const name of this.scene()==='outside'?['fatigue','hunger']:['hunger','fatigue'])if(tick>=this[name+'Due']){
      const value=this[name],other=name==='hunger'?'fatigue':'hunger',suppressed=value>=4&&this[other]===5;
      const warn=value===3||value>=4&&!suppressed;
      this[name+'Due']=tick+(name==='hunger'?7200:14400);
      // Main 5578/564E finish their synchronous warning before incrementing
      // the need. Urgent retries and the other need's grace period likewise
      // start after the warning returns (5622/5731 and 575D/579B).
      const complete=()=>{
        if(warn&&this[other]>=3&&((this[other+'Due']-this.tick)<<16>>16)<600)this[other+'Due']=this.tick+600;
        if(value>=4)this[name+'Due']=this.tick+3600;
        if(!suppressed)this[name]=Math.min(5,this[name]+1);
        this.changed();
      };
      if(!warn)complete();
      else if(this.scene()==='outside'){
        const pillow=this.objects.some(o=>o.type===8&&o.inside),variant=name==='hunger'?(value===3?5:6):pillow?(value===3?3:4):2;
        this.runObject((function*(){yield* this.windowScene(variant);complete();}).call(this));
      }else{
        if(value>=4&&name==='hunger'&&this.pose===2)this.action(29);
        this.action(value===3?(name==='hunger'?13:15):(name==='hunger'?14:16),complete);
      }
      changed=true;break;
    }
    if(this.scene()==='outside'&&!this.busy&&this.hunger<4&&this.fatigue<4&&tick>=this.windowDue){this.runObject(this.windowScene(7));changed=true;}
    return changed;
  }
  // A00B..A044 creates the basket worm and saves its background without
  // drawing it. Its first draw follows the nested 9141 press wait.
  drawObjects(surface,inside,foreground=null,front=false){for(const o of this.objects){const aboveCharacter=!!(o.inFrontOfCharacter||this.drag?.moved&&this.drag.object===o);if(front!==aboveCharacter)continue;if(o.inside!==inside||o.hidden||this.drag?.newlyCreated&&this.drag.object===o&&this.tick-this.drag.since<15||foreground&&this.bounds(o)[2]<=foreground.minBottom)continue;if(o.type===16){const frame=o.foodFrame??7;if(frame)surface.draw(this.store,'th',this.store.palette('th',1300).first+frame-1,1300,o.rect[1],o.rect[0],10,foreground?.clip);continue;}const t=this.tables.objects[o.type],relative=t.states[o.state%10]||0;if(!relative)continue;const r=this.bounds(o);let shape=this.store.shape('th',this.store.palette('th',t.palette).first+relative-1);if(o.nestMirror||o.type===0&&o.state>=2&&o.state<=4&&r[1]<160)shape=this.mirrored(shape);surface.blit(shape,this.store.palette('th',t.palette).rgba,r[1],r[0],10,o.type===10?foreground?[Math.max(r[0],foreground.clip[0]),Math.max(r[1],foreground.clip[1]),Math.min(r[2],foreground.clip[2]),Math.min(r[3],foreground.clip[3])]:r:foreground?.clip);}}
  drawObjectMotion(surface){if(this.scene()==='outside'&&this.pondAnimation&&this.pondAnimation!==this.ambientAnimation)this.pondAnimation.draw(surface);if(this.windowAnimation)this.windowAnimation.draw(surface);if(this.ambientAnimation)this.ambientAnimation.draw(surface);if(this.objectSprite){const v=this.objectSprite;surface.blit(v.shape,this.store.palette('th',v.palette).rgba,v.x,v.y,10,v.clip);}}
  draw(surface){if(this.active)this.active.draw(surface);else{const id=20500+[1,1,1,4,15][this.pose],shape=this.store.shape(this.character(),id),r=this.rect();surface.draw(this.store,this.character(),id,20500,r[1],r[0]);}}
  drawNap(surface){if(!this.wakeTime)return;const hour=this.wakeTime.getHours()%12||12,minute=this.wakeTime.getMinutes(),shift=hour>9?0:3;const items=[[1212,4,142],[1202+hour%10,16-shift,142],[1213,22-shift,142],[1202+Math.floor(minute/10),24-shift,142],[1202+minute%10,29-shift,143]];if(hour>9)items.push([1203,11,143]);for(const[id,x,y]of items)surface.draw(this.store,'th',id,1200,x,y);}
}
