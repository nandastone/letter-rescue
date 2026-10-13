"""Capture original earned egg, airplane and caterpillar interactions."""
from pathlib import Path
import argparse
import ctypes as C
import json
import struct
from capture import Recorder, digest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'testing/output/treehouse'


def state(native):
    native.snapshot_boundary()
    pointer, length = next((p+o, l) for s, p, o, l in native.memory if s == 0 and p)
    ram = C.string_at(pointer, length)
    ds, shared = 0x323f0, 0x318b0
    w = lambda off: struct.unpack_from('<h', ram, ds+off)[0]
    u = lambda off: struct.unpack_from('<I', ram, ds+off)[0]
    sw = lambda off: struct.unpack_from('<h', ram, shared+off)[0]
    return dict(tick=u(0x201e), seed=u(0x5290), pointer=[w(0x2066), w(0x2064)], scene=sw(0xb34),
                date=[w(0x52ce), ram[ds+0x52cd], ram[ds+0x52cc]], calendarOpen=bool(w(0x5262)), chalkTool=w(0x15e8)-1,
                selected=bool(w(0x5692)), sex=sw(0xa14), cloud=sw(0xb4), cloudX=sw(0xa18), outsideCycle=w(0x5570),
                pose=w(0x5688), hunger=w(0x5282), fatigue=w(0x581c), windowRemaining=w(0x201a),
                ambientDue=u(0x531c), longDue=u(0x5318), hungerDue=u(0x568e), fatigueDue=u(0x5576),
                objects=[dict(type=w(0x5830+20*i), state=w(0x5832+20*i), inside=bool(w(0x5834+20*i)),
                              rect=[w(0x5836+20*i+2*j) for j in range(4)], due=u(0x5840+20*i)) for i in range(w(0x556c))])


def capture(output, kind, gesture="click"):
    output.mkdir(parents=True, exist_ok=False)
    core = DATA/'capture-core/dosbox_pure_libretro.dll'
    content = DATA/'source/reference-v1.zip'
    origin = DATA/('research-object-completion/clicks/state/disc-room.state' if kind == 0 else f'research-object-completion/flight-prizes/state/room-{kind}.state')
    report = dict(complete=False, passed=False, kind=kind, gesture=gesture, core_sha256=digest(core), content_sha256=digest(content),
                  restore_source=str(origin), restore_sha256=digest(origin), tool_sha256=digest(Path(__file__)), actions=[], checkpoints=[])
    native = None
    try:
        native = Recorder(core, content, output)
        native.perform([dict(frames=1800)])
        native.restore(origin); native.image_base = 544
        pending = []

        def action(frames, point=None, left=False):
            before = state(native); mouse = dict(left=left)
            if point:
                mouse.update(dx=2*(point[0]-before['pointer'][0]), dy=2*(point[1]-before['pointer'][1]))
            entry = dict(frames=frames, mouse=mouse); report['actions'].append(entry)
            native.perform([entry]); after = state(native)
            pending.append(dict(from_tick=before['tick'], to_tick=after['tick'], point=after['pointer'], left=left))

        def checkpoint(name):
            native.save(name, ram=True); after = state(native)
            report['checkpoints'].append(dict(name=name, inputs=pending[:], after=after)); pending.clear()
            print(name, after['seed'], [(o['type'], o['state'], o['rect']) for o in after['objects'] if o['type'] == kind], flush=True)
            return after

        def center(model):
            r = next(o['rect'] for o in model['objects'] if o['type'] == kind)
            return [(r[1]+r[3])//2, (r[0]+r[2])//2]

        native.perform([dict(frames=60)])
        initial = checkpoint('initial')
        assert initial['scene'] == 5 and initial['selected'] and initial['pose'] == 0
        if kind == 0 and gesture == 'drag':
            action(30, center(initial)); action(25, left=True)
            action(20, [190,110], left=True); checkpoint('held')
            action(20); checkpoint('released')
            action(400); final = checkpoint('settled')
        elif kind == 0:
            action(30, center(initial)); action(15, left=True); checkpoint('pressed')
            action(30); checkpoint('cracked')
            action(40); checkpoint('head')
            action(15); checkpoint('hatching')
            action(50); checkpoint('flying')
            action(1000); final = checkpoint('departed')
            assert [next(o['state'] for o in c['after']['objects'] if o['type']==0) for c in report['checkpoints'][:-1]] == [1,1,2,3,4,5]
        else:
            action(30, center(initial)); action(25, left=True)
            action(20, [140,55] if kind == 1 else [169,145], left=True)
            checkpoint('held')
            action(25 if kind == 1 else 80); checkpoint('released')
            action(400 if kind == 1 else 1000); settled = checkpoint('settled')
            if kind == 1:
                assert any(o['type'] == kind for o in settled['objects'])
                action(20, center(settled)); action(1, left=True); action(1000)
                final = checkpoint('departed')
            else:
                final = settled
        assert not any(o['type'] == kind for o in final['objects'])
        report.update(complete=True, passed=True, snapshot_boundary_version=native.snapshot_boundary_version, video_callbacks=native.callback_index)
    finally:
        if native:
            native.close()
        if (output/'frames.jsonl').exists():
            report['timeline_sha256'] = digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--kind', type=int, choices=[0,1,5], required=True)
    p.add_argument('--gesture', choices=['click','drag'], default='click')
    args = p.parse_args()
    raise SystemExit(0 if capture(args.output, args.kind, args.gesture) else 1)
