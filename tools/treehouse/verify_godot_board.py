"""Compare Godot board rendering, rules, continuous motion and sound dispatch.

The preserved JS implementation is the port reference here. These complete RGB
and state comparisons do not establish native timing or waveform fidelity.
"""
import argparse,base64,hashlib,io,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT

FIELDS='mode opponent levels options played phase player nodes directions balances types remaining first winner loser rewards rewardCoins path message rollFrames rollIndex rollResult offerHint nodeHint offerStage headerHidden ending carHidden paymentHand paymentCoinsVisible paidChips transfer exchange resolvedNodeIcons'.split()

def cases():
    result=[]
    for character in ['boy','girl']:
        for mode in range(2):
            for opponent in [1,2]:
                for level in range(3):
                    result.append(dict(name=f'options-{character}-{mode}-{opponent}-{level}',character=character,state=dict(mode=mode,opponent=opponent,levels=[level,2-level]),actions=[['enter']]))
    for mode in range(2):
        for opponent in [1,2]:
            result.append(dict(name=f'game-{mode}-{opponent}',continuous=True,state=dict(mode=mode,opponent=opponent),actions=[['start'],['play',18000]]))
        for balance,payment in [(0,5),(4,8),(10,4),(100,16),(200,114)]:
            result.append(dict(name=f'payment-{mode}-{balance}-{payment}',continuous=True,state=dict(mode=mode,options=False,played=True,phase='payment',balances=[balance,10],rewards=[-payment],paymentRequested=payment,paymentBefore=balance,paymentLoser=0 if payment>balance else -1),actions=[['motion','landing',True],['play',2400]]))
        for balance,credit in [(9,4),(99,11),(199,12)]:
            result.append(dict(name=f'credit-{mode}-{balance}-{credit}',continuous=True,state=dict(mode=mode,options=False,played=True,phase='reward',balances=[balance,10],rewards=[credit,credit+1],rewardCoins=[[0,0,0,0,0,credit],[0,0,0,0,0,credit+1]] if not mode else []),actions=[['choose',1],['play',3000]]))
    return result

def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False);fixtures=cases()
    (output/'cases.json').write_text(json.dumps(fixtures),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_board.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=240)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:8000])
    actual={c['name']:c for c in json.loads((output/'godot.json').read_text())}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''({cases,fields})=>{
          const out=[],camel=s=>s.replace(/_([a-z])/g,(_,c)=>c.toUpperCase());
          for(const c of cases){
            gameplayRandom.reset(123456);let sounds=[];
            const g=new BoardGame(store,{character:()=>c.character||'boy',speak:id=>{const key=ORIGINAL.pcm[`digisnd:${id}`]?`digisnd:${id}`:`voices:${id}`,s=ORIGINAL.pcm[key];if(!s)return 0;const rate=Math.floor(1e6/Math.floor(1e6/s.rate)),duration=Math.ceil(bytes(s.pcm).length/rate*TICK_HZ);sounds.push({tick:g.tick,key,rate,duration});return duration;}});
            Object.assign(g,c.state||{});let index=0;
            const capture=name=>{g.draw(screen);const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);const state={seed:gameplayRandom.seed};for(const key of fields)state[key]=g[key]??({rollIndex:0,rollResult:0,offerHint:-1,nodeHint:-1,headerHidden:false,ending:false,carHidden:false,resolvedNodeIcons:{}}[key]??null);out.push({name,state:JSON.parse(JSON.stringify(state)),sounds:JSON.parse(JSON.stringify(sounds)),png:canvas.toDataURL().split(',')[1]});};
            const play=()=>{if(g.phase==='exchange'&&g.exchange&&!g.motion.accepted)g.exchangeChips();else if(!g.motion.busy&&!g.moving){if(['ready','result'].includes(g.phase)&&g.winner<0&&g.loser<0)g.roll();else if(g.phase==='move'&&g.role()!==2)g.move(g.neighbours()[0]);else if(g.phase==='reward')g.choose(g.rewards[0]>=g.rewards[1]?0:1);}};
            for(const [method,...args]of c.actions||[]){if(['advance','play'].includes(method)){for(let i=0;i<args[0];i++){if(method==='play')play();g.update(g.tick+1);if(c.continuous&&(i%24===23||i===args[0]-1))capture(c.name+'-'+String(index++).padStart(4,'0'));}}else if(method==='motion')g.motion.start(g.motion[camel(args[0])](...args.slice(1)));else g[camel(method)](...args);if(c.continuous&&!['advance','play'].includes(method))capture(c.name+'-'+String(index++).padStart(4,'0'));}if(!c.continuous)capture(c.name);
          }return out;
        }''',dict(cases=fixtures,fields=FIELDS))
        browser.close()
    checks=[]
    for e in expected:
        name=e['name'];a=actual[name];image=Image.open(output/(name+'.png')).convert('RGB');reference=Image.open(io.BytesIO(base64.b64decode(e['png']))).convert('RGB')
        delta=ImageChops.difference(image,reference);pixels=0 if image.tobytes()==reference.tobytes() else sum(x!=y for x,y in zip(image.getdata(),reference.getdata()))
        if pixels:delta.save(output/(name+'-diff.png'));reference.save(output/(name+'-js.png'))
        diff={k:dict(actual=a['state'].get(k),expected=v) for k,v in e['state'].items() if a['state'].get(k)!=v}
        checks.append(dict(name=name,different_pixels=pixels,bounds=delta.getbbox(),differences=diff,sound_passed=a['sounds']==e['sounds'],passed=not pixels and not diff and a['sounds']==e['sounds']))
    report=dict(passed=len(checks)==len(actual) and all(c['passed'] for c in checks),checks=checks,scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[dict(name=c['name'],pixels=c['different_pixels'],fields=list(c['differences']),sound=c['sound_passed']) for c in checks if not c['passed']][:25]),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
