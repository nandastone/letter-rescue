"""Check Godot character action wrapping/callbacks against the JS reconstruction.

Explicit per-case pose/seed/empty-object fixtures isolate the action wrapper.
This is port-regression evidence, not a native journey or ambient/needs proof.
Device playback is disabled in the accelerated Godot cases; decoded sample
durations still drive action deadlines. Audio output requires separate checks.
"""
import argparse,base64,hashlib,io,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
    cases=[]
    for who in ['boy','girl']:
        for pose in [0,1,2]:
            for action in range(1,32):
                ident=20500+action+(0 if assets['room']['exempt'][action] else {0:0,1:200,2:100}[pose])
                if f'{who}:{ident}' in assets['scripts']:
                    cases.append(dict(who=who,pose=pose,action=action,name=f'{who}-{pose}-{action}'))
    (output/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    run=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_resident_actions.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=180)
    log=run.stdout+run.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    if run.returncode or 'ERROR' in log:
        raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page()
        # An origin allows the constructor's guarded local-storage lookup.
        page.route('http://treehouse.test/',lambda route:route.fulfill(body='<html></html>',content_type='text/html'))
        page.goto('http://treehouse.test/')
        for filename in ['engine.js','room-character.js']:
            page.add_script_tag(content=(ROOT/'treehouse-demo'/filename).read_text(encoding='utf-8'))
        expected=page.evaluate('''({assets,cases})=>{
          const store=new ResourceStore(assets),results=[],hz=1193181/19886;
          const sound=id=>{const a=assets.pcm['digisnd:'+id]||assets.pcm['voices:'+id];if(!a)return 0;const q=Math.floor(1000000/a.rate),rate=q>0&&q<256?Math.floor(1000000/q):a.rate;return Math.ceil(bytes(a.pcm).length/rate*hz);};
          for(const c of cases){
            const balloon={x:96,y:43,hidden:true},r=new RoomCharacter(store,{character:()=>c.who,scene:()=> 'inside',room:{now:()=>new Date(1992,0,1),busy:false,speech:[],tick:0,speechDue:0,updateCloud:()=>false},balloon,sound,changed:()=>{},announce:()=>{}});
            r.objects=[];r.pose=c.pose;r.selected=false;r.ambientEnabled=false;r.hungerDue=r.fatigueDue=Infinity;balloon.hidden=true;gameplayRandom.reset(42);r.action(c.action);
            let tick;for(tick=1;tick<=3000;tick++){r.update(tick);if(!r.busy)break;}
            const s=new Surface();r.drawObjects(s,true);r.draw(s);r.drawObjects(s,true,null,true);
            const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(s.image,0,0);
            results.push({name:c.name,pose:r.pose,objects:r.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:o.rect,front:!!o.inFrontOfCharacter})),tick:Math.min(tick,3000),busy:r.busy,seed:gameplayRandom.seed,png:canvas.toDataURL().split(',')[1]});
          }return results;
        }''',dict(assets=assets,cases=cases))
        browser.close()
    checks=[]
    for a,e in zip(actual,expected):
        expected_image=Image.open(io.BytesIO(base64.b64decode(e.pop('png')))).convert('RGB')
        image=Image.open(output/(a['name']+'.png')).convert('RGB')
        pixels=sum(x!=y for x,y in zip(image.getdata(),expected_image.getdata()))
        differences={k:dict(actual=a[k],expected=e[k]) for k in e if a[k]!=e[k]}
        if pixels:
            expected_image.save(output/(a['name']+'-js.png'))
            ImageChops.difference(image,expected_image).save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,differences=differences,passed=not differences and pixels==0))
    report=dict(checks=checks,passed=len(actual)==len(cases) and all(c['passed'] for c in checks),scope=__doc__,
                files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
