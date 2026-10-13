"""Compare Godot nature composition and continuous behavior to the JS reference.

Whole RGB frames, reported gameplay/RNG state and sound dispatch are compared.
These port consistency checks do not prove native presentation/audio parity.
"""
import argparse,base64,hashlib,io,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def cases():
    data=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
    result=[]
    for time in range(2):
        for attribute in range(7):
            for value in range(len(data['strings'][f'modules:{5200+attribute}'])):
                values=[0]*7;values[attribute]=value
                classes=sorted(set(a['category'] for a in data['nature']['animals'] if a['active_time']==time and a['attributes'][attribute]==value))
                for category in classes:
                    result.append(dict(name=f'filter-{time}-{attribute}-{value}-{category}',state=dict(time=time,attribute=attribute,values=values,category=category)))
    for a in data['nature']['animals']:
        for fact in range(len(data['strings'][f"modules:{5100+a['id']}"])):
            values=[0]*7;values[0]=a['attributes'][0]
            result.append(dict(name=f"animal-{a['id']}-fact-{fact}",state=dict(time=a['active_time'],attribute=0,values=values,category=a['category'],selected=a['id'],factIndex=fact,factOpen=True),actions=[['add_animal',a['id']]]))
    for character in ['boy','girl']:
        for opponent in [1,2]:
            for enabled in [False,True]:
                result.append(dict(name=f'options-{character}-{opponent}-{enabled}',character=character,state=dict(mode='quiz'),quiz=dict(opponent=opponent,help=[enabled,enabled,True])))
        for selected in range(92):
            result.append(dict(name=f'card-{character}-{selected}',character=character,state=dict(mode='quiz'),quiz=dict(options=False,phase='question',player=0,cards=[[selected,1,2,3,4,5,6,7],[8,9,10,11,12,13,14,15]],secret=[0,0],selected=0,available=[0,4,7])))
        for attribute in range(8):
            result.append(dict(name=f'definition-{character}-{attribute}',character=character,state=dict(mode='quiz'),quiz=dict(options=False),actions=[['q_inspect_attribute',attribute]]))
        actions=[['enter_quiz'],['q_set','opponent',1],['q_start'],['q_inspect_attribute',4],['advance',12],['q_roll'],['advance',250],['smart_ask'],['advance',1000],['q_roll'],['advance',250],['q_cross_out',0],['advance',25],['q_cross_out',0],['advance',25],['q_toggle_guess'],['advance',220],['smart_guess',1],['advance',1000],['q_roll'],['advance',250],['q_toggle_guess'],['advance',220],['smart_guess',0],['advance',1400],['q_inspect_winner',0],['advance',250],['q_inspect_winner',1],['advance',250]]
        result.append(dict(name=f'continuous-{character}',character=character,continuous=True,actions=actions))
    result.append(dict(name='robot-help',continuous=True,actions=[['enter_quiz'],['q_set','help',[True,True,True]],['q_start'],['q_roll'],['advance',250],['smart_ask'],['advance',1600],['q_roll'],['advance',2400],['q_roll'],['advance',250],['q_toggle_guess'],['advance',220],['smart_guess',0],['advance',1500]]))
    for opponent in [1,2]:
        result.append(dict(name=f'opponent-victory-{opponent}',continuous=True,state=dict(mode='quiz'),quiz=dict(options=False,opponent=opponent,phase='question',player=1,cards=[[0,1,2,3,4,5,6,7],[8,9,10,11,12,13,14,15]],secret=[0,0],available=[0,4,7]),actions=[['smart_guess',0],['advance',1400],['q_inspect_winner',0],['advance',250]]))
    result.append(dict(name='collage',continuous=True,actions=[['add_animal',36],['add_animal',14],['advance',1300],['toggle_time'],['add_animal',60],['advance',400],['toggle_time'],['begin_drag',210,115],['move_drag',20,130],['end_drag'],['request_clear'],['advance',24],['answer_dialog',True],['advance',40],['undo_clear'],['advance',300]]))
    return result


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False);fixtures=cases()
    (output/'cases.json').write_text(json.dumps(fixtures),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_nature.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=300)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:8000])
    observed={c['name']:c for c in json.loads((output/'godot.json').read_text())}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''cases=>{
          const result=[],camel=s=>s.replace(/_([a-z])/g,(_,c)=>c.toUpperCase());
          for(const c of cases){
            gameplayRandom.reset(123456);let sounds=[],dialog=null;
            const n=new NatureActivity(store,{character:()=>c.character||'boy',confirm:(message,yes)=>{dialog={message,yes,start:n.tick};},speak:(id,requested,options={})=>{const key=ORIGINAL.pcm[`digisnd:${id}`]?`digisnd:${id}`:`voices:${id}`,sample=ORIGINAL.pcm[key];if(!sample)return 0;const rate=Math.floor(1e6/Math.floor(1e6/(requested||sample.rate))),duration=bytes(sample.pcm).length/rate*TICK_HZ;sounds.push({tick:n.tick,key,rate,duration:Math.ceil(duration)});return options.fractional?duration:Math.ceil(duration);}});
            Object.assign(n,c.state||{});Object.assign(n.quiz,c.quiz||{});let index=0;
            const capture=name=>{n.draw(screen);
              if(dialog){const oldPreferences=preferences,oldTick=tick;preferences={kind:'question',message:dialog.message,yes:dialog.yes,start:dialog.start,background:screen.clone()};tick=n.tick;drawQuestion();tick=oldTick;preferences=oldPreferences;}
              const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);
              const state={nature:{},quiz:{},seed:gameplayRandom.seed};for(const key of ['time','attribute','values','category','selected','factIndex','factOpen','objects'])state.nature[key]=n[key];for(const key of ['cards','secret','remaining','asked','player','available','phase','guessing','winner','options','selected','selectedAttribute','answer','explanation','winStage'])state.quiz[key]=n.quiz[key]??null;
              result.push({name,state:JSON.parse(JSON.stringify(state)),sounds:JSON.parse(JSON.stringify(sounds)),png:canvas.toDataURL().split(',')[1]});};
            for(const [method,...args]of c.actions||[]){
              if(method==='advance'){for(let i=0;i<args[0];i++){if(dialog)n.tick++;else n.update(n.tick+1);if(c.continuous&&(i%12===11||i===args[0]-1))capture(c.name+'-'+String(index++).padStart(4,'0'));}}
              else if(method==='smart_ask')n.quiz.ask(n.quiz.available[0]);
              else if(method==='smart_guess')n.quiz.guess((n.quiz.secret[n.quiz.player]+args[0])%8);
              else if(method==='q_set')n.quiz[camel(args[0])]=args[1];
              else if(method.startsWith('q_'))n.quiz[camel(method.slice(2))](...args);
              else if(method==='answer_dialog'){const old=dialog;dialog=null;if(args[0])old.yes?.();}
              else n[camel(method)](...args);
              if(c.continuous&&method!=='advance')capture(c.name+'-'+String(index++).padStart(4,'0'));
            }
            if(!c.continuous)capture(c.name);
          }return result;
        }''',fixtures)
        browser.close()
    checks=[]
    for c in expected:
        name=c['name'];image=Image.open(output/(name+'.png')).convert('RGB');reference=Image.open(io.BytesIO(base64.b64decode(c['png']))).convert('RGB')
        delta=ImageChops.difference(image,reference);pixels=sum(a!=b for a,b in zip(image.getdata(),reference.getdata()))
        if pixels:delta.save(output/(name+'-diff.png'));reference.save(output/(name+'-js.png'))
        diff={k:dict(expected=v,actual=observed[name]['state'].get(k)) for k,v in c['state'].items() if v!=observed[name]['state'].get(k)}
        checks.append(dict(name=name,different_pixels=pixels,bounds=delta.getbbox(),state_diff=diff,sound_passed=c['sounds']==observed[name]['sounds'],passed=not pixels and not diff and c['sounds']==observed[name]['sounds']))
    report=dict(passed=len(observed)==len(checks) and all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[dict(name=c['name'],pixels=c['different_pixels'],fields=list(c['state_diff']),sound=c['sound_passed']) for c in checks if not c['passed']][:25]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
