"""Compare Godot maze generation and a continuous original route through victory.

Generation cases use isolated native seeds/states. The playable journey receives
one initial native maze state then ordinary pointer choices; it waits for each
operation to finish. Full settled images/state/RNG and an in-progress victory
highlight are required. Exact timing, fresh entry and audio output are separate.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT
from verify_maze_generation import model


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    data=ROOT/'testing/output/treehouse'
    ref=data/'research-music-maze/playthrough/state'
    initial=model(ref/'settled.ram-0')
    ram=(ref/'settled.ram-0').read_bytes();y,x,_,_=struct.unpack_from('<4h',ram,0x318b0+0x9ba)
    initial.update(actor=[y+40,x+17],earned=ram[0x318b0+0x9e6],phase='play',frog=False)
    generation=[]
    for i in range(7):
        generation.append(dict(name=f'challenge-{i}',initial=model(ref/(('wrong' if i==0 else f'correct-{i-1}')+'.ram-0')),expected=model(ref/f'correct-{i}.ram-0')))
    intro=data/'research-maze-completion/intro-capture/state'
    generation.append(dict(name='first-easy-challenge',initial=model(intro/'intro-06.ram-0'),expected=model(intro/'intro-07.ram-0'),first=True))
    checkpoints=[]
    for name in ['settled','wrong']+[f'correct-{i}' for i in range(8)]:
        ram=(ref/(name+'.ram-0')).read_bytes();y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        target=data/'maze-victory-tail-b/state/tail-0' if name=='correct-7' else ref/name
        expected=model(target.with_suffix('.ram-0'));expected['earned']=target.with_suffix('.ram-0').read_bytes()[0x318b0+0x9e6]
        checkpoints.append(dict(name=name,pointer=[x,y],expected=expected,reference=str(target.with_suffix('.png'))))
    fixture=dict(initial=initial,generation=generation,checkpoints=checkpoints,highlight=str(ref/'correct-7.png'))
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_maze.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=240)
    log=p.stdout+p.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    checks=[]
    generation_fields=['seed','hard','excluded','typeHistory','patternHistory','familyHistory','type','correct','choices']
    journey_fields=generation_fields+['streak','songs','history','secret','node','earned']
    for group,fields in [('generation',generation_fields),('checkpoints',journey_fields)]:
        for a,e in zip(actual[group],fixture[group]):
            selected=fields+(['secret','node'] if e.get('first') else [])
            diff={k:dict(actual=a['actual'][k],expected=e['expected'][k]) for k in selected if a['actual'][k]!=e['expected'][k]}
            check=dict(name=a['name'],differences=diff,passed=not diff)
            if group=='checkpoints':
                image=Image.open(output/(a['name']+'.png')).convert('RGB');native=Image.open(e['reference']).convert('RGB')
                delta=ImageChops.difference(image,native);pixels=sum(x!=y for x,y in zip(image.getdata(),native.getdata()))
                if pixels:delta.save(output/(a['name']+'-diff.png'))
                check.update(different_pixels=pixels,bounds=delta.getbbox(),passed=not diff and not pixels,elapsed=a['elapsed'])
            checks.append(check)
    checks.append(dict(name='original in-progress victory highlight generated',passed=actual['highlight']))
    checks.append(dict(name='journey reaches completed victory',passed=actual['checkpoints'][-1]['actual']['phase']=='win' and not actual['checkpoints'][-1]['actual']['busy']))
    report=dict(passed=len(actual['generation'])==len(generation) and len(actual['checkpoints'])==len(checkpoints) and all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
