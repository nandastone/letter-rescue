"""Original loop bounds and source-defined owner cleanup using real Web Audio nodes."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        page.evaluate('async()=>{await audio.unlock();resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;}')
        def check(name,code):
            try:report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
            except Exception as e:report['checks'].append(dict(name=name,passed=False,error=str(e)))
        for sound in [1002,1013,1015,1018,1022,1036,10000,10001,10014,10017,10031,10043,10048]:
            check(f'{sound}: zero loop end means complete sample',f'()=>{{const id=audio.start("digisnd:{sound}"),v=audio.active.get(id);return !!v&&v.source.loop&&v.source.loopStart===0&&v.source.loopEnd===v.source.buffer.duration;}}')
        check('finite playback suppresses resource looping','()=>{const id=audio.start("digisnd:1002",null,null,{loop:false});return !audio.active.get(id).source.loop;}')
        check('stop by sound ID leaves a different sound alone','()=>{const id=audio.start("digisnd:1013");audio.stopSound(1002);const kept=audio.active.has(id);audio.stopSound(1013);return kept&&!audio.active.size;}')
        check('new digital sample replaces prior looping channel','()=>{const old=audio.start("digisnd:1013"),next=audio.start("digisnd:1002");return !audio.active.has(old)&&audio.active.has(next)&&audio.active.size===1;}')
        check('accepted room input stops the sustained radio','()=>{setScene("inside");activate(125,136,"test");const on=[...audio.active.values()].some(v=>v.key==="digisnd:1013");activate(315,110,"test");return on&&!audio.active.size;}')
        check('calendar stops at both endpoints','()=>{room.height=room.target=28;for(const end of [98,28]){room.toggle();if(![...audio.active.values()].some(v=>v.key==="digisnd:10031"))return false;for(let i=0;i<30&&room.height!==room.target;i++)advance();if(room.height!==end||audio.active.size)return false;}return true;}')
        for kind in [0,1,5]:
            check(f'object {kind}: departure stops its flight loop',f'()=>{{const o=resident.create({kind});resident.clickObject(o);for(let i=0;i<4000&&resident.busy;i++)advance();return !resident.busy&&!resident.objects.includes(o)&&!audio.active.size;}}')
        check('food sound stops after its 480-tick wait','()=>{const o=resident.create(16,false);resident.runObject(resident.consumeFood(o));advance(479);const active=audio.active.size===1&&resident.objects.includes(o);advance();return active&&!resident.busy&&!resident.objects.includes(o)&&!audio.active.size;}')
        check('food wait accepts input interruption and stops sound','()=>{const o=resident.create(16,false);resident.runObject(resident.consumeFood(o));advance(20);activate(315,110,"test");return !resident.busy&&!resident.objects.includes(o)&&!audio.active.size;}')
        check('alien telescope replay stops final whole-sample loop','()=>{setScene("telescope");telescope=1;startTelescopeAnimation(true);for(let i=0;i<3000&&animations.some(a=>!a.done);i++)advance();return animations.every(a=>a.done)&&!audio.active.size;}')
        check('maze rollers stop before outward pause and after return','()=>{setScene("maze");maze.cancel();maze.setupRound();const old=maze.stopSound,calls=[];maze.stopSound=id=>{calls.push({id,tick,roller:maze.roller});old(id);};maze.run(maze.reward());for(let i=0;i<2000&&maze.busy;i++)advance();maze.stopSound=old;return calls.length===2&&calls[0].roller===76&&calls[1].roller===60&&!audio.active.size;}')
        for role in [0,1,2]:
            check(f'nature role {role}: question/guess/retreat wrapper stops audio',f'()=>{{setScene("nature");const q=nature.quiz;q.player={int(role!=0)};q.opponent={role};for(const index of [0,3,8,9]){{q.run(q.perform(index));for(let i=0;i<2000&&q.busy;i++)q.update(q.tick+1);if(q.busy||audio.active.size)return false;}}return true;}}')
        check('instrument illustration suppresses its embedded effect channel','()=>{setScene("music");for(const entry of music.instruments){instrument=entry.id;auditionInstrument();for(let i=0;i<3000&&audition&&!audition.done;i++){advance();if([...audio.active.values()].some(v=>v.key.startsWith("digisnd:")))return false;}if(audio.active.size||!audition.done)return false;}return true;}')
        check('character final display waits for audio and consumes skip input','()=>{setScene("inside");resident.pose=0;const old=resident.sound;let finished=false;resident.sound=()=>10000;resident.action(23,()=>finished=true);for(let i=0;i<5000&&!resident.active.done;i++)advance();const waiting=resident.busy&&!finished&&resident.active.done;activate(50,185,"test");resident.sound=old;return waiting&&finished&&!resident.busy&&scene==="inside"&&!roomTravel;}')
        check('ordinary SCR body cannot be skipped by tail input','()=>{resident.action(19);const active=resident.active;activate(50,185,"test");const held=resident.active===active&&!active.done&&!roomTravel;for(let i=0;i<5000&&resident.busy;i++)advance();return held&&!resident.busy;}')
        check('spider final display waits and consumes navigation input','()=>{room.environment=animation("th",1080,1080,{onSound:()=>{}});room.environment.soundDue=tick+10000;for(let i=0;i<5000&&!room.environment.done;i++)advance();const waiting=room.busy&&room.environment.done;navigateScene("outside");return waiting&&!room.busy&&scene==="inside";}')
        check('exterior gag retains final frame through finite sound tail','()=>{setScene("outside");const old=resident.sound;resident.sound=()=>10000;resident.playAmbient(1060,1060);for(let i=0;i<5000&&!resident.ambientAnimation.done;i++)advance();const waiting=resident.busy&&resident.ambientAnimation.done;activate(246,80,"test");resident.sound=old;return waiting&&!resident.busy&&scene==="outside";}')
        check('exterior food wrapper forces stop at script completion','()=>{const old=resident.sound;resident.sound=()=>10000;const food=resident.create(16,false);resident.playAmbient(1300,1300,food);for(let i=0;i<5000&&resident.busy;i++)advance();resident.sound=old;return !resident.busy&&!resident.objects.includes(food)&&!audio.active.size;}')
        check('window opening and closing suppress script sounds','()=>{const old=resident.sound,calls=[];resident.sound=id=>{calls.push({id,script:resident.windowAnimation?.id});return 1;};resident.runObject(resident.windowScene(7));for(let i=0;i<5000&&resident.busy;i++)advance();resident.sound=old;return !resident.busy&&calls.length>0&&calls.every(c=>c.script===20407);}')
        check('muted sample requests do not invent audio waits','()=>{audio.enabled=false;const duration=theaterSpeech(1013);audio.enabled=true;return duration===0&&!audio.active.size;}')
        check('hollow squirrel waits for the externally started sound','()=>{setScene("hollow");const old=exterior.sound;exterior.sound=()=>10000;activate(160,90,"test");for(let i=0;i<5000&&!resident.ambientAnimation.done;i++)advance();const waiting=resident.busy&&resident.ambientAnimation.done;activate(10,190,"test");exterior.sound=old;return waiting&&!resident.busy&&scene==="hollow";}')
        check('empty robot shelf retains its first frame silently','()=>{setScene("telescope");rewards.shelf.fill(false);telescope=3;audio.stopAll();startTelescopeAnimation();return animations[0].done&&!telescopeBusy()&&!audio.active.size;}')
        check('earned robot shelf plays on arrival with four original cues','()=>{rewards.shelf[0]=true;const old=audio.start,cues=[];audio.start=function(key,...args){cues.push(key);return old.call(this,key,...args);};startTelescopeAnimation();const starts=telescopeBusy();for(let i=0;i<5000&&telescopeBusy();i++)advance();audio.start=old;return starts&&!telescopeBusy()&&cues.length===4&&cues.every(k=>k==="digisnd:10024")&&!audio.active.size;}')
        check('telescope body blocks replay and leaving','()=>{startTelescopeAnimation(true);const a=animations[0];activate(160,100,"test");navigateScene("inside");const kept=scene==="telescope"&&animations[0]===a&&!a.done;for(let i=0;i<5000&&telescopeBusy();i++)advance();return kept&&!telescopeBusy();}')
        check('robot shelf final sound wait consumes input','()=>{startTelescopeAnimation(true);const a=animations[0];for(let i=0;i<5000&&!a.done;i++)advance();a.tailWait=true;a.soundDue=tick+10000;activate(310,5,"test");return scene==="telescope"&&!a.tailWait&&!audio.active.size;}')
        check('audio completion preserves fractional time before native countdowns','()=>{setScene("nature");const q=nature.quiz,starts=[];q.player=0;q.tick=0;q.run((function*(){for(let i=0;i<3;i++){starts.push(q.tick);yield* q.changeCandidate(i,false);yield 18;}})());for(let t=1;t<120&&q.busy;t++)q.update(t);return JSON.stringify(starts)==="[0,31,62]";}')
        check('interrupting a candidate sound starts the next countdown now','()=>{const q=nature.quiz;let end=null;q.tick=0;q.run((function*(){yield* q.changeCandidate(0,false);yield 18;end=q.tick;})());q.update(5);q.interruptWait();for(let t=6;t<40&&q.busy;t++)q.update(t);return end===23;}')
        report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']);browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
