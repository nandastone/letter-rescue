"use strict";
// Original overlay 2 exploration: animal classifications, facts, and collages.
class NatureActivity {
  constructor(store,{changed=()=>{},announce=()=>{},character=()=>"boy",speak=()=>{},stopSound=()=>{},confirm=()=>{},print=()=>{}}={}) {
    this.store=store;this.tables=store.data.nature;this.changed=changed;this.announce=announce;this.speak=speak;this.confirm=confirm;this.print=print;
    this.time=0;this.attribute=0;this.values=Array(7).fill(0);this.category=3;
    this.selected=-1;this.factIndex=0;this.factOpen=false;this.objects=[[],[]];this.drag=null;
    this.tick=0;this.idleUntil=240;this.undo=null;this.mode="explore";
    this.quiz=new NatureQuiz(this,{character,speak,stopSound,leave:()=>this.leaveQuiz()});
  }
  strings(id){return this.store.data.strings[`modules:${id}`];}
  name(id){return this.strings(5000)[id];}
  attributeNames(){return this.strings(5300).slice(0,7);}
  valueNames(){return this.strings(5200+this.attribute);}
  classNames(){return this.strings(5208+this.time);}
  matching(){return this.tables.animals.filter(a=>a.active_time===this.time&&a.attributes[this.attribute]===this.values[this.attribute]);}
  availableClasses(){return new Set(this.matching().map(a=>a.category));}
  animals(){return this.matching().filter(a=>a.category===this.category);}
  facts(){return this.selected<0?[]:this.strings(5100+this.selected);}
  fact(){const facts=this.facts();return facts.length?facts[this.factIndex%facts.length]:"";}
  interact(){this.idleUntil=this.tick+240;}
  selectAttribute(index,cycle=true){if(this.eraseTask)return;this.speak(1008);this.interact();if(this.attribute===index&&cycle)this.values[index]=(this.values[index]+1)%this.strings(5200+index).length;this.attribute=index;this.category=-1;this.factOpen=false;this.selected=-1;this.changed();}
  selectValue(index){if(this.eraseTask)return;this.values[this.attribute]=index;this.selectAttribute(this.attribute,false);}
  selectClass(index){if(this.eraseTask)return;if(!this.availableClasses().has(index))return;this.speak(1008);this.interact();this.category=index;this.factOpen=false;this.selected=-1;this.changed();}
  toggleTime(){if(this.eraseTask)return;this.speak(1042);this.interact();this.time=1-this.time;this.category=-1;this.factOpen=false;this.selected=-1;this.drag=null;for(const o of this.objects[this.time])this.schedule(o);this.changed();}
  selectAnimal(id){if(this.eraseTask)return;this.speak(1008);this.interact();this.selected=id;this.factIndex=this.random(Math.max(1,this.facts().length));this.factOpen=true;this.changed();}
  nextFact(){if(this.eraseTask)return;this.factIndex++;this.factOpen=true;this.changed();}
  dismissFact(){if(this.eraseTask)return;this.speak(1008);this.factOpen=false;this.changed();}
  get randomState(){return gameplayRandom.seed;}
  set randomState(value){gameplayRandom.reset(value);}
  random(max){return gameplayRandom.pick(max);}
  schedule(object){object.due=this.tick+(object.blink?30+this.random(120):120+this.random(360));}
  addAnimal(id,x=210,y=115){
    if(this.objects[this.time].length>=40){this.announce("This scene has 40 animals. Remove one to add another.");return null;}
    const a=this.tables.animals[id],s=this.store.shape("modules",a.large);
    const object={id,x:Math.max(131,Math.min(315-s.w,x-Math.floor(s.w/2))),y:Math.max(5,Math.min(195-s.h,y-Math.floor(s.h/2))),blink:0,due:0};
    this.schedule(object);this.objects[this.time].push(object);this.interact();this.changed();return object;
  }
  clear(){this.undo={time:this.time,objects:this.objects[this.time]};this.objects[this.time]=[];this.changed();this.announce("Scene cleared. Undo is available.");}
  requestClear(all=false){
    if(this.eraseTask)return;this.speak(1008);const count=all?this.objects[0].length+this.objects[1].length:this.objects[this.time].length;
    if(!count){this.confirm('No animals to send home!',null);return;}
    this.confirm(all?'Send daytime AND nighttime animals home?':'Send all animals home?',()=>{
      this.undo={scenes:this.objects.map(list=>list.slice())};
      if(all){this.objects=[[],[]];this.changed();}else{this.eraseTask=this.eraseAnimals();this.eraseDue=this.tick;this.stepErase();}
    });
  }
  *eraseAnimals(){
    const list=this.objects[this.time];while(list.length){const object=list.pop(),shape=this.store.shape('modules',this.tables.animals[object.id].large),x=object.x+Math.floor(shape.w/2),y=object.y+Math.floor(shape.h/2);this.eraseEffect={object,id:923,x,y};yield 4;this.eraseEffect.id=924;this.speak(10034);yield 4;this.eraseEffect.id=925;yield 4;this.eraseEffect=null;}this.announce('Animals sent home. Undo is available.');
  }
  stepErase(){if(!this.eraseTask||this.tick<this.eraseDue)return false;const step=this.eraseTask.next();if(step.done){this.eraseTask=null;this.changed();}else this.eraseDue=this.tick+step.value;return true;}
  undoClear(){if(this.eraseTask)return;if(this.undo){if(this.undo.scenes)this.objects=this.undo.scenes;else this.objects[this.undo.time]=this.undo.objects;this.undo=null;this.changed();}}
  enterQuiz(){if(this.eraseTask)return;this.endDrag();this.mode="quiz";this.quiz.options=true;this.quiz.robotDue=null;this.changed();}
  leaveQuiz(){if(this.quiz.interruptWait())return;this.quiz.stopReminder();if(this.quiz.busy||this.quiz.winAnimation&&!this.quiz.winAnimation.done)return;this.mode="explore";this.quiz.robotDue=null;this.changed();}
  update(tick){this.tick=tick;if(this.eraseTask)return this.stepErase();if(this.mode==="quiz")return this.quiz.update(tick);if(tick<this.idleUntil||this.drag)return false;let changed=false;
    for(const object of this.objects[this.time])if(tick>=object.due){object.blink=1-object.blink;this.schedule(object);changed=true;}return changed;}
  hit(b,x,y){return x>=b[1]&&x<b[3]&&y>=b[0]&&y<b[2];}
  thumbnails(){let x=8,y=107,rowHeight=0;return this.animals().map(a=>{
    const s=this.store.shape("modules",a.small);if(x+s.w>122){x=8;y+=rowHeight;rowHeight=0;}
    const item={animal:a,rect:[y,x,y+s.h,x+s.w]};x+=s.w+1;rowHeight=Math.max(rowHeight,s.h);return item;});}
  beginDrag(x,y){
    if(this.mode==="quiz"||this.eraseTask)return false;
    const objects=this.objects[this.time];
    for(let i=objects.length-1;i>=0;i--){const o=objects[i],s=this.store.shape("modules",this.tables.animals[o.id].large);if(this.hit([o.y,o.x,o.y+s.h,o.x+s.w],x,y)){
      objects.splice(i,1);objects.push(o);this.interact();this.factOpen=false;this.changed();this.drag={object:o,start:[x,y],origin:[o.x,o.y],fresh:false};return true;}}
    for(const item of this.thumbnails())if(this.hit(item.rect,x,y)){
      this.selectAnimal(item.animal.id);const o=this.addAnimal(item.animal.id,x,y);if(!o)return true;
      const s=this.store.shape("modules",item.animal.large);o.x=Math.round(x)-Math.floor(s.w/2);o.y=Math.round(y)-Math.floor(s.h/2);
      this.drag={object:o,start:[x,y],origin:[o.x,o.y],fresh:true};return true;}return false;
  }
  moveDrag(x,y){if(!this.drag)return false;const d=this.drag,s=this.store.shape("modules",this.tables.animals[d.object.id].large);
    d.object.x=Math.max(0,Math.min(320-s.w,d.origin[0]+Math.round(x-d.start[0])));d.object.y=Math.max(0,Math.min(200-s.h,d.origin[1]+Math.round(y-d.start[1])));return true;}
  endDrag(){if(!this.drag)return;const {object:o,fresh}=this.drag,a=this.tables.animals[o.id],s=this.store.shape("modules",a.large);this.drag=null;
    if(o.x+s.w<=131||o.x>=315||o.y+s.h<=5||o.y>=195){const list=this.objects[this.time];list.splice(list.indexOf(o),1);if(!fresh)this.speak(10034);}
    else{o.x=Math.max(131,Math.min(315-s.w,o.x));o.y=Math.max(5,Math.min(195-s.h,o.y));if(!fresh)this.schedule(o);}
    this.interact();this.changed();}
  click(x,y,modifiers={}){if(this.eraseTask)return;if(this.mode==="quiz"){this.quiz.click(x,y);return;}const r=this.tables.rectangles;this.interact();
    for(let i=0;i<7;i++)if(this.hit(r[i+1],x,y)){this.selectAttribute(i);return;}
    if(this.hit(r[12],x,y)){this.selectAttribute(this.attribute);return;}
    if(this.factOpen&&this.hit(r[26],x,y)){this.dismissFact();return;}
    for(let i=0;i<10;i++)if(this.hit(r[14+i],x,y)){this.selectClass(i);return;}
    if(this.hit(r[13],x,y)){this.toggleTime();return;}
    if(this.hit(r[10],x,y)){this.requestClear(!!modifiers.ctrlKey);return;}
    if(this.hit(r[9],x,y)){this.print();return;}
    if(this.hit(r[11],x,y)){this.enterQuiz();return;}
  }
  draw(surface){
    if(this.mode==="quiz"){this.quiz.draw(surface);return;}
    const s=this.store,r=this.tables.rectangles,pal=s.palette("modules",5650).rgba;
    const draw=(id,palette,x,y,mode=10,clip=null)=>surface.draw(s,"modules",id,palette,x,y,mode,clip);
    const fill=(b,c)=>surface.rect(b[1],b[0],b[3]-b[1],b[2]-b[0],c);
    const center=(id,b,palette=5650,color=null)=>{if(color!==null)fill(b,color);const shape=s.shape("modules",id);draw(id,palette,Math.floor((b[1]+b[3])/2)-Math.floor(shape.w/2),Math.floor((b[0]+b[2])/2)-Math.floor(shape.h/2));};
    const width=value=>[...value].reduce((n,c)=>n+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);
    const text=(value,b)=>surface.text(s,value,Math.floor((b[1]+b[3])/2)-Math.floor(width(value)/2),Math.floor((b[0]+b[2])/2)-4);
    draw(5401,5400,0,0,2);
    for(let i=0;i<7;i++)center(5651+i,r[i+1],5650,pal[i===this.attribute?8:2]);
    text(this.factOpen?this.name(this.selected):this.valueNames()[this.values[this.attribute]],r[12]);
    const available=this.availableClasses();
    for(let i=0;i<10;i++){
      if(!available.has(i)){fill(r[14+i],0xffaaaaaa);continue;}
      let substitute=-1;const v=this.values[this.attribute];
      if(this.time===1&&i===0&&((this.attribute===3&&v===1)||(this.attribute===2&&v===0)))substitute=60;
      if(this.time===1&&i===7&&this.attribute===4&&v===4)substitute=70;
      if(this.time===0&&i===0&&this.attribute===3&&v===1)substitute=63;
      if(this.time===0&&i===6&&((this.attribute===3&&v===2)||(this.attribute===4&&v===1)))substitute=79;
      const animal=substitute>=0?this.tables.animals[substitute]:null;
      center(animal?animal.small:this.tables.class_icons[this.time][i],r[14+i],animal?animal.palette:5650,i===this.category?pal[8]:0xffffffff);
    }
    if(this.category>=0)text(this.classNames()[this.category],[99,6,108,124]);
    for(const item of this.thumbnails()){const a=item.animal;if(this.factOpen&&this.selected===a.id){
      // Main 0x6B21 fills the union of two inset rectangles, preserving corners.
      const[t,l,b,r]=item.rect;surface.rect(l+1,t,r-l-2,b-t,pal[8]);surface.rect(l,t+1,r-l,b-t-2,pal[8]);
    }draw(a.small,a.palette,item.rect[1],item.rect[0]);}
    if(this.factOpen){fill(r[26],0xffffffff);let y=49,line="";for(const word of this.fact().split(" ")){
      if(line&&width(line+" "+word)>120){surface.text(s,line,5,y,0xff000000,s.data.font,0,r[26]);y+=10;line=word;}else line+=(line?" ":"")+word;}
      if(line)surface.text(s,line,5,y,0xff000000,s.data.font,0,r[26]);}
    for(let i=0;i<3;i++)center(5659+i,r[9+i],5650,pal[2]);
    if(this.time===0)draw(5501,5500,127,4);
    else{draw(5501,5501,127,4,10,[39,127,196,317]);draw(5511,5510,128,4);}
    for(const o of this.objects[this.time]){if(this.drag?.object===o)continue;const a=this.tables.animals[o.id];draw(a.large+o.blink,a.palette,o.x,o.y);}
    surface.draw(s,"th",8,6,304,1);
    if(this.drag){const o=this.drag.object,a=this.tables.animals[o.id];draw(a.large,a.palette,o.x,o.y);}
    if(this.eraseEffect){const e=this.eraseEffect;if(e.id===923){const o=e.object,a=this.tables.animals[o.id];draw(a.large,a.palette,o.x,o.y);}const shape=s.shape('th',e.id);surface.draw(s,'th',e.id,900,e.x-Math.floor(shape.w/2),e.y-Math.floor(shape.h/2));}
  }
}
