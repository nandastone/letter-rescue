"use strict";
// Calendar and clock geometry from resident 0x2F86, 0x341E, 0x3515, 0x3F44.
class TreehouseRoom {
  constructor(store,{changed,announce,speak=()=>0,stopSound=()=>{},animate=null,balloon=null,now=()=>new Date(),calendarComplete=()=>{},environmentComplete=()=>{}}){Object.assign(this,{store,changed,announce,speak,stopSound,animate,balloon,now,calendarComplete,environmentComplete});this.date=new Date(now());this.cloud=5;this.cloudX=195;this.height=28;this.target=28;this.due=0;this.tick=0;this.pendingDate=null;this.minute='';this.environment=null;this.pendingEnvironment=null;this.chirpUntil=0;this.chirpStart=0;this.speech=[];this.speechDue=0;this.clearDue=0;}
  get busy(){return !!(this.height!==this.target||this.calendarRead||this.question||this.environment||this.pendingEnvironment||this.chirpUntil>this.tick);}
  enter(tick){this.tick=tick;this.cloudDue=tick+300;}
  get open(){return this.target===98;}
  get dateLabel(){const months=this.store.data.strings['th:500'];return `${months[this.date.getMonth()]} ${this.date.getDate()}, ${this.date.getFullYear()}`;}
  get story(){const values=this.store.data.strings[`th:${1001+this.date.getMonth()}`],i=2*(this.date.getDate()-1);return {heading:values[i]||'',body:values[i+1]||''};}
  slide(target){this.target=target;this.due=this.tick+2;if(this.height!==target){this.speak(10031);this.sliding=true;}}
  toggle(){this.slide(this.open?28:98);this.changed();}
  browse(delta){const date=new Date(this.date);date.setDate(date.getDate()+delta);if(date<new Date(1980,0,1))return;this.chooseDate(date);}
  chooseDate(date){if(this.height>28){this.pendingDate=new Date(date);this.slide(28);}else{this.date=new Date(date);this.readCalendar();}this.changed();}
  readCalendar(){this.sayDate();this.calendarRead=true;this.calendarReadOpen=!this.open;this.changed();}
  nextCloud(){if(this.height>28||this.open)return;this.cloud=(this.cloud+1)%7;this.cloudX=223-Math.floor(this.store.shape('th',171+this.cloud).w/2);this.changed();}
  // Resident CD40/CEC3/D166 concatenate the original voice fragments. Numbers
  // in a speech queue are resource IDs; arrays contain explicit tick pauses.
  say(queue,complete=null){this.speech=queue.slice();this.speechComplete=complete;this.speechDue=this.tick;this.serviceSpeech();}
  serviceSpeech(){if(this.tick<this.speechDue)return false;if(!this.speech.length){const complete=this.speechComplete;this.speechComplete=null;complete?.();if(this.portraitFrame===932){this.portraitFrame=931;return true;}return !!complete;}const part=this.speech.shift();this.portraitFrame=Array.isArray(part)||part?.mouth===false?931:932;this.speechDue=this.tick+(Array.isArray(part)?part[0]:this.speak(typeof part==='object'?part.sound:part));return true;}
  numberSpeech(value,leadingZero=false){const tens=[30,0,20,13,14,15,6,7,8,19],teens=[10,11,12,13,14,15,6,7,8,19],out=[];if(!value)return [[5]];if(value>=10&&value<20){out.push(11000+teens[value%10]);if(value>=13)out.push([5],11027);}else{if(value>=20||leadingZero)out.push(11000+tens[Math.floor(value/10)],[5]);if(value>=20)out.push(11022,[5]);out.push(11000+value%10);if(value%10===8)out.push(11021);}return [...out,[5]];}
  sayTime(date=this.now(),wake=false,complete=null){const hour=date.getHours()%12||12;this.say([...(wake?[11028,[15],11026]:[11023]),[15],11000+hour,...(hour===8?[11021]:[]),[20],...this.numberSpeech(date.getMinutes(),true),[20],11024+Number(date.getHours()>=12)],complete);}
  sayDate(){const day=this.date.getDate(),teens=[10,11,12,13,14,15,6,7,8,19],out=[11120+this.date.getDay(),[30],11100+this.date.getMonth(),[12]];if(day<=12)out.push(11129+day);else if(day<20)out.push(11000+teens[day%10],[5],11142);else{out.push(day<30?11020:11013);if(day%10===0)out.push(11143);else out.push(11022,[5],11129+day%10);}this.say(out);}
  interact(kind){if(this.busy)return false;if((kind==='nest'||kind==='chirp')&&(this.open||this.height>28))return false;this.slide(28);this.pendingEnvironment=kind;this.clearDue=this.tick;this.changed();return true;}
  beginEnvironment(){const kind=this.pendingEnvironment,b=this.balloon,r=kind==='spider'?[0,0,84,283]:kind==='nest'?[74,207,104,281]:[81,237,94,260];if(b&&!b.hidden&&b.x<r[3]&&b.x+29>r[1]&&b.y<r[2]+2&&b.y+38>r[0]-2){if(this.tick>=this.clearDue){b.y+=kind==='spider'?2:-2;this.clearDue=this.tick+2;}return;}this.pendingEnvironment=null;if(kind==='chirp'){this.chirpStart=this.tick;this.chirpUntil=this.tick+Math.min(180,this.speak(1041));}else if(this.animate)this.environment=this.animate(kind==='spider'?1080:1250);}
  finishEnvironment(){this.stopSound();this.environment=null;this.environmentComplete();}
  interruptAudio(){if(!this.environment?.done||this.tick>=this.environment.soundDue)return false;this.finishEnvironment();this.changed();return true;}
  leave(){this.sliding=false;this.calendarRead=false;this.pendingDate=null;this.environment=null;this.pendingEnvironment=null;this.chirpUntil=0;this.speech=[];this.speechComplete=null;this.question=null;this.blank=false;}
  updateCloud(){if(this.open||this.height!==28||this.busy||this.tick<this.cloudDue)return false;if(++this.cloudX>283){this.cloud=(this.cloud+1)%7;this.cloudX=163-this.store.shape('th',171+this.cloud).w;}this.cloudDue=this.tick+300;return true;}
  update(tick,modal=false){this.tick=tick;let dirty=false;const now=this.now(),minute=`${now.getHours()}:${now.getMinutes()}`;if(minute!==this.minute){this.minute=minute;dirty=true;}
    if(!modal&&this.updateCloud())dirty=true;
    if(this.height!==this.target&&!this.sliding){this.speak(10031);this.sliding=true;}
    if(tick>=this.due&&this.height!==this.target){this.height+=Math.sign(this.target-this.height)*10;this.due=tick+2;dirty=true;if(this.height===this.target){this.stopSound();this.sliding=false;if(this.height===28)this.cloudDue=tick+300;if(this.height===28||!this.question)this.calendarComplete(this.height===98);}if(this.height===28&&this.pendingDate){this.date=this.pendingDate;this.pendingDate=null;this.readCalendar();this.changed();}if(this.height===this.target)this.changed();}
    if(this.height===28&&this.pendingEnvironment){this.beginEnvironment();dirty=true;}
    if(this.environment){this.environment.update(tick);if(this.environment.done&&tick>=(this.environment.soundDue??tick))this.finishEnvironment();dirty=true;}
    if(this.chirpUntil){dirty=true;if(tick>=this.chirpUntil){this.chirpUntil=0;this.environmentComplete();}}
    if(this.serviceSpeech())dirty=true;
    if(this.calendarRead&&!this.speech.length&&tick>=this.speechDue){this.calendarRead=false;if(this.calendarReadOpen)this.slide(98);this.changed();dirty=true;}return dirty;
  }
  drawEnvironment(surface){if(this.environment){if(this.environment.id===1250)surface.rect(211,81,70,23,0xffffe3c3);this.environment.draw(surface);}if(this.chirpUntil>this.tick)surface.draw(this.store,'th',920+Math.floor((this.tick-this.chirpStart)/8)%2,900,241,82);}
  drawCloud(surface){const s=this.store,shape=s.shape('th',171+this.cloud);surface.draw(s,'th',171+this.cloud,170,this.cloudX,55-Math.floor(shape.h/2),10,[30,163,80,283]);}
  drawPortrait(surface){if(this.portraitFrame)surface.draw(this.store,'th',this.portraitFrame,930,25,43,2);}
  drawDateClock(surface){
    const s=this.store,label=this.dateLabel,width=[...label].reduce((n,c)=>n+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);surface.rect(58,24,76,11,0xffffffff);surface.text(s,label,96-Math.floor(width/2),25,0xff5555ff);
    const now=this.now(),hour=now.getHours()%12||12,minute=now.getMinutes();surface.rect(92,108,22,10,0xff000000);for(const[id,x]of [[hour>9?1227:1226,95],[1215+hour%10,97],[1225,102],[1215+Math.floor(minute/10),104],[1215+minute%10,109]])surface.draw(s,'th',id,1200,x,110,2);
  }
  drawCalendar(surface){const s=this.store,clip=[28,162,this.height,283];if(this.height>28){surface.rect(162,28,121,this.height-28,0xffffffff);if(!this.blank){const {heading,body}=this.story,width=value=>[...value].reduce((n,c)=>n+(s.data.font[c.charCodeAt(0)]?.[0]||4),0);surface.text(s,heading,222-Math.floor(width(heading)/2),28,0xff000000,s.data.font,0,clip);let line='',lines=[];for(const word of body.split(' ')){const next=line?line+' '+word:word;if(width(next)>118&&line){lines.push(line);line=word;}else line=next;}if(line)lines.push(line);lines.forEach((value,i)=>surface.text(s,value,164,39+10*i,0xff000000,s.data.font,0,clip));}}surface.draw(s,'th',1201,1200,162,this.height);}
}
