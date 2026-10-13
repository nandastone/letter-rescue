"""Check four Godot telescope views and native robot shelf, plus production input.

Both children visit all four randomly selected views through room controls.
Mouse/touch replay/exit and animation input ownership are checked. Full final
RGB images are compared with the original. The populated shelf is an explicitly
isolated fixture; reward integration, exact timing and audio waveform remain
separate requirements.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT

def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    base=ROOT/'testing/output/treehouse'
    native=base/'telescope-views-native-b'
    robot=base/'robot-prize-native-a'
    views=json.loads((native/'run.json').read_text(encoding='utf-8'))
    shelf=json.loads((robot/'run.json').read_text(encoding='utf-8'))
    assert views['passed'] and shelf['passed']
    cases=sorted((c for c in views['checkpoints'] if c.get('view') is not None),key=lambda c:c['view'])
    robot_case=next(c for c in shelf['checkpoints'] if c['name']=='shelf-first-visit')
    fixture=dict(views=[c['after'] for c in cases],shelf=robot_case['after'])
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        result=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_telescope.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=180)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if 'ERROR' in log:raise RuntimeError(log[:6000])
    controls=json.loads((output/'controls.json').read_text())
    images=[]
    comparisons=[(f'{who}-view-{c["view"]}',native/'state'/(c['name']+'.png')) for who in ['mouse-boy','touch-girl'] for c in cases]
    comparisons.append(('robot-shelf',robot/'state'/(robot_case['name']+'.png')))
    for name,path in comparisons:
        actual=Image.open(output/(name+'.png')).convert('RGB');expected=Image.open(path).convert('RGB')
        delta=ImageChops.difference(actual,expected)
        count=sum(a!=b for a,b in zip(actual.getdata(),expected.getdata()))
        if count:delta.save(output/(name+'-diff.png'))
        images.append(dict(name=name,different_pixels=count,bounds=delta.getbbox(),passed=count==0,reference=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    report=dict(passed=result.returncode==0 and controls['passed'] and all(c['passed'] for c in images),controls=controls,images=images,scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],controls=len(controls['checks']),images=images),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
