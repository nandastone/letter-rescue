"""Replay piano-to-maze entrances and exits from one original piano snapshot."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
import browser_audio_observation as audio_observation

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'


def verify(html,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['passed']
    initial=native['checkpoints'][0]['after'];ram=(reference/'state/initial.ram-0').read_bytes()
    initial['idleCountdown']=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]-initial['tick']
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),checks=[],pixels={},checkpoints=[],errors=[])
    report['native_input_schedule']={c['name']:dict(click=any(a['left'] for a in c['inputs']),inputs=c['inputs']) for c in native['checkpoints']}
    generated=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        page.evaluate('''async m=>{
          await audio.unlock();setScene('maze');setScene('music');maze.cancel();
          for(const key of ['songs','typeHistory','patternHistory','familyHistory'])maze[key]=m.maze[key];
          maze.history=new Set(m.maze.history);maze.savedSongs=null;maze.started=false;maze.introduced=!m.first_intro;
          maze.initialAdvanced=m.maze.hard;maze.hard=m.maze.hard;maze.phase=undefined;
          songId=m.selection[Number(m.advanced)*2];musicEditor.enabled=m.composing;longScore=musicEditor.advanced=m.advanced;
          listeningBooks.songs[Number(m.advanced)][songId][2]=m.song[2];listeningBooks.songs[Number(m.advanced)][songId][3]=m.song[3];
          instrument=m.song[3];setScene('music');musicIdle.frame=-1;musicIdle.due=tick+m.idleCountdown;repeatSong=false;
          gameplayRandom.reset(m.maze.seed);treehouseDemo.setPointer(...m.pointer);render();
          window.observeEntry=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data,scene,transfer:roomTravel?.maze?{phase:roomTravel.effect.phase,frame:roomTravel.effect.frame,actorFrame:roomTravel.effect.actor?.frameUpdates,returning:roomTravel.effect.returning}:null});}if(i<n)advance();}return frames;};
        }''',initial)
        audio_observation.install(page);held=False
        try:
            for cp in native['checkpoints']:
                name=cp['name'];audio_observation.checkpoint(page,name);frames=[]
                for action in cp['inputs']:
                    x,y=action['point'];box=page.locator('#game').bounding_box()
                    page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    frames.extend(page.evaluate('observeEntry',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeEntry(0)')
                actual=page.evaluate('''()=>({scene,seed:gameplayRandom.seed,hard:maze.hard,streak:maze.streak,excluded:maze.excluded,typeHistory:maze.typeHistory,patternHistory:maze.patternHistory,familyHistory:maze.familyHistory,songs:maze.songs,history:[...maze.history].sort((a,b)=>a-b),secret:maze.secret,node:maze.node,type:maze.type,correct:maze.correct,choices:maze.choices,earned:maze.earned,busy:maze.busy,tutoring:maze.tutoring,actor:maze.actor,frog:maze.frogPoint})''')
                expected=cp['after']['maze'];keys=['seed','songs','history','hard']
                if cp['after']['phase']==8 and not cp['after']['first_intro']:
                    keys+=['secret','node','type','correct','choices','typeHistory','patternHistory','familyHistory']
                differences={k:dict(expected=expected[k],actual=actual.get(k)) for k in keys if expected[k]!=actual.get(k)}
                report['checks'].append(dict(name=name+' active state and RNG',passed=not differences))
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');target=hashlib.sha256(original.tobytes()).hexdigest();chosen=None;matched=None
                for frame in frames:
                    image=Image.open(BytesIO(base64.b64decode(frame.pop('data')))).convert('RGB')
                    frame['hash']=hashlib.sha256(image.tobytes()).hexdigest();frame['checkpoint']=name;generated.append(frame)
                    if frame['hash']==target:chosen=image;matched=frame['tick']
                if chosen is None:chosen=image
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched,native_hash=target)
                print(name,'PASS' if not differences and count==0 else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        audio_observation.collect(page,report);browser.close()
    report['generated_frames']=generated
    callbacks=[json.loads(line) for line in (reference/'frames.jsonl').read_text().splitlines()]
    start=native['checkpoints'][0]['after']['tick'];end=native['checkpoints'][-1]['after']['tick']
    lookup={}
    for row in callbacks:
        if row.get('original_tick') is not None and start<=row['original_tick']<=end:
            lookup.setdefault(row.get('rgb_sha256'),[]).append(row['original_tick'])
    report['transfer_frames']=[dict(**frame,native_ticks=lookup.get(frame['hash'],[]),exact=frame['hash'] in lookup) for frame in generated if frame.get('transfer')]

    report['whole_route_image_membership']={name:[dict(tick=f['tick'],checkpoint=f['checkpoint']) for f in generated if f['hash']==d['native_hash']] for name,d in report['pixels'].items()}
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(d['exact'] for d in report['pixels'].values())
    report['scope']='One original piano snapshot, actual recorded pointer inputs and native game-tick intervals thereafter. Per-checkpoint image membership/state and separate whole-route image diagnostic. No clock shifting, per-step resets, rendered waveform or full timing-parity claim.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--reference',type=Path,default=DATA/'maze-entry-control-a')
    a=parser.parse_args();raise SystemExit(0 if verify(a.html,a.output,a.reference) else 1)
