"""Replay original collage editing or quiz inputs in the production Godot runtime.

One initial native fixture, then ordinary recorded pointer/tick intervals. Check
full checkpoint image membership and active gameplay/RNG fields. Quiz scope ends
after both hidden animals are revealed; prize/room integration remains required.
Exact display timing and output audio waveform parity are separate requirements.
"""
import argparse,datetime,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT


def verify(engine,output,kind,reference=None,until='other-animal'):
    if reference is None:reference=ROOT/'testing/output/treehouse'/('nature-edit-native-a' if kind=='edit' else 'nature-native-journey-c')
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['complete'] and native['passed']
    checkpoints=native['checkpoints']
    if kind=='quiz':
        checkpoints=checkpoints[next(i for i,c in enumerate(checkpoints) if c['name']=='initial'):]
        checkpoints=checkpoints[:next(i for i,c in enumerate(checkpoints) if c['name']==until)+1]
    fixture=dict(kind=kind,initial=checkpoints[0]['after'],checkpoints=checkpoints,reference=str(reference.resolve()))
    if kind=='quiz':
        ram=(reference/'state/initial.ram-0').read_bytes();low=(reference/'state/initial.ram-100000').read_bytes();ds=0x323f0
        w=lambda off:struct.unpack_from('<h',ram,off)[0]
        u=lambda off:struct.unpack_from('<I',ram,off)[0]
        shared=(w(ds+0x4ada)&65535)*16-0x1860
        fixture['room']=dict(time=int(datetime.datetime(1992,1,1,tzinfo=datetime.timezone.utc).timestamp()+struct.unpack_from('<I',low,0x46c)[0]*65536/1193181),cloud=w(shared+0xb4),cloud_x=w(shared+0xa18),pose=w(ds+0x5688),hunger=w(ds+0x5282),fatigue=w(ds+0x581c),ambient_due=u(ds+0x531c),long_due=u(ds+0x5318),hunger_due=u(ds+0x568e),fatigue_due=u(ds+0x5576))
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_nature.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=240)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:5000])
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'));checks=[]
    for a,e in zip(actual,checkpoints):
        expected=dict(e['after'])
        if kind=='quiz' and (expected['answered']!=0 or expected['win_phase']!=0):expected['available']=[]
        fields=list(a['actual'])
        if kind=='quiz':
            fields=['seed','scene']
            fields += [key for key in ['shelf','visited_mask'] if key in expected]
            if expected['scene']==9:fields+=['cards','secret','opponent','help','player','asked','remaining','available','answered','guessing','win_phase']
            if expected['scene']==9 and expected['win_phase']:fields+=['winner']
            if e['name']=='prize-chooser':fields+=['prize_choices']
            if expected['scene']==5:fields+=['objects']
        diff={k:dict(actual=a['actual'].get(k),expected=expected[k]) for k in fields if a['actual'].get(k)!=expected[k]}
        image=Image.open(output/(a['name']+'.png')).convert('RGB');original=Image.open(reference/'state'/(a['name']+'.png')).convert('RGB')
        delta=ImageChops.difference(image,original);pixels=sum(x!=y for x,y in zip(image.getdata(),original.getdata()))
        if pixels:delta.save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,bounds=delta.getbbox(),differences=diff,matched_tick=a['matched_tick'],passed=not pixels and not diff))
    scope=__doc__ if until=='other-animal' else 'One original quiz and room-state fixture, then the complete recorded input journey through victory, prize choice/delivery, a fresh game, nature exploration and room return. Full checkpoint RGB membership and active quiz/RNG/scene fields, plus room objects at return. Exact presentation and audio waveform parity remain unproven.'
    report=dict(passed=len(actual)==len(checkpoints) and all(c['passed'] for c in checks),checks=checks,scope=scope,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--kind',choices=['edit','quiz'],required=True);p.add_argument('--reference',type=Path)
    p.add_argument('--until',default='other-animal')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.kind,a.reference,a.until) else 1)
