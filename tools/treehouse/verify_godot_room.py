"""Replay bounded original room journeys in Godot; report full-image differences.

One native initial room/time fixture is supplied. Game ticks drive subsequent
inputs. This verifies calendar/cloud/chalk/balloon fields and image membership, not
unported resident RNG, object lifecycles, strict display timing or audio parity.
"""
import argparse
import datetime
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageChops
from build_demo import ROOT


def verify(engine,output,start,stop,portrait,reference,objects=False):
    output.mkdir(parents=True,exist_ok=False)
    native = json.loads((reference/'run.json').read_text(encoding='utf-8'))
    checkpoints = native['checkpoints']
    checkpoints = checkpoints[next(i for i,c in enumerate(checkpoints) if c['name']==start):]
    checkpoints = checkpoints[:next(i for i,c in enumerate(checkpoints) if c['name']==stop)+1]
    checkpoints[0] = dict(checkpoints[0],inputs=[])
    ram = (reference/'state'/f'{start}.ram-0').read_bytes()
    low = (reference/'state'/f'{start}.ram-100000').read_bytes()
    seconds = struct.unpack_from('<I',low,0x46c)[0]*65536/1193181
    time = int(datetime.datetime(1992,1,1,tzinfo=datetime.timezone.utc).timestamp()+seconds)
    initial = dict(checkpoints[0]['after'])
    initial.setdefault('date',[1992,1,1])
    initial.setdefault('calendarOpen',False)
    initial.setdefault('chalkTool',-1)
    fixture = dict(reference=str(reference.resolve()),initial=initial,checkpoints=checkpoints,check_objects=objects,
                   time=time,cloud_x=struct.unpack_from('<h',ram,0x318b0+0xa18)[0],portrait_frame=portrait)
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    process = subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_room.gd','--',str(output.resolve())],
                             capture_output=True,text=True,encoding='utf-8',timeout=240)
    log = process.stdout+process.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    print(log)
    if process.returncode or 'ERROR' in log:
        raise RuntimeError('Godot replay failed; see godot.log')
    report = json.loads((output/'godot.json').read_text(encoding='utf-8'))
    for c in report['checkpoints']:
        original = Image.open(reference/'state'/(c['name']+'.png')).convert('RGB')
        actual = Image.open(output/(c['name']+'.png')).convert('RGB')
        difference = ImageChops.difference(original,actual)
        c['different_pixels'] = sum(a!=b for a,b in zip(original.getdata(),actual.getdata()))
        c['bounds'] = difference.getbbox()
        difference.save(output/(c['name']+'-diff.png'))
    report['scope'] = __doc__
    if objects:
        report['scope'] += ' Also compares shared RNG and all object types/states/scenes/rectangles, sorted by type; storage order is reported. Held objects retain their stored drag origin in this state comparison; full images check their displayed position. Sound device output is disabled; sample durations still drive deadlines.'
    report['reference_sha256'] = hashlib.sha256((reference/'run.json').read_bytes()).hexdigest()
    report['files'] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))}
    report['passed'] = all(c['passed'] for c in report['checkpoints'])
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k in ['passed','checkpoints']},indent=2))
    return report['passed']


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--start',default='initial')
    parser.add_argument('--stop',default='cloud-changed')
    parser.add_argument('--portrait',type=int,default=0)
    parser.add_argument('--objects',action='store_true')
    parser.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/room-native-journey-c')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot,args.output,args.start,args.stop,args.portrait,args.reference,args.objects) else 1)
