"use strict";
// Overlay 1 4E3A and character scripts 20300/20301: piano/maze transfer.
class MazeTransition {
  constructor(store,{character,returning,tick,sound,complete}){
    Object.assign(this,{store,character,returning,tick,sound,complete});
    this.phase=returning?'bucket':'cloud';this.begin();
  }
  get hidePointer(){return this.phase==='bucket';}
  begin(){
    this.start=this.tick;
    if(this.phase==='cloud'){this.frame=0;this.sound(10034);}
    else{this.actor=new Animation(this.store,this.character,20300+Number(this.returning),20300,{startTick:this.tick});this.actor.update(this.tick);}
  }
  interrupt(){}
  update(tick){
    this.tick=tick;
    if(this.phase==='cloud'){this.frame=Math.floor((tick-this.start)/8);if(this.frame<8)return;}
    else{this.actor.update(tick);if(!this.actor.done)return;}
    if(this.phase===(this.returning?'cloud':'bucket')){this.complete();return;}
    this.phase=this.returning?'cloud':'bucket';this.begin();
  }
  draw(surface,base){
    const visible=this.phase==='cloud'&&(this.returning?this.frame>=4:this.frame<4);
    base({instrumentVisible:visible});
    if(this.phase==='bucket')this.actor.draw(surface);
    else{
      if(this.returning&&this.frame<4)this.actor.draw(surface);
      const[y,x]=this.store.data.music.maze_cloud_positions[this.frame];surface.draw(this.store,'modules',2381+this.frame,2380,x,y,10);
    }
  }
}

// Resident 5204/530D: teleport ring, activity bubble and backing callbacks5442.
// Each stage executes the original SCR. Saved screen captures are never assets.
class RoomTransition {
  constructor(store,{variant,returning=false,tick,speak,stopSound,complete}){
    Object.assign(this,{store,variant,returning,tick,speak,stopSound,complete});
    this.phase='opening';this.childVisible=!returning;this.openInlet=returning&&variant===3;
    this.soundDue=tick;this.speak(1015);this.play(980,980);
  }
  play(id,palette){
    this.actor=new Animation(this.store,'th',id,palette,{startTick:this.tick,onSound:id=>{this.soundDue=this.tick+(this.speak(id)||0);},onCallback:(slot,arg)=>{if(slot===0)this.childVisible=!!arg;},onDisplay:()=>{this.displayChild=this.childVisible;}});
    // Callback5442 changes the hidden backing. C78A presents that backing with
    // the next displayed composition, never with the preceding frame's slots.
    this.actor.update(this.tick);
  }
  get hidePointer(){return this.phase!=='entry-pause';}
  interrupt(){if(['sound-tail','board-pause','entry-pause'].includes(this.phase)){this.stopSound();this.soundDue=this.due=this.tick;}}
  update(tick){
    this.tick=tick;
    if(this.phase==='entry-pause'){if(tick>=this.due)this.complete();return;}
    if(this.phase==='board-pause'){if(tick>=this.due){this.openInlet=false;if(this.returning)this.complete();else{this.phase='entry-pause';this.due=tick+60;}}return;}
    if(this.phase==='sound-tail'){if(tick>=this.soundDue)this.endTransfer();return;}
    this.actor.update(tick);if(!this.actor.done)return;
    if(this.phase==='opening'){
      if(this.returning)this.stopSound();
      if(this.variant===3)this.openInlet=true;
      this.phase='transfer';this.play(1100+this.variant+4*Number(this.returning),1100);
    }else if(this.phase==='transfer'){
      this.phase='sound-tail';if(tick>=this.soundDue)this.endTransfer();
    }else if(this.phase==='closing'){
      this.actor=null;this.phase='board-pause';this.due=tick+(this.variant===3?60:0);if(this.variant!==3)this.complete();
    }
  }
  endTransfer(){
    this.stopSound();this.actor=null;
    if(this.returning){this.phase='closing';this.play(981,980);}
    else if(this.variant===3){this.phase='board-pause';this.due=this.tick+60;}
    else{this.phase='entry-pause';this.due=this.tick+60;}
  }
  draw(surface,base,resident){
    const transferring=this.phase==='transfer'||this.phase==='sound-tail';
    base({characterVisible:false,curtainVisible:!(transferring&&this.variant===2)});
    if(this.openInlet)surface.draw(this.store,'th',927,900,160,184);
    if(this.phase==='opening'||this.phase==='closing')this.actor.draw(surface);
    else if(this.phase!=='board-pause'||!this.returning)surface.draw(this.store,'th',986,980,150,162);
    if(this.actor?this.displayChild:this.childVisible)resident.draw(surface);
    if(transferring)this.actor.draw(surface);
    const bounds=transferring?this.actor.script.bounds:[162,150,174,197];
    resident.drawObjects(surface,true,{clip:bounds,minBottom:transferring?168:0});
  }
}
