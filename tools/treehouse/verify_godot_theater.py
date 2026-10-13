"""Godot theater: whole-frame fixtures, continuous JS progression and DOS images.

JS comparisons prove port consistency, not original timing. The ten DOS images
are independent native snapshots; stricter native progression remains required.
"""
import argparse,base64,hashlib,io,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT
from verify_theater import CASES as NATIVE


def cases():
    result=[]
    def add(name,**state):
        result.append(dict(name=name,state=dict(options=False,selection=[0,0,1,1],**state)))
    for actor in range(8):
        for place in range(-1,6):
            for time in range(-1,4):
                result.append(dict(name=f'stage-{actor}-{place}-{time}',state=dict(options=False,selection=[actor,actor,place,time])))
    for category in range(5):add(f'choices-{category}',category=category,propsEnabled=True)
    for curtain in range(4):
        for opening in [False,True]:add(f'curtain-{curtain}-{opening}',curtain=curtain,curtainMoving=True,openingEditor=opening,mixUp=True)
    for feedback in range(7):add(f'feedback-{feedback}',feedback=feedback,mixUp=True,order=[1,2,0,3])
    for category in range(4):
        for tick in [0,12,24,60]:add(f'preview-{category}-{tick}',previewCategory=category,presenting=category,previewBlinkUntil=60,previewUntil=80,tick=tick)
    for opts in [False,True]:
        result.append(dict(name=f'options-{opts}',state=dict(options=True,mixUp=opts,propsEnabled=opts)))
    result.append(dict(name='continuous',continuous=True,actions=[
        ['enter'],['advance',32],['set_option','mix_up',True],['set_option','props_enabled',True],['start'],['advance',240],
        ['show_choices',0],['choose',0,0],['advance',220],['choose',1,0],['advance',220],['choose',2,1],['advance',220],['choose',3,1],['advance',220],
        ['add_prop',0],['begin_drag',162,117],['move_drag',200,140],['end_drag'],['play'],['advance',1300],
        ['shuffle'],['advance',1000],['play'],['advance',1000],['correct'],['advance',130],['play'],['advance',1300],
        ['choose',0,-1],['play'],['advance',900],['choose',0,7],['advance',200],['play'],['advance',1300]]))
    # Reconstruct the same selections as the independent native snapshot suite.
    actions=[]
    increments=[[],[['start'],['advance',250]],[['show_choices',0]],[['choose',0,0],['advance',250]],[['show_choices',1]],[['choose',1,0],['advance',200]],[['show_choices',2]],[['choose',2,1],['advance',250]],[['show_choices',3]],[['choose',3,1],['advance',200]]]
    for (name,folder,snapshot,_),extra in zip(NATIVE,increments):
        actions+=extra
        reference=ROOT/'testing/output/treehouse'/folder
        run=json.loads((reference/'run.json').read_text())
        ram=(reference/'state'/f'{snapshot}.ram-0').read_bytes()
        y,x=struct.unpack_from('<HH',ram,run['main_image_base']+0x321d0+0x2064)
        result.append(dict(name='native-'+name,actions=actions.copy(),pointer=[x,y],native=str(reference/'state'/f'{snapshot}.png')))
    return result


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    fixtures=cases()
    (output/'cases.json').write_text(json.dumps(fixtures),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_theater.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=240)
    log=p.stdout+p.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:10000])
    observed={c['name']:c for c in json.loads((output/'godot.json').read_text())}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''cases=>{
          const result=[],camel=s=>s.replace(/_([a-z])/g,(_,c)=>c.toUpperCase());
          for(const c of cases){
            localStorage.removeItem('treehouse-theater-v1');gameplayRandom.reset(123456);let sounds=[];
            const a=new TheaterActivity(store,{speak:id=>{const key=ORIGINAL.pcm[`digisnd:${id}`]?`digisnd:${id}`:`voices:${id}`,sample=ORIGINAL.pcm[key];if(!sample)return 0;const rate=Math.floor(1e6/Math.floor(1e6/sample.rate)),duration=Math.ceil(bytes(sample.pcm).length/rate*TICK_HZ);sounds.push({tick:a.tick,key,rate,duration});return duration;}});
            Object.assign(a,c.state||{});let index=0;
            const capture=name=>{a.draw(screen);if(c.pointer){pointer={x:c.pointer[0],y:c.pointer[1]};drawCursor();}
              const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);
              const state={};for(const key of ['selection','order','category','tick','playing','presenting','phase','curtain','curtainMoving','director','feedback','previousValidation','performances','actorDrag','props','tokenSprite'])state[key]=a[key]??(key==='curtainMoving'?false:null);state.random=gameplayRandom.seed;
              result.push({name,state:JSON.parse(JSON.stringify(state)),sounds:JSON.parse(JSON.stringify(sounds)),png:canvas.toDataURL().split(',')[1]});};
            for(const [method,...args]of c.actions||[]){
              if(method==='advance'){for(let i=0;i<args[0];i++){a.update(a.tick+1);if(c.continuous&&(i%8===7||i===args[0]-1))capture(c.name+'-'+String(index++).padStart(4,'0'));}}
              else if(method==='set')a[camel(args[0])]=args[1];
              else if(method==='set_option')a.setOption(camel(args[0]),args[1]);
              else a[camel(method)](...args);
              if(c.continuous&&method!=='advance')capture(c.name+'-'+String(index++).padStart(4,'0'));
            }
            if(!c.continuous)capture(c.name);
          }return result;
        }''',[c for c in fixtures if 'native' not in c])
        browser.close()
    checks=[]
    def compare(name,reference,scope,state=None,sounds=None):
        image=Image.open(output/(name+'.png')).convert('RGB');reference=reference.convert('RGB')
        delta=ImageChops.difference(image,reference);pixels=sum(a!=b for a,b in zip(image.getdata(),reference.getdata()))
        if pixels:delta.save(output/(name+'-diff.png'));reference.save(output/(name+'-reference.png'))
        item=dict(name=name,scope=scope,different_pixels=pixels,bounds=delta.getbbox(),passed=not pixels)
        if state is not None:
            item['state_diff']={k:dict(expected=v,actual=observed[name]['state'].get(k)) for k,v in state.items() if v!=observed[name]['state'].get(k)}
            item['sound_passed']=sounds==observed[name]['sounds'];item['passed'] &= not item['state_diff'] and item['sound_passed']
        checks.append(item)
    for c in expected:compare(c['name'],Image.open(io.BytesIO(base64.b64decode(c['png']))),'JS port',c['state'],c['sounds'])
    for c in fixtures:
        if 'native' in c:compare(c['name'],Image.open(c['native']),'DOS original')
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']][:25]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)

