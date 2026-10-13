"""Replay consecutive original board-game inputs from one starting snapshot.

Game state/RNG are loaded only once. Every original checkpoint must occur in
the generated sequence, including hints and delivery. This is ordered image
membership, not equality at the original presentation timestamps.
"""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,sys
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
import browser_audio_observation as audio_observation

ROOT=Path(__file__).resolve().parents[2]
REF=ROOT/'testing/output/treehouse/research-boardgame/turn-b/state'


def model(path):
    ram=path.read_bytes();ds=0x323f0
    words=lambda at,n=1:list(struct.unpack_from('<'+str(n)+'h',ram,ds+at))
    settings=(words(0x4ada)[0]&65535)*16-0x1860
    mode,opponent,*levels=struct.unpack_from('<8h',ram,settings+0x3ee)
    return dict(mode=mode,opponent=opponent,levels=[levels[3*mode],levels[3*mode+opponent]],player=words(0x52d8)[0],nodes=words(0x52c4,2),directions=words(0x5734,2),balances=words(0x5a0c,2),types=words(0x59da,24),remaining=words(0x5276)[0],first=bool(words(0x57c6)[0]),seed=struct.unpack_from('<I',ram,ds+0x5290)[0])


def verify(html,output,reference=REF,names=None,complete_game=False,observe_initial=False,observe_audio=False,native_waits=False):
    output.mkdir(parents=True,exist_ok=False)
    names=names or ['started','rolled','move-0','move-1','move-2','reward-chosen','next-turn']
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},checkpoints=[],errors=[])
    schedule={}
    if native_waits:
        recording=json.loads((reference.parent/'run.json').read_text(encoding='utf-8'))
        callbacks=[json.loads(line) for line in (reference.parent/'frames.jsonl').read_text().splitlines()]
        by_run={}
        for frame in callbacks:by_run.setdefault(frame['run'],frame['original_tick'])
        cursor=max(by_run)+1-sum(a['frames'] for a in recording['actions'])
        prior=None;press_tick=None
        for action in recording['actions']:
            if action.get('mouse',{}).get('left'):press_tick=by_run[cursor]
            cursor+=action['frames']
            if name:=action.get('capture'):
                end=struct.unpack_from('<I',(reference/f'{name}.ram-0').read_bytes(),0x323f0+0x201e)[0]
                if name in names:
                    schedule[name]=dict(before=0 if prior is None else press_tick-prior,total=0 if prior is None else end-prior)
                    assert 0<=schedule[name]['before']<=schedule[name]['total']
                    prior=end
        assert list(schedule)==names
        report['native_input_schedule']=schedule
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960));page.set_default_timeout(5000)
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        if observe_audio:audio_observation.install(page)
        initial=model(reference/f'{names[0]}.ram-0')
        initial.update(options=False,played=True,phase='move' if initial['remaining']>0 else 'ready',hintRed=initial['remaining']<0)
        if native_waits:
            ram=(reference/f'{names[0]}.ram-0').read_bytes()
            initial['hintDue']=struct.unpack_from('<H',ram,0x323f0+0x201a)[0]
            # These initial snapshots are in the white, between-reminder wait.
            # Require that fixture condition rather than searching later frames.
            assert initial['hintDue']>0 and Image.open(reference/f'{names[0]}.png').convert('RGB').getpixel((85,51))==(255,255,255)
            initial['hintRed']=False
        page.evaluate('''async m=>{await audio.unlock();setScene('boardgame');boardgame.motion.cancel();Object.assign(boardgame,m);boardgamePanel();render();}''',initial)
        try:
            for name in names:
                if observe_audio:audio_observation.checkpoint(page,name)
                ram=(reference/f'{name}.ram-0').read_bytes();py,px=struct.unpack_from('<hh',ram,0x323f0+0x2064)
                canvas=page.locator('#game');box=canvas.bounding_box()
                page.mouse.move(box['x']+(px+0.1)*box['width']/320,box['y']+(py+0.1)*box['height']/200)
                frames=[]
                if native_waits:page.evaluate('n=>advance(n)',schedule[name]['before'])
                if name!=names[0]:
                    page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');page.mouse.up()
                if native_waits:
                    sequence=page.evaluate('''n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return {frames};}''',schedule[name]['total']-schedule[name]['before'])
                    frames=sequence['frames']
                elif name!=names[0] or complete_game or observe_initial:
                    sequence=page.evaluate('''()=>{let n=0;const frames=[],seen=new Set(),save=()=>{render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data});}},busy=()=>((boardgame.motion.busy||boardgame.moving||boardgame.phase==='rolling')&&!(boardgame.phase==='exchange'&&!boardgame.motion.accepted));save();while(busy()&&n++<30000){advance();save();}const done=!busy();if(done){for(let i=0;i<420;i++){advance();save();}}return {done,frames};}''')
                    if not sequence['done']:
                        raise AssertionError(name+': animation did not finish')
                    frames=sequence['frames']
                page.evaluate('render()')
                expected=model(reference/f'{name}.ram-0')
                actual=page.evaluate('()=>{const g=boardgame;return {mode:g.mode,opponent:g.opponent,levels:g.levels,player:g.player,nodes:g.nodes,directions:g.directions,balances:g.balances,types:g.types,remaining:g.remaining,first:g.first,seed:g.seed};}')
                # Original 20D1..20DA switches logical player to the prize
                # recipient after loss, while retaining the loser's dashboard.
                # The browser stores those meanings separately. Compare the
                # logical recipient here; full RGB still checks the dashboard.
                ending_roles=page.evaluate('()=>({displayPlayer:boardgame.player,loser:boardgame.loser,recipient:boardgame.loser>=0?1-boardgame.loser:boardgame.player})')
                actual['player']=ending_roles['recipient']
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in expected if expected[k]!=actual[k]}
                report['checks'].append(dict(name=name+' state and random seed',passed=not differences))
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual,ending_roles=ending_roles))
                image=Image.open(BytesIO(base64.b64decode(canvas.evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB')
                original=Image.open(reference/f'{name}.png').convert('RGB')
                match_tick=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():
                        image=generated;match_tick=frame['tick'];break
                delta=ImageChops.difference(image,original);count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
                image.save(output/(name+'.png'));delta.save(output/(name+'-difference.png'))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=match_tick)
                print(name,'PASS' if not differences and count==0 else 'FAIL',list(differences),count,flush=True)
            if complete_game:
                report['checks'].append(dict(name='complete original game reaches matching ending',passed=page.evaluate('boardgame.phase==="result"&&!boardgame.motion.busy&&(boardgame.winner>=0||boardgame.loser>=0)')))
        except Exception as e:
            report['errors'].append(str(e))
        if observe_audio:audio_observation.collect(page,report)
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='Consecutive original board checkpoints from one initial snapshot, then actual pointer inputs without resetting state. Every native checkpoint must be generated, including hints and delivery frames. Persistent model/RNG checked after each sequence. Inputs use original coordinates with a fixed 420-tick idle observation after each completed action. No full game/ending, native input timing or presentation timing claim.'
    if complete_game:
        report['scope']='Complete original board game from one initial snapshot through its ending. Mode, opponent and goals are read from the snapshot. Each original mouse choice is replayed without resetting state/RNG. Every reference checkpoint must occur among generated frames; state/RNG compared after every action. A fixed 420-tick idle observation follows each completed action. This establishes state continuity and ordered image membership, not equality at native input/presentation times, fresh-entry behavior, every branch or audio waveform equality.'
    report['scope']+=' At a losing ending, player means the prize recipient; the separately reported displayPlayer retains the losing dashboard and is checked by full RGB. The names listed in checkpoints define the replay span; an ending check alone does not prove the preceding game.'
    if native_waits:report['scope']='Complete original board input choices with waits derived from recorded mouse-press callback ticks and checkpoint RAM ticks; no settling extension or fixed idle wait. Full RGB checkpoint membership and gameplay/random state are still compared. This does not establish intermediate display timestamps or actual audio sample scheduling.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors']),indent=2));return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();sys.exit(0 if verify(a.html,a.output) else 1)
