"""Replay original room calendar, clock and chalkboard inputs continuously."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,sys
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def verify(html,output,reference,start=None,stop=None,portrait_frame=None):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    checkpoints=native['checkpoints']
    if start:checkpoints=checkpoints[next(i for i,c in enumerate(checkpoints) if c['name']==start):]
    if stop:checkpoints=checkpoints[:1+next(i for i,c in enumerate(checkpoints) if c['name']==stop)]
    checkpoints=[dict(c,inputs=[] if i==0 else c['inputs']) for i,c in enumerate(checkpoints)]
    initial=checkpoints[0]['after'];first=checkpoints[0]['name']
    ram=(reference/'state'/f'{first}.ram-0').read_bytes();low=(reference/'state'/f'{first}.ram-100000').read_bytes()
    initial=dict(initial,portraitFrame=portrait_frame,cloudX=struct.unpack_from('<h',ram,0x318b0+0xa18)[0],secondsOfDay=struct.unpack_from('<I',low,0x46c)[0]*65536/1193181)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
        start_checkpoint=checkpoints[0]['name'],end_checkpoint=checkpoints[-1]['name'],initial_portrait_frame=portrait_frame,
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
          room.now=()=>new Date(+date+(tick-start)*1000/TICK_HZ);room.date=new Date(m.date[0],m.date[1]-1,m.date[2]);room.portraitFrame=m.portraitFrame;room.cloud=m.cloud;room.cloudX=m.cloudX;room.cloudDue=tick+m.windowRemaining;room.height=room.target=m.calendarOpen?98:28;chalk.select(m.chalkTool);
          for(const k of ['pose','hunger','fatigue','outsideCycle'])resident[k]=m[k];
          for(const k of ['ambientDue','longDue','hungerDue','fatigueDue'])resident[k]=tick+m[k]-m.tick;
          resident.windowDue=tick+m.windowRemaining;
          gameplayRandom.reset(m.seed);gameplayRandom.trace=[];treehouseDemo.setPointer(...m.pointer);render();
          window.roomEvents=[];let lastRoomEvent="";
          window.observeRoom=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){
            const event={seed:gameplayRandom.seed,ambientDue:resident.ambientDue,cloudX:room.cloudX,balloonDue:balloon.due,objects:resident.objects.filter(o=>[0,6].includes(o.type)).map(o=>({type:o.type,state:o.state,rect:resident.bounds(o)}))},key=JSON.stringify(event);if(key!==lastRoomEvent){roomEvents.push({tick,...event});lastRoomEvent=key;}
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
                    frames.extend(page.evaluate('n=>observeRoom(n)',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeRoom(0)')
                actual=page.evaluate('''()=>({scene:{outside:4,inside:5,hollow:14}[scene],seed:gameplayRandom.seed,
                  selected:resident.selected,sex:character==='girl'?1:0,cloud:room.cloud,outsideCycle:resident.outsideCycle,
                  pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,
                  date:[room.date.getFullYear(),room.date.getMonth()+1,room.date.getDate()],calendarOpen:room.open,chalkTool:chalk.tool,
                  objects:resident.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:resident.drag?.moved&&resident.drag.object===o?resident.drag.rect:resident.bounds(o)})),
                  drag:resident.drag?{type:resident.drag.object.type,origin:resident.drag.rect,displayed:resident.bounds(resident.drag.object),moved:resident.drag.moved}:null,
                  tick,ambientDue:resident.ambientDue,longDue:resident.longDue,hungerDue:resident.hungerDue,fatigueDue:resident.fatigueDue,
                  nuts:exterior.nuts,signWaiting:exterior.signWaiting,randomCalls:gameplayRandom.trace})''')
                fields=['scene','seed','selected','sex','cloud','pose','hunger','fatigue','date','calendarOpen','chalkTool']
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                expected_objects=[{k:o[k] for k in ['type','state','inside','rect']} for o in expected['objects']]
                # Object identity, state and geometry are gameplay state. Storage order
                # is an implementation detail; rendering and replayed hits still expose
                # any observable layering/selection difference without pixel masks.
                object_order=dict(expected=[o['type']for o in expected_objects],actual=[o['type']for o in actual['objects']])
                object_order['equal']=object_order['expected']==object_order['actual']
                if sorted(expected_objects,key=lambda o:o['type'])!=sorted(actual['objects'],key=lambda o:o['type']):differences['objects']=dict(expected=expected_objects,actual=actual['objects'])
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');chosen=None;matched=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():chosen=generated;matched=frame['tick'];break
                if chosen is None:chosen=Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB')
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['checks'].append(dict(name=name+' state/random sequence',passed=not differences))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched)
                report['checkpoints'].append(dict(name=name,differences=differences,object_storage_order=object_order,actual=actual))
                print(name,'PASS' if not differences and not count else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        report["room_events"]=page.evaluate("roomEvents")
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial snapshot, then ordinary mouse clicks and held drags at recorded game-tick intervals. No subsequent state or random resets. Each native checkpoint must occur in its corresponding generated input interval. During a held drag, stored object position is compared with the drag origin; the separately reported displayed position is checked by the full RGB image. Object identity/state/geometry are compared independently of storage order, which is reported diagnostically; full images and replayed inputs still check observable layering and selection. This checks complete image membership and listed gameplay fields, not exact presentation timestamps or audio waveform equality.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'room-native-journey-c');p.add_argument('--start');p.add_argument('--stop');p.add_argument('--portrait-frame',type=int,choices=[931,932]);a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,a.reference,a.start,a.stop,a.portrait_frame) else 1)
