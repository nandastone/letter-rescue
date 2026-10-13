"""Replay a complete original board game in Godot from one initial snapshot.

Recorded pointer choices run without resetting gameplay or RNG. Full native
checkpoint RGB membership in the production scanout output and state are required. Each action settles and then
observes 420 ticks, as in the existing reference verifier; this is not exact
native input/presentation timing or output audio waveform evidence. Scanout is
fed logical-tick framebuffer commits; original drawing/loading work and absolute
video phase are not reconstructed by this comparison.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT
from verify_board_native_journey import model

def verify(engine,output,reference,observe=''):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['complete'] and native['passed']
    names=['initial']+[d['name'] for d in native['decisions']]
    initial=model(reference/'state/initial.ram-0')
    initial.update(options=False,played=True,phase='move' if initial['remaining']>0 else 'ready',hintRed=initial['remaining']<0)
    checkpoints=[]
    for name in names:
        ram=(reference/'state'/(name+'.ram-0')).read_bytes();y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        checkpoints.append(dict(name=name,point=[x,y],expected=model(reference/'state'/(name+'.ram-0'))))
    fixture=dict(initial=initial,checkpoints=checkpoints,reference=str(reference.resolve()),observe=observe)
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    with (output/'godot.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_board.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=240)
    log=(output/'godot.log').read_text(encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:8000])
    actual=json.loads((output/'godot.json').read_text());checks=[]
    for a,e in zip(actual['checkpoints'],checkpoints):
        image=Image.open(output/(a['name']+'.png')).convert('RGB');expected=Image.open(reference/'state'/(a['name']+'.png')).convert('RGB')
        delta=ImageChops.difference(image,expected);pixels=sum(x!=y for x,y in zip(image.getdata(),expected.getdata()))
        if pixels:delta.save(output/(a['name']+'-diff.png'))
        diff={k:dict(actual=a['actual'].get(k),expected=v) for k,v in e['expected'].items() if a['actual'].get(k)!=v}
        checks.append(dict(name=a['name'],different_pixels=pixels,bounds=delta.getbbox(),differences=diff,completed=a['completed'],matched_tick=a['matched_tick'],matched_presentation_ms=a['matched_presentation_ms'],passed=not pixels and not diff and a['completed']))
    report=dict(passed=actual['ending'] and len(checks)==len(checkpoints) and all(c['passed'] for c in checks),ending=actual['ending'],checks=checks,presented_frames=actual['presented_frames'],scope=__doc__,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest())
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[dict(name=c['name'],pixels=c['different_pixels'],fields=list(c['differences'])) for c in checks if not c['passed']]),indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--observe',default='',help='Save every changed production presentation in this checkpoint for diagnosis.')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.reference,a.observe) else 1)
