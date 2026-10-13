"""Read-only call observation for ordinary browser input journeys."""

def install(page):
    page.evaluate('''()=>{window.soundEvents=[];window.soundCheckpoint='initial';window.soundClockOrigin=tick;
      const start=audio.start,stop=audio.stop;
      audio.start=function(...args){const id=start.apply(this,args);if(id!==null){const v=this.active.get(id);soundEvents.push({type:'start',tick,key:v.key,id,rate:v.rate,when:args[2]??null,checkpoint:soundCheckpoint,scene});}return id;};
      audio.stop=function(id,...args){if(this.active.has(id))soundEvents.push({type:'stop',tick,id,key:this.active.get(id).key,when:args[0]??null,checkpoint:soundCheckpoint,scene});return stop.call(this,id,...args);};
    }''')

def checkpoint(page,name):page.evaluate('name=>{soundCheckpoint=name;}',name)

def collect(page,report):
    report['sound_events']=page.evaluate('soundEvents')
    report['sound_clock_origin']=page.evaluate('soundClockOrigin')
    report['sound_observation_scope']='Unchanged production start/stop calls and returned voice IDs during the input-driven journey. Game-tick positions measure dispatch, not actual rendered waveform or native sample-time parity.'
