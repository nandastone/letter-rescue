"""Replay a restored game through the ordinary adapter in fresh processes.

Requires exact callback order, full RGB images, PIT clocks and audio against
both a second capture and the established read-only trace control. No trace
extension is required by the ordinary capture core.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, struct, subprocess, sys
from capture import Recorder, digest
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture(core, output):
    output.mkdir(parents=True,exist_ok=False)
    origin=DATA/'research-nature/quiz-answer-capture/state/quiz-answer.state'
    native=Recorder(core,DATA/'source/reference-v1.zip',output)
    try:
        native.perform([dict(frames=1800)])
        native.restore(origin)
        pointer=next(p+o for s,p,o,l in native.memory if s==0 and p)
        py,px=struct.unpack('<hh',C.string_at(pointer+0x34454,4))
        actions=[dict(frames=15,mouse=dict(dx=2*(150-px),dy=2*(20-py)),capture='before'),
                 dict(frames=1,mouse=dict(left=True)),dict(frames=1300,capture='after')]
        native.perform(actions)
    finally:
        native.close()
    report=dict(snapshot_boundary_version=native.snapshot_boundary_version,
                core_sha256=digest(core),origin_sha256=digest(origin),actions=actions,
                adapter_sha256=digest(Path(__file__).with_name('libretro.py')),
                callbacks=native.callback_index,passed=native.callback_index==3116)
    (output/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


def timeline(folder):
    rows=[json.loads(line) for line in (folder/'frames.jsonl').read_text().splitlines()]
    if len(rows)!=3116:raise ValueError('Incomplete callback timeline')
    seen=set()
    for i,r in enumerate(rows):
        if r['run']!=i or r['callback']!=i:raise ValueError('Missing/reordered callback')
        path=(folder/r['image']).resolve()
        if not path.is_relative_to(folder.resolve()):raise ValueError('Frame outside evidence')
        if path not in seen:
            image=Image.open(path).convert('RGB')
            if image.size!=(r['width'],r['height']) or hashlib.sha256(image.tobytes()).hexdigest()!=r['rgb_sha256']:
                raise ValueError('Corrupt callback image')
            seen.add(path)
    return [{k:r[k] for k in ['run','callback','width','height','original_tick','rgb_sha256']} for r in rows]


def verify(core,reference,output):
    output.mkdir(parents=True,exist_ok=False)
    for name in ['first','repeat']:
        result=subprocess.run([sys.executable,__file__,'--capture','--core',str(core),'--output',str(output/name)],capture_output=True,text=True)
        (output/f'{name}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'Capture failed; see {name}.log')
    captures=[reference,output/'first',output/'repeat']
    rows=[timeline(p) for p in captures]
    audio=[digest(p/'state/audio.wav') for p in captures]
    checks=[dict(name='same complete callback pixels and clocks as established reference',passed=rows[0]==rows[1]),
            dict(name='fresh ordinary replay is repeatable',passed=rows[1]==rows[2]),
            dict(name='all captured audio bytes identical',passed=len(set(audio))==1),
            dict(name='both ordinary captures use snapshot protocol 2',passed=all(json.loads((p/'run.json').read_text())['snapshot_boundary_version']==2 for p in captures[1:]))]
    report=dict(core_sha256=digest(core),adapter_sha256=digest(Path(__file__).with_name('libretro.py')),
                reference=str(reference),callbacks=3116,checks=checks,passed=all(c['passed'] for c in checks))
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,default=DATA/'capture-core/dosbox_pure_libretro.dll')
    p.add_argument('--reference',type=Path,default=DATA/'nature-redraw-control-a')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--capture',action='store_true');a=p.parse_args()
    if a.capture:capture(a.core,a.output)
    else:sys.exit(0 if verify(a.core,a.reference,a.output) else 1)
