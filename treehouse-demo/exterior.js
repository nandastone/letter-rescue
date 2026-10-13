"use strict";
// Exterior scene4 and squirrel close-up scene14, resident ACE and3D39.
class TreehouseExterior {
  constructor(store,resident,room,{sound,stopSound,changed,leave}){
    Object.assign(this,{store,resident,room,sound,stopSound,changed,leave});this.credit=0;this.creditDue=600;this.nuts=[];
    this.hotspots=[[2,45,52,122],[64,232,184,290],[78,132,106,164],[128,202,160,230],[177,14,200,92],[6,5,35,38],[33,217,64,258],[105,80,184,128],[109,128,188,174]];
    this.hollowHotspots=[[81,138,109,184],[95,102,126,148],[131,206,164,263],[26,154,73,224],[18,82,198,271]];
  }
  fresh(tick){this.credit=0;this.creditDue=tick+600;}
  update(tick){if(!this.resident.selected&&tick>=this.creditDue){this.credit=(this.credit+1)%8;this.creditDue=tick+(this.credit===0?600:360);return true;}return false;}
  drawCloud(surface){const shape=this.store.shape('th',171+this.room.cloud);surface.draw(this.store,'th',171+this.room.cloud,170,83-Math.floor(shape.w/2),27-Math.floor(shape.h/2));}
  drawCredits(surface){const [x,y]=[[12,60],[12,55],[10,52],[10,52],[10,52],[26,50],[24,49],[27,57]][this.credit];surface.blit(this.store.shape('th',10+this.credit),[0,0xff000000],x,y);}
  click(x,y){
    if(this.resident.busy)return true;
    const i=this.hotspots.findIndex(r=>this.resident.hit(r,x,y));
    if(!this.resident.selected)return i===1?'ladder':i===7?'boy':i===8?'girl':null;
    if(i===0){this.room.cloud=(this.room.cloud+1)%7;this.sound(1044);this.changed();}
    else if(i===1)return 'ladder';
    else if(i===2)this.resident.playAmbient(1060,1060);
    else if(i===3)return 'hollow';
    else if(i===4){this.resident.playAmbient(1000+this.resident.outsideCycle,1000);this.resident.outsideCycle=(this.resident.outsideCycle+1)%3;}
    else if(i===5)this.resident.playAmbient(1301,1300);
    else if(i===6)this.resident.windowStatus();
    return null;
  }
  enterHollow(){this.nuts=[];this.signWaiting=false;}
  // Hollow interactions return directly to their loop without resetting yard timers.
  hollowClick(x,y){
    if(this.resident.busy){if(this.signWaiting){this.resident.objectDue=this.resident.tick;this.resident.stepObject();}return;}
    const i=this.hollowHotspots.findIndex(r=>this.resident.hit(r,x,y));
    if(i<0){this.leave();return;}
    if(i<2){const duration=this.sound(1019);this.resident.playAmbient(i===0?1401:1400,1400,null,duration,{resetAmbient:false});}
    else if(i===2&&this.nuts.length<3)this.resident.runObject(this.toss(),{resetAmbient:false});
    else if(i===3)this.resident.runObject(this.readSign(),{resetAmbient:false});
  }
  *readSign(){this.signWaiting=true;yield this.sound(20001)||1;this.stopSound();this.signWaiting=false;}
  *toss(){const point=[[220,99],[195,77],[219,78]][this.nuts.length];this.sound(10035);yield* this.resident.flight([234,140],point,[937,937],930,{delay:8,step:12});this.sound(10033);this.nuts.push(point);this.changed();}
  drawHollow(surface){surface.draw(this.store,'th',1448,1400,0,0,2);for(const [x,y]of this.nuts)surface.draw(this.store,'th',1447,1400,x-4,y-4);this.resident.drawObjectMotion(surface);surface.draw(this.store,'th',8,6,304,1);}
}
