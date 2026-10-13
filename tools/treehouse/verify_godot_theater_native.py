"""One original theater-options snapshot, then recorded DOS inputs through shuffle.

Checks complete RGB checkpoint membership within the corresponding input
interval and end-of-interval gameplay/RNG state. Room entry/exit, exact frame
timing and output audio waveform equality are outside this replay's scope.
"""
import argparse,datetime,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT


def verify(engine,output,reference,room=False):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['passed'] and native['complete']
    checkpoints=native['checkpoints'] if room else native['checkpoints'][1:-1]
    checkpoints[0]=dict(checkpoints[0],inputs=[])
    fixture=dict(initial=checkpoints[0]['after'],checkpoints=checkpoints,reference=str(reference.resolve()))
    if room:
        ram=(reference/'state/initial.ram-0').read_bytes();low=(reference/'state/initial.ram-100000').read_bytes()
        ds=0x323f0;shared=0x318b0
        w=lambda off:struct.unpack_from('<h',ram,off)[0]
        u=lambda off:struct.unpack_from('<I',ram,off)[0]
        fixture['room']=dict(time=int(datetime.datetime(1992,1,1,tzinfo=datetime.timezone.utc).timestamp()+struct.unpack_from('<I',low,0x46c)[0]*65536/1193181),
            cloud=w(shared+0xb4),cloud_x=w(shared+0xa18),cloud_due=w(ds+0x201a),pose=w(ds+0x5688),hunger=w(ds+0x5282),fatigue=w(ds+0x581c),
            ambient_due=u(ds+0x531c),long_due=u(ds+0x5318),hunger_due=u(ds+0x568e),fatigue_due=u(ds+0x5576),
            objects=[dict(type=w(ds+0x5830+20*i),state=w(ds+0x5832+20*i),inside=bool(w(ds+0x5834+20*i)),rect=[w(ds+0x5836+20*i+2*j) for j in range(4)],due=u(ds+0x5840+20*i)) for i in range(w(ds+0x556c))])
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_theater.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=240)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:6000])
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'));checks=[]
    for a,e in zip(actual,checkpoints):
        expected=dict(e['after'])
        expected['props']=[[dict(id=(3175 if p['encoded']>>8 else 3145)+(p['encoded']&255),palette=3175 if p['encoded']>>8 else 3145,x=p['rect'][1],y=p['rect'][0]) for p in items] for items in expected['props']]
        diff={k:dict(actual=v,expected=expected[k]) for k,v in a['actual'].items() if v!=expected[k]}
        image=Image.open(output/(a['name']+'.png')).convert('RGB');original=Image.open(reference/'state'/(a['name']+'.png')).convert('RGB')
        delta=ImageChops.difference(image,original);pixels=sum(x!=y for x,y in zip(image.getdata(),original.getdata()))
        if pixels:delta.save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,bounds=delta.getbbox(),differences=diff,matched_tick=a['matched_tick'],passed=not pixels and not diff))
    scope=__doc__ if not room else 'One original room snapshot, then the complete recorded room/theater/return pointer journey. Full checkpoint image membership and reported theater gameplay/RNG fields; exact timing and output audio waveform parity remain unproven.'
    report=dict(passed=len(actual)==len(checkpoints) and all(c['passed'] for c in checks),checks=checks,scope=scope,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/theater-native-journey-e')
    p.add_argument('--room',action='store_true')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.reference,a.room) else 1)
