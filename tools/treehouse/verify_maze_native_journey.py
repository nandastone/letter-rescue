"""Replay a native maze playthrough continuously from one initial snapshot.

Unlike the per-transition generation checks, the RNG and model are initialized
only once. Subsequent original mouse choices drive the complete browser model.
Stable checkpoint pixels/state are compared; this is not timing parity.
"""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json, struct, sys
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from verify_maze_generation import model
import browser_audio_observation as audio_observation
from native_input_schedule import mouse_schedule
from original_sound_cache import prepared_sounds

ROOT=Path(__file__).resolve().parents[2]
REF=ROOT/'testing/output/treehouse/research-music-maze/playthrough'
TAIL=ROOT/'testing/output/treehouse/maze-victory-tail-b/state/tail-0'


def verify(html,output,observe_audio=False,reference=REF,victory=TAIL,native_waits=False):
    reference=reference.resolve();victory=victory.resolve()
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[],checkpoints=[])
    names=['settled','wrong']+[f'correct-{i}' for i in range(8)]
    if native_waits:
        names.append('victory');schedule=mouse_schedule(reference,names);report['native_input_schedule']=schedule
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960));page.set_default_timeout(5000)
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        if observe_audio:audio_observation.install(page)
        initial=model(reference/'state/settled.ram-0')
        ram=(reference/'state/settled.ram-0').read_bytes()
        initial['preparedSounds']=prepared_sounds(ram)
        y,x,_,_=struct.unpack_from('<4h',ram,0x318b0+0x9ba)
        initial.update(actor=[y+40,x+17],earned=ram[0x318b0+0x9e6],phase='play',frog=False)
        if native_waits:initial['timers']=list(struct.unpack_from('<2H',ram,0x323f0+0x2018))
        page.evaluate('''async m=>{await audio.unlock();setScene('maze');maze.cancel();Object.assign(maze,m);maze.history=new Set(m.history);maze.random=null;maze.started=true;maze.introduced=true;maze.roundReplaced=false;maze.actorAnimation=3;maze.actorFrame=0;maze.wrong=new Set();maze.eliminated=new Set();maze.guessLocked=false;maze.feedback=-1;maze.hint=false;maze.roller=null;maze.falling=null;gameplayRandom.reset(m.seed);maze.resetIdle();mazePanel();render();}''',initial)
        page.evaluate('sounds=>{audio.preparedSamples=new Set(sounds);}',initial['preparedSounds'])
        report['initial_prepared_sounds']=initial['preparedSounds']
        if native_waits:page.evaluate('timers=>{maze.targetDue=tick+timers[0];maze.hintDue=tick+timers[1];}',initial['timers'])
        page.evaluate('''()=>{window.observeMazeTicks=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};}''')
        try:
            for name in names:
                if observe_audio:audio_observation.checkpoint(page,name)
                ram=(reference/'state'/f'{name}.ram-0').read_bytes()
                py,px=struct.unpack_from('<hh',ram,0x323f0+0x2064)
                canvas=page.locator('#game');box=canvas.bounding_box()
                page.mouse.move(box['x']+(px+0.1)*box['width']/320,box['y']+(py+0.1)*box['height']/200)
                observed_frames=[]
                if native_waits:
                    interval=schedule[name]
                    observed_frames.extend(page.evaluate('observeMazeTicks',interval['before']))
                    if interval['click']:
                        page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                        observed_frames.extend(page.evaluate('observeMazeTicks',interval['held']));page.mouse.up()
                    observed_frames.extend(page.evaluate('observeMazeTicks',interval['total']-interval['before']-interval['held']))
                elif name!='settled':
                    page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');page.mouse.up()
                    playback=page.evaluate('''()=>{let n=0,previous=-1,frames=[];while(maze.busy&&n++<30000){advance();const index=maze.currentEvent?.scoreIndex;if(maze.phase==='arrival'&&index!==undefined&&index!==previous){previous=index;render();frames.push({tick,index,data:canvas.toDataURL().split(',')[1]});}}render();return {done:!maze.busy,frames};}''')
                    if not playback['done']:
                        raise AssertionError(name+': animation did not finish')
                    if name=='correct-7':
                        # The historical endpoint is still playing note 9.
                        # Require that real generated playback frame as well as
                        # the newly captured, completed victory screen below.
                        original=Image.open(reference/'state/correct-7.png').convert('RGB')
                        matches=[]
                        for frame in playback['frames']:
                            image=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                            if image.tobytes()==original.tobytes():
                                matches.append(dict(tick=frame['tick'],note=frame['index']))
                        report['checks'].append(dict(name='native in-progress victory highlight is generated',passed=bool(matches),matches=matches))
                page.evaluate('render()')
                checkpoint_reference=victory if name=='correct-7' and not native_waits else reference/'state'/name
                ram=checkpoint_reference.with_suffix('.ram-0').read_bytes()
                expected=model(checkpoint_reference.with_suffix('.ram-0'))
                expected['earned']=ram[0x318b0+0x9e6]
                keys=['seed','hard','streak','excluded','typeHistory','patternHistory','familyHistory','songs','history','secret','node','type','correct','choices','earned']
                actual=page.evaluate('''()=>({seed:gameplayRandom.seed,hard:maze.hard,streak:maze.streak,excluded:maze.excluded,typeHistory:maze.typeHistory,patternHistory:maze.patternHistory,familyHistory:maze.familyHistory,songs:maze.songs,history:[...maze.history].sort((a,b)=>a-b),secret:maze.secret,node:maze.node,type:maze.type,correct:maze.correct,choices:maze.choices,earned:maze.earned})''')
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in keys if expected[k]!=actual[k]}
                report['checks'].append(dict(name=name+' native state and RNG',passed=not differences))
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                raw=base64.b64decode(canvas.evaluate('c=>c.toDataURL()').split(',')[1])
                image=Image.open(BytesIO(raw)).convert('RGB')
                original=Image.open(checkpoint_reference.with_suffix('.png')).convert('RGB')
                if native_waits:
                    for frame in observed_frames:
                        generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                        if generated.tobytes()==original.tobytes():image=generated;break
                delta=ImageChops.difference(image,original)
                count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),reference=str(checkpoint_reference.with_suffix('.png').relative_to(ROOT)))
                image.save(output/(name+'.png'));delta.save(output/(name+'-difference.png'))
                print(name,'PASS' if not differences and count==0 else 'FAIL',list(differences),count,flush=True)
            report['checks'].append(dict(name='continuous play reaches native victory',passed=page.evaluate('maze.phase==="win"&&!maze.busy')))
        except Exception as e:
            report['errors'].append(str(e))
        if observe_audio:audio_observation.collect(page,report)
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial native snapshot, then original canvas inputs: wrong sign and eight correct signs through victory. Full state/RNG and stable RGB checkpoints. No per-step state resets, frame shifting, timing/audio parity or fresh-entry claim.'
    if native_waits:report['scope']='One initial snapshot and original pointer choices, press/release waits and checkpoint intervals derived from native callback ticks. Full state/RNG and interval RGB checkpoint membership through victory. No per-step resets or extra settling time. Exact presentation timestamps and rendered audio remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors']),indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--observe-audio',action='store_true');parser.add_argument('--reference',type=Path,default=REF);parser.add_argument('--victory',type=Path,default=TAIL)
    parser.add_argument('--native-waits',action='store_true')
    a=parser.parse_args();sys.exit(0 if verify(a.html,a.output,a.observe_audio,a.reference,a.victory,a.native_waits) else 1)
