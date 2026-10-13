"""Replay an original full guessing game and prize from one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json, struct, sys
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
import browser_audio_observation as audio_observation

ROOT=Path(__file__).resolve().parents[2]
REFERENCE=ROOT/'testing/output/treehouse/nature-native-journey-c'


def verify(html,output,until='back-to-room',start_name='initial',observe_audio=False,continuation=None,reference=REFERENCE):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    checkpoints=native['checkpoints'];start=next(i for i,c in enumerate(checkpoints) if c['name']==start_name)
    checkpoints=checkpoints[start:];checkpoints=checkpoints[:next(i for i,c in enumerate(checkpoints) if c['name']==until)+1]
    initial=checkpoints[0]['after']
    ram=(reference/'state'/f'{start_name}.ram-0').read_bytes();ds=0x323f0
    word=lambda off:struct.unpack_from('<h',ram,off)[0]
    shared=(word(ds+0x4ada)&65535)*16-0x1860
    low_ram=(reference/'state'/f'{start_name}.ram-100000').read_bytes()
    seconds_of_day=struct.unpack_from('<I',low_ram,0x46c)[0]*65536/1193181
    initial=dict(initial,environment=dict(minute=word(shared+0x9da),cloud=word(shared+0xb4),
                 secondsOfDay=seconds_of_day,cloudX=word(shared+0xa18),pose=word(ds+0x5688),hunger=word(ds+0x5282),fatigue=word(ds+0x581c),
                 timers={key:struct.unpack_from('<I',ram,ds+off)[0] for key,off in [('ambientDue',0x531c),('longDue',0x5318),('hungerDue',0x568e),('fatigueDue',0x5576)]}))
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
                reference_report_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),
                start_checkpoint=start_name,end_checkpoint=until,checks=[],pixels={},checkpoints=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960));page.set_default_timeout(5000)
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        if observe_audio:audio_observation.install(page)
        page.evaluate('''async m=>{
          await audio.unlock();setScene('nature');nature.mode=m.scene===9?'quiz':'explore';
          const q=nature.quiz;
          Object.assign(q,{cards:m.cards,secret:m.secret,opponent:m.opponent,help:m.help,
            player:m.player,asked:m.asked,remaining:m.remaining,available:m.available,
            phase:'ready',options:false,winner:-1,guessing:false,selected:-1,
            visibleQuestions:[],hintDue:tick+m.idle_timer,winPhase:0,winStage:null});
          resident.objects=m.objects.map(o=>({...o,due:Infinity}));resident.selected=true;
          for(const o of resident.objects)resident.setBounds(o,o.rect);
          const e=m.environment,startTick=tick,date=new Date(+new Date(1992,0,1)+e.secondsOfDay*1000);
          room.now=()=>new Date(+date+(tick-startTick)*1000/TICK_HZ);room.date=date;
          room.cloud=e.cloud;room.cloudX=e.cloudX;
          resident.pose=e.pose;resident.hunger=e.hunger;resident.fatigue=e.fatigue;
          if(m.restoreNeedTimers)for(const key of ['hungerDue','fatigueDue'])resident[key]=tick+e.timers[key]-m.tick;
          if(m.shelf)rewards.shelf=m.shelf.slice();if(m.visited_mask!==undefined)rewards.visited=m.visited_mask;
          gameplayRandom.reset(m.seed);naturePanel();treehouseDemo.setPointer(...m.pointer);render();
          window.observeNature=function(n){const frames=[],seen=new Set();
            for(let i=0;i<=n;i++){render();const data=canvas.toDataURL().split(',')[1];
              if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}
            return frames;};
        }''',dict(initial,restoreNeedTimers=continuation is not None or native.get('robot',False)))
        try:
            for index,checkpoint in enumerate(checkpoints):
                name=checkpoint['name'];expected=checkpoint['after'];frames=[]
                if observe_audio:audio_observation.checkpoint(page,name)
                if index:
                    previous=checkpoints[index-1]['after']
                    before_input=checkpoint['input_tick']-previous['tick']
                    after_input=expected['tick']-checkpoint['input_tick']
                    assert before_input>=0 and after_input>=0
                    px,py=expected['pointer'];canvas=page.locator('#game');box=canvas.bounding_box()
                    page.mouse.move(box['x']+(px+.1)*box['width']/320,box['y']+(py+.1)*box['height']/200)
                    page.evaluate('n=>advance(n)',before_input)
                    page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');page.mouse.up()
                    frames=page.evaluate('n=>observeNature(n)',after_input)
                else:
                    frames=page.evaluate('observeNature(0)')
                actual=page.evaluate('''()=>{const q=nature.quiz;return {
                  cards:q.cards,secret:q.secret,opponent:q.opponent,help:q.help,player:q.player,
                  asked:q.asked,remaining:q.remaining,available:q.phase==='question'&&q.winner<0?[...q.available].sort((a,b)=>a-b):[],
                  answered:q.phase==='ready'?-1:['answered','won'].includes(q.phase)?1:0,
                  guessing:Number(q.phase==='question'&&q.guessing),win_phase:q.winPhase||0,
                  seed:gameplayRandom.seed,phase:q.phase,scene,natureMode:nature.mode,
                  winner:q.winner,prizeActive:rewards.active,prizeChoices:rewards.choices||[],shelf:rewards.shelf.slice(),visited_mask:rewards.visited,
                  room:{tick,cloud:room.cloud,cloudX:room.cloudX,balloon:{...balloon},ambientDue:resident.ambientDue,longDue:resident.longDue,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue},
                  objects:resident.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:resident.bounds(o)}))};}''')
                # Quiz scratch storage is reused by other scenes. Compare only
                # active fields, and effective question availability, not stale flags.
                expected=dict(expected)
                if expected['answered']!=0 or expected['win_phase']!=0:expected['available']=[]
                fields=['seed']
                if expected['scene']==9:fields+=['cards','secret','opponent','help','player','asked','remaining','available','answered','guessing','win_phase']
                if expected['scene']==9 and expected['win_phase']:fields+=['winner']
                fields += [key for key in ['shelf','visited_mask'] if key in expected]
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                if native.get('robot') and expected['scene']==5:
                    expected_objects=[{key:o[key] for key in ['type','state','inside','rect']} for o in expected['objects']]
                    if sorted(expected_objects,key=lambda o:o['type'])!=sorted(actual['objects'],key=lambda o:o['type']):
                        differences['objects']=dict(expected=expected_objects,actual=actual['objects'])
                    room_ram=(reference/'state'/f'{name}.ram-0').read_bytes()
                    for key,off in [('pose',0x5688),('hunger',0x5282),('fatigue',0x581c)]:
                        value=struct.unpack_from('<h',room_ram,ds+off)[0]
                        if value!=actual['room'][key]:differences[key]=dict(expected=value,actual=actual['room'][key])
                expected_scene={9:('nature','quiz'),1:('nature','explore'),5:('inside',None),12:('telescope',None),2:('theater',None),13:('theater',None)}[expected['scene']]
                if actual['scene']!=expected_scene[0] or expected_scene[1] and actual['natureMode']!=expected_scene[1]:
                    differences['scene']=dict(expected=expected_scene,actual=[actual['scene'],actual['natureMode']])
                if name=='prize-chooser' and expected['prize_choices']!=actual['prizeChoices']:
                    differences['prizeChoices']=dict(expected=expected['prize_choices'],actual=actual['prizeChoices'])
                report['checks'].append(dict(name=name+' state and random sequence',passed=not differences))
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB')
                selected=Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB');matched=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():selected=generated;matched=frame['tick'];break
                delta=ImageChops.difference(selected,original);count=sum(a!=b for a,b in zip(selected.getdata(),original.getdata()))
                selected.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched)
                print(name,'PASS' if not differences and count==0 else 'FAIL',list(differences),count,flush=True)
            if continuation is not None:
                continuation(page, report, output)
            prize=native['selected_prize']['type']
            report['checks'].append(dict(name='prize delivered',passed=page.evaluate('(slot)=>!rewards.active&&rewards.shelf[slot]',native['selected_prize']['slot']) if native.get('robot') else page.evaluate('(type)=>!rewards.active&&resident.objects.some(o=>o.type===type)',prize)))
            if until in ['back-to-room','theater-return']:
                report['checks'].append(dict(name='returned to room',passed=page.evaluate('scene==="inside"')))
        except Exception as e:report['errors'].append(str(e))
        if observe_audio:audio_observation.collect(page,report)
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']=f'One initial native quiz/room-object snapshot, then ordinary canvas inputs at recorded integer game ticks through {until}. No per-checkpoint state/RNG resets. Each reference image must occur in the generated interval. Exact presentation timing and full room environment/timer initialization are not established. Compare active scene fields only: quiz scratch storage is reused after exit, and available flags are meaningful only during a question. Initial calendar/clock, cloud, character needs and balloon bounds are restored once; wall time advances with the game clock.'
    if continuation is not None:
        report['scope']+=' Continued into the linked earned-prize input recording on the same page without resetting game state, random state, objects or timers. For this longer journey, the two original need deadlines are also restored once at the initial quiz snapshot; existing suites retain their prior initialization. Existing return/timing failures remain part of the result.'
    if native.get('robot'):
        report['scope']+=' Robot journey also initializes its session shelf flags, telescope visit mask and need deadlines once from the initial snapshot. Shelf ownership/visit mask are compared after every action; room checkpoints also compare object identity/state/geometry and character pose/hunger/fatigue. No outcome, prize, random state or shelf is injected later.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors']),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--start',default='initial')
    p.add_argument('--observe-audio',action='store_true')
    p.add_argument('--reference',type=Path,default=REFERENCE);p.add_argument('--until',default='back-to-room')
    a=p.parse_args();sys.exit(0 if verify(a.html,a.output,start_name=a.start,observe_audio=a.observe_audio,reference=a.reference,until=a.until) else 1)
