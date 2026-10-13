"""Isolated Godot/JS object operations, with identical seed, needs and civil clock.

Checks complete resident RGBA frames every eighth tick and at completion,
completion ticks, poses, needs, object state, shared RNG and sample events.
These component fixtures do not establish native timing or device audio parity.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(engine, output):
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for who in ['boy', 'girl']:
        for op, types in [('offer', [2,3,4,5,8,11,12,17,18,19,20]), ('click', [0,1,2,5,7,9,10,12,14,15,16]), ('place', [1,2,7,8,11,17])]:
            for kind in types:
                for need in ([1,5] if op=='offer' else [1]):
                    cases.append(dict(name=f'{who}-{op}-{kind}-{need}',who=who,op=op,type=kind,hunger=need,fatigue=need,state=1,scene='inside'))
        for kind in [12,14,16]:
            cases.append(dict(name=f'{who}-outside-{kind}',who=who,op='click',type=13 if kind==12 else kind,hunger=1,fatigue=1,state=1,scene='outside'))
        cases.append(dict(name=f'{who}-offer-worm-bird',who=who,op='offer',type=12,hunger=1,fatigue=1,state=1,scene='inside',bird=True))
    (output/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    p = subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_object_actions.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=240)
    log=p.stdout+p.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:
        raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page()
        page.route('http://localhost/',lambda route:route.fulfill(body='<html></html>',content_type='text/html'))
        page.goto('http://localhost/')
        for name in ['engine.js','room.js','room-character.js']:
            page.add_script_tag(content=(ROOT/'treehouse-demo'/name).read_text(encoding='utf-8'))
        expected=page.evaluate('''async ({assets,cases})=>{
          const store=new ResourceStore(assets),results=[],hz=1193181/19886;
          for(const c of cases){
            let tick=0;const sounds=[],balloon={x:96,y:43,hidden:true};
            const sound=id=>{const key=assets.pcm['digisnd:'+id]?'digisnd:'+id:'voices:'+id,a=assets.pcm[key];if(!a)return 0;const q=Math.floor(1e6/a.rate),rate=q>0&&q<256?Math.floor(1e6/q):a.rate,d=Math.ceil(bytes(a.pcm).length/rate*hz);sounds.push([tick,key,d]);return d;};
            const room=new TreehouseRoom(store,{changed:()=>{},announce:()=>{},speak:sound,balloon,now:()=>new Date(1992,0,1,10),environmentComplete:()=>r.scheduleAmbient(),calendarComplete:open=>{if(open)r.scheduleAmbient();else r.enterScene();}});
            const r=new RoomCharacter(store,{character:()=>c.who,scene:()=>c.scene,room,balloon,sound,changed:()=>{},announce:()=>{}});
            r.objects=[];r.ambientEnabled=false;r.hunger=c.hunger;r.fatigue=c.fatigue;r.hungerDue=r.fatigueDue=999999;balloon.hidden=true;
            const o=r.create(c.type,c.scene==='inside');o.state=c.state;
            if(c.bird)r.create(15).rect=[95,218,115,243];
            gameplayRandom.reset(42);sounds.length=0;
            if(c.op==='offer')r.offer(o);else if(c.op==='place'){r.setBounds(o,[40,100,40+o.rect[2]-o.rect[0],100+o.rect[3]-o.rect[1]]);r.place(o);}else r.clickObject(o);
            const frames=[];
            for(tick=1;tick<=4000;tick++){
              room.update(tick,r.busy);r.update(tick);
              const idle=!r.busy&&!room.busy&&!room.speech.length&&tick>=room.speechDue;
              if(tick%8===0||idle){const s=new Surface();r.drawNap(s);r.drawObjects(s,c.scene==='inside');if(c.scene==='inside')r.draw(s);r.drawObjects(s,c.scene==='inside',null,true);r.drawObjectMotion(s);const hash=await crypto.subtle.digest('SHA-256',s.image.data);frames.push([tick,[...new Uint8Array(hash)].map(v=>v.toString(16).padStart(2,'0')).join('')]);}
              if(idle)break;
            }
            results.push({name:c.name,tick:Math.min(tick,4000),pose:r.pose,hunger:r.hunger,fatigue:r.fatigue,seed:gameplayRandom.seed,objects:r.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:r.bounds(o),front:!!o.inFrontOfCharacter})),frames,sounds});
          }return results;
        }''',dict(assets=assets,cases=cases))
        browser.close()
    (output/'js.json').write_text(json.dumps(expected),encoding='utf-8')
    checks=[]
    for a,e in zip(actual,expected):
        differences={k:dict(actual=a[k],expected=e[k]) for k in e if a[k]!=e[k]}
        checks.append(dict(name=e['name'],passed=not differences,differences=differences))
    report=dict(passed=len(actual)==len(cases) and all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[dict(name=c['name'],fields=list(c['differences'])) for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if verify(a.godot,a.output) else 1)
