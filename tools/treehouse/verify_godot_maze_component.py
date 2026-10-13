"""Compare complete maze images across scenes, signs, actors and moving UI.

Explicit rendering fixtures against the recovered JavaScript reference; this
does not prove timing, input, state progression or device audio output.
"""
import argparse,base64,hashlib,io,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    tables=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))['music']['maze']
    cases=[]
    def add(name,character='boy',**state):
        base=dict(phase='play',node=0,songs=list(range(6)),secret=0,earned=3,actor=tables['centers'][state.get('node',0)],actorAnimation=3,actorFrame=0,wrong=[1],eliminated=[2],guessLocked=False,feedback=-1,hint=False,type=0,choices=[0,1,2,3],frog=False)
        base.update(state);cases.append(dict(name=name,character=character,state=base))
    for character in ['boy','girl']:
        for node in range(9):
            for kind in range(5):add(f'{character}-scene-{node}-type-{kind}',character,node=node,type=kind,choices=[7,9,12,18] if kind==4 else [0,1,2,3])
        for who in [0,1]:
            for animation,row in enumerate(tables['animation_count']):
                if not row[who]:continue
                for frame in sorted(set([0,row[who]-1])):
                    state=dict(frog=True,frogPoint=[135,197],frogAnimation=animation,frogFrame=frame) if who else dict(actorAnimation=animation,actorFrame=frame)
                    add(f'{character}-actor-{who}-{animation}-{frame}',character,**state)
        for y in range(60,107,2):add(f'{character}-drawer-{y}',character,chooser=True,drawerY=y,drawerSlots=[0,1,2,3,4,5],guessHighlight=2,questionBlank=True)
        for phase in ['intro','arrival','win']:
            add(f'{character}-{phase}',character,phase=phase,node=9,largeIntro=phase=='intro',actor=[150,162],frog=True,frogPoint=[150,130],controlFlash=1,currentEvent=dict(score_index=3))
    for y in [107,119,135,147]:add(f'fall-{y}',falling=dict(index=3,y=y,landed=y==147),roller=115)
    for d in range(4):
        add(f'feedback-{d}',feedback=d)
        add(f'dim-{d}',dimOther=d)
        add(f'playing-{d}',type=2,currentEvent=dict(sign=d,note=1))
    (output/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_maze_component.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=120)
    log=p.stdout+p.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''cases=>cases.map(c=>{
          const m=new MusicMaze(store,{character:()=>c.character,stop:()=>{},changed:()=>{}});m.cancel();
          Object.assign(m,c.state);m.wrong=new Set(c.state.wrong);m.eliminated=new Set(c.state.eliminated);if(c.state.drawerSlots)m.drawerSlots=new Set(c.state.drawerSlots);
          if(m.currentEvent&&m.currentEvent.score_index!==undefined)m.currentEvent.scoreIndex=m.currentEvent.score_index;
          m.draw(screen);const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);
          return {name:c.name,png:canvas.toDataURL().split(',')[1]};
        })''',cases)
        browser.close()
    checks=[]
    for c in expected:
        image=Image.open(output/(c['name']+'.png')).convert('RGB');reference=Image.open(io.BytesIO(base64.b64decode(c['png']))).convert('RGB')
        delta=ImageChops.difference(image,reference);pixels=sum(a!=b for a,b in zip(image.getdata(),reference.getdata()))
        if pixels:
            delta.save(output/(c['name']+'-diff.png'));reference.save(output/(c['name']+'-js.png'))
        checks.append(dict(name=c['name'],different_pixels=pixels,bounds=delta.getbbox(),passed=not pixels))
    report=dict(passed=len(expected)==len(cases) and all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
