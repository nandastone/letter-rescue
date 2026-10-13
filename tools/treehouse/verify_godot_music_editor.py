"""Replay the original two-book composing journey through Godot input handlers.

One initial native fixture, then the recorded clicks, drags and key events.
Checks complete image membership in each input interval and active song records,
titles, selections, insertion marker and shared RNG. Device audio and exact
presentation time are outside this check.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT
from verify_music_native_journey import active_song


def verify(engine,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    initial=dict(native['checkpoints'][0]['after'])
    ram=(reference/'state/initial.ram-0').read_bytes()
    initial['idleCountdown']=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]-initial['tick']
    initial['listeningPreferences']=[list(ram[544+0x2f180+o:544+0x2f180+o+50]) for o in (0x75f,0x791,0x7c3)]
    fixture=dict(initial=initial,checkpoints=native['checkpoints'],reference=str(reference.resolve()))
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    result=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_music.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=240)
    log=result.stdout+result.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    if result.returncode or 'ERROR' in log:raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    checks=[]
    for result,checkpoint in zip(actual,native['checkpoints']):
        a=result['actual'];e=checkpoint['after'];mode=int(e['advanced'])
        fields=['seed','composing','advanced']+(['title','marker'] if e['composing'] else [])
        differences={k:dict(actual=a[k],expected=e[k]) for k in fields if a[k]!=e[k]}
        if not a['composing']:a['song'][2:4]=[a['tempo'],a['instrument']]
        es=active_song(e['song'],mode);gs=active_song(a['song'],mode)
        if es!=gs:differences['active_song']=dict(actual=gs,expected=es)
        i=2*mode+int(e['composing'])
        if e['selection'][i]!=a['selection'][i]:differences['selection']=dict(actual=a['selection'][i],expected=e['selection'][i])
        image=Image.open(output/(checkpoint['name']+'.png')).convert('RGB')
        original=Image.open(reference/'state'/(checkpoint['name']+'.png')).convert('RGB')
        delta=ImageChops.difference(image,original)
        pixels=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
        if pixels:delta.save(output/(checkpoint['name']+'-diff.png'))
        checks.append(dict(name=checkpoint['name'],different_pixels=pixels,bounds=delta.getbbox(),differences=differences,matched_tick=result['matched_tick'],passed=not pixels and not differences))
    report=dict(passed=len(actual)==len(native['checkpoints']) and all(c['passed'] for c in checks),checks=checks,scope=__doc__,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/music-native-journey-d')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.reference) else 1)
