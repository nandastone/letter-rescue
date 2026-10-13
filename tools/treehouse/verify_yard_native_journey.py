"""Replay a continuous original yard journey from one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,sys
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def verify(html,output,reference,start=None,stop=None):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    checkpoints=native['checkpoints']
    if start:checkpoints=checkpoints[next(i for i,c in enumerate(checkpoints) if c['name']==start):]
    if stop:checkpoints=checkpoints[:1+next(i for i,c in enumerate(checkpoints) if c['name']==stop)]
    checkpoints=[dict(c,inputs=[] if i==0 else c['inputs']) for i,c in enumerate(checkpoints)]
    initial=checkpoints[0]['after'];first=checkpoints[0]['name']
    ram=(reference/'state'/f'{first}.ram-0').read_bytes();low=(reference/'state'/f'{first}.ram-100000').read_bytes()
    initial=dict(initial,cloudX=struct.unpack_from('<h',ram,0x318b0+0xa18)[0],secondsOfDay=struct.unpack_from('<I',low,0x46c)[0]*65536/1193181)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
        start_checkpoint=checkpoints[0]['name'],end_checkpoint=checkpoints[-1]['name'],
        reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),checks=[],pixels={},checkpoints=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        page.evaluate('''async m=>{
          await audio.unlock();character=m.sex?'girl':'boy';resident.selected=m.selected;setScene({4:'outside',5:'inside',14:'hollow'}[m.scene]);
          resident.objects=m.objects.map(o=>({...o,due:tick+o.due-m.tick}));balloon.hidden=!resident.objects.some(o=>o.type===6);
          for(const o of resident.objects){resident.setBounds(o,o.rect);if(o.type===6)balloon.due=o.due;}
          const start=tick,date=new Date(+new Date(1992,0,1)+m.secondsOfDay*1000);
          room.now=()=>new Date(+date+(tick-start)*1000/TICK_HZ);room.date=date;room.cloud=m.cloud;room.cloudX=m.cloudX;
          for(const k of ['pose','hunger','fatigue','outsideCycle'])resident[k]=m[k];
          for(const k of ['ambientDue','longDue','hungerDue','fatigueDue'])resident[k]=tick+m[k]-m.tick;
          resident.windowDue=tick+m.windowRemaining;
          gameplayRandom.reset(m.seed);gameplayRandom.trace=[];treehouseDemo.setPointer(...m.pointer);render();
          window.observeYard=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){
            render();const data=canvas.toDataURL().split(',')[1];
            if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};
        }''',initial)
        held=False
        try:
            for checkpoint in checkpoints:
                name=checkpoint['name'];expected=checkpoint['after'];frames=[]
                for action in checkpoint['inputs']:
                    point=action['point'];box=page.locator('#game').bounding_box()
                    page.mouse.move(box['x']+(point[0]+.1)*box['width']/320,box['y']+(point[1]+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    frames.extend(page.evaluate('n=>observeYard(n)',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeYard(0)')
                actual=page.evaluate('''()=>({scene:{outside:4,inside:5,hollow:14}[scene],seed:gameplayRandom.seed,
                  selected:resident.selected,sex:character==='girl'?1:0,cloud:room.cloud,outsideCycle:resident.outsideCycle,
                  pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,
                  objects:resident.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:resident.bounds(o)})),
                  tick,ambientDue:resident.ambientDue,longDue:resident.longDue,hungerDue:resident.hungerDue,fatigueDue:resident.fatigueDue,
                  nuts:exterior.nuts,signWaiting:exterior.signWaiting,randomCalls:gameplayRandom.trace})''')
                fields=['scene','seed','selected','sex','cloud','outsideCycle','pose','hunger','fatigue']
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                expected_objects=[{k:o[k] for k in ['type','state','inside','rect']} for o in expected['objects']]
                if expected_objects!=actual['objects']:differences['objects']=dict(expected=expected_objects,actual=actual['objects'])
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');chosen=None;matched=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():chosen=generated;matched=frame['tick'];break
                if chosen is None:chosen=Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB')
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['checks'].append(dict(name=name+' state/random sequence',passed=not differences))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched)
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                print(name,'PASS' if not differences and not count else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial snapshot, then ordinary mouse clicks and held drags at recorded game-tick intervals. No subsequent state or random resets. Each native checkpoint must occur in its corresponding generated input interval. This checks complete image membership and listed gameplay fields, not exact presentation timestamps or audio waveform equality.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'yard-native-journey-a');p.add_argument('--start');p.add_argument('--stop');a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,a.reference,a.start,a.stop) else 1)
