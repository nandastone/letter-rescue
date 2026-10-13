"""Replay a complete native theater journey from one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,sys
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def verify(html,output,reference,observe_audio=False,observe_presentation=False):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    checkpoints=native['checkpoints'];initial=checkpoints[0]['after']
    ram=(reference/'state/initial.ram-0').read_bytes();low=(reference/'state/initial.ram-100000').read_bytes()
    ds=0x323f0;shared=0x318b0;w=lambda off:struct.unpack_from('<h',ram,off)[0];u=lambda off:struct.unpack_from('<I',ram,off)[0]
    initial=dict(initial,category=w(ds+0x530e),environment=dict(secondsOfDay=struct.unpack_from('<I',low,0x46c)[0]*65536/1193181,
        cloud=w(shared+0xb4),cloudX=w(shared+0xa18),cloudDue=w(ds+0x201a),pose=w(ds+0x5688),hunger=w(ds+0x5282),fatigue=w(ds+0x581c),
        ambientDue=u(ds+0x531c)-initial['tick'],longDue=u(ds+0x5318)-initial['tick'],hungerDue=u(ds+0x568e)-initial['tick'],fatigueDue=u(ds+0x5576)-initial['tick']),
        objects=[dict(type=w(ds+0x5830+20*i),state=w(ds+0x5832+20*i),inside=bool(w(ds+0x5834+20*i)),
            rect=[w(ds+0x5836+20*i+2*j) for j in range(4)],due=u(ds+0x5840+20*i)-initial['tick']) for i in range(w(ds+0x556c))])
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
        reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),checks=[],pixels={},checkpoints=[],errors=[])
    if observe_presentation:
        timeline=[json.loads(line) for line in (reference/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
        report['presentation_observations']=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        if observe_audio:
            page.evaluate('''()=>{window.theaterSoundEvents=[];window.theaterSoundCheckpoint='initial';
              const start=audio.start,stop=audio.stop;
              audio.start=function(...args){const id=start.apply(this,args);if(id!==null){const v=this.active.get(id);theaterSoundEvents.push({type:'start',tick,key:v.key,id,rate:v.rate,when:args[2]??null,checkpoint:theaterSoundCheckpoint,phase:theater?.phase});}return id;};
              audio.stop=function(id,...args){if(this.active.has(id))theaterSoundEvents.push({type:'stop',tick,id,key:this.active.get(id).key,when:args[0]??null,checkpoint:theaterSoundCheckpoint,phase:theater?.phase});return stop.call(this,id,...args);};
            }''')
        page.evaluate('''async m=>{
          await audio.unlock();setScene(m.scene===5?'inside':'theater');resident.selected=true;
          if(m.scene!==5){Object.assign(theater,{selection:m.selection,order:m.order,mixUp:m.mixUp,propsEnabled:m.propsEnabled,previousValidation:m.validation,actorDrag:m.actor_drag,category:m.category,options:m.scene===13});
            theater.props=m.props.map(items=>items.map(p=>({id:((p.encoded>>8)?3175:3145)+(p.encoded&255),palette:(p.encoded>>8)?3175:3145,x:p.rect[1],y:p.rect[0]})));theaterPanel();}
          resident.objects=m.objects.map(o=>({...o,due:tick+o.due}));
          for(const o of resident.objects){resident.setBounds(o,o.rect);if(o.type===6)balloon.due=o.due;}
          const e=m.environment,start=tick,date=new Date(+new Date(1992,0,1)+e.secondsOfDay*1000);
          room.now=()=>new Date(+date+(tick-start)*1000/TICK_HZ);room.date=date;
          room.cloud=e.cloud;room.cloudX=e.cloudX;room.cloudDue=tick+e.cloudDue;
          for(const k of ['pose','hunger','fatigue'])resident[k]=e[k];
          for(const k of ['ambientDue','longDue','hungerDue','fatigueDue'])resident[k]=tick+e[k];
          gameplayRandom.reset(m.seed);gameplayRandom.trace=[];window.theaterReturnActions=[];const action=resident.action;resident.action=function(id,after){theaterReturnActions.push({id,tick,returning:!!roomTravel?.returning,phase:roomTravel?.phase});return action.call(this,id,after);};treehouseDemo.setPointer(...m.pointer);render();
          window.observeTheater=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){
            render();const data=canvas.toDataURL().split(',')[1];
            if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};
        }''',initial)
        held=False
        try:
            for checkpoint in checkpoints:
                name=checkpoint['name'];expected=checkpoint['after'];frames=[]
                if observe_audio:page.evaluate('name=>{theaterSoundCheckpoint=name;}',name)
                for action in checkpoint['inputs']:
                    point=action['point'];box=page.locator('#game').bounding_box()
                    page.mouse.move(box['x']+(point[0]+.1)*box['width']/320,box['y']+(point[1]+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    frames.extend(page.evaluate('n=>observeTheater(n)',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeTheater(0)')
                if observe_presentation:
                    first=checkpoint['inputs'][0]['from_tick'] if checkpoint['inputs'] else expected['tick']
                    native_frames={r['rgb_sha256']:r for r in timeline if r.get('original_tick') is not None and first<=r['original_tick']<=expected['tick'] and r.get('width')==320 and r.get('height')==200}
                    generated=set();browser_frames=[];frame_folder=output/'presentation-frames';frame_folder.mkdir(exist_ok=True)
                    for f in frames:
                        picture=Image.open(BytesIO(base64.b64decode(f['data']))).convert('RGB')
                        digest=hashlib.sha256(picture.tobytes()).hexdigest();generated.add(digest)
                        path=frame_folder/(digest+'.png')
                        if not path.exists():picture.save(path)
                        browser_frames.append(dict(tick=f['tick'],sha256=digest,image=path.relative_to(output).as_posix()))
                    missing=set(native_frames)-generated
                    report['presentation_observations'].append(dict(name=name,native_unique=len(native_frames),browser_unique=len(generated),represented=len(set(native_frames)&generated),unrepresented=len(missing),browser_frames=browser_frames,missing=[dict(sha256=h,image=native_frames[h]['image'],tick=native_frames[h]['original_tick']) for h in sorted(missing)]))
                actual=page.evaluate('''()=>({scene,seed:gameplayRandom.seed,selection:theater?.selection,order:theater?.order,
                  mixUp:theater?.mixUp,propsEnabled:theater?.propsEnabled,validation:theater?.previousValidation,
                  prop_counts:theater?.props.map(p=>p.length),actor_drag:theater?.actorDrag,
                  props:theater?.props,category:theater?.category,options:theater?.options,playing:theater?.playing,
                  feedback:theater?.feedback,phase:theater?.phase,randomCalls:gameplayRandom.trace,roomState:{tick,residentTick:resident.tick,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,ambientDue:resident.ambientDue,longDue:resident.longDue,hungerDue:resident.hungerDue,fatigueDue:resident.fatigueDue,objects:resident.objects}})''')
                fields=['seed']
                if expected['scene'] in [2,13]:fields+=['selection','order','mixUp','propsEnabled','validation','prop_counts','actor_drag']
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                if expected['scene'] in [2,13]:
                    props=[[dict(id=(3175 if p['encoded']>>8 else 3145)+(p['encoded']&255),palette=3175 if p['encoded']>>8 else 3145,x=p['rect'][1],y=p['rect'][0]) for p in items] for items in expected['props']]
                    if props!=actual['props']:differences['props']=dict(expected=props,actual=actual['props'])
                if actual['scene']!=('inside' if expected['scene']==5 else 'theater'):
                    differences['scene']=dict(expected=expected['scene'],actual=actual['scene'])
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
        report['return_actions']=page.evaluate('theaterReturnActions');report['checks'].append(dict(name='room reminders wait until return effect completes',passed=not any(a['returning'] for a in report['return_actions'])))
        if observe_audio:
            report['sound_events']=page.evaluate('theaterSoundEvents')
            report['sound_observation_scope']='Unchanged production start/stop calls and returned voice IDs during the input-driven journey. Tick positions are game ticks. This records event dispatch, not actual output waveform or native sample-time parity.'
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial snapshot, then ordinary mouse clicks and held drags at recorded game-tick intervals. No subsequent state or random resets. Each native checkpoint must occur in its corresponding generated input interval. This checks complete image membership and listed gameplay fields, not exact presentation timestamps or audio waveform equality.'
    if observe_presentation:report['presentation_scope']='Diagnostic membership of every original RGB display observed within each input interval, including partial redraws. No time shifting, masks or pixel tolerance. Reported separately from checkpoint acceptance; full presentation parity requires zero unrepresented displays and matching timestamps.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'theater-native-journey-e');p.add_argument('--observe-audio',action='store_true');p.add_argument('--observe-presentation',action='store_true');a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,a.reference,a.observe_audio,a.observe_presentation) else 1)
