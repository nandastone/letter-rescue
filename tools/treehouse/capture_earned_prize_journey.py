"""Continue the recorded quiz win with ordinary inputs on its earned room toy."""
from pathlib import Path
import argparse
import json
from capture import Recorder, digest
from capture_prize_object_journey import DATA, state


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    parent = DATA/'nature-native-journey-c'
    source = parent/'state/back-to-room.state'
    prior = json.loads((parent/'run.json').read_text(encoding='utf-8'))
    assert prior['complete'] and prior['passed'] and prior['selected_prize']['type'] == 2
    report = dict(complete=False, passed=False, parent=str(parent),
                  parent_report_sha256=digest(parent/'run.json'), restore_source=str(source),
                  restore_sha256=digest(source), tool_sha256=digest(Path(__file__)),
                  actions=[], checkpoints=[])
    native = None
    try:
        core, content = DATA/'capture-core/dosbox_pure_libretro.dll', DATA/'source/reference-v1.zip'
        report.update(core_sha256=digest(core), content_sha256=digest(content))
        native = Recorder(core, content, output)
        native.perform([dict(frames=1800)])
        native.restore(source)
        native.image_base = 544
        pending = []

        def act(frames, point=None, left=False):
            before = state(native)
            mouse = dict(left=left)
            if point is not None:
                mouse.update(dx=2*(point[0]-before['pointer'][0]), dy=2*(point[1]-before['pointer'][1]))
            action = dict(frames=frames, mouse=mouse)
            report['actions'].append(action)
            native.perform([action])
            after = state(native)
            pending.append(dict(from_tick=before['tick'], to_tick=after['tick'], point=after['pointer'], left=left))

        def mark(name):
            native.save(name, ram=True)
            after = state(native)
            report['checkpoints'].append(dict(name=name, inputs=pending[:], after=after))
            pending.clear()
            print(name, after['scene'], after['pose'], [(o['type'], o['state']) for o in after['objects']], flush=True)
            return after

        def center():
            rect = next(o['rect'] for o in state(native)['objects'] if o['type'] == 2)
            return [(rect[1]+rect[3])//2, (rect[0]+rect[2])//2]

        # The core's first payload after restore still contains its pre-restore
        # frontend image. Allow ordinary room animation to refresh it, as in
        # the existing room/object captures. Retain this wait in the manifest
        # so the joined browser replay advances through it without a reset.
        act(60)
        initial = mark('initial')
        assert initial['scene'] == 5 and any(o['type'] == 2 for o in initial['objects'])
        act(10, center()); act(1, left=True); act(12); mark('toy-click')
        act(100); mark('toy-settled')
        act(10, center()); act(25, left=True); act(20, [169,145], left=True); mark('toy-held')
        act(1400); offered = mark('toy-offered')
        assert any(o['type'] == 2 for o in offered['objects'])
        # Main room trapdoor and the exterior ladder (the existing yard journey).
        act(10, [281,187]); act(1, left=True); act(1200); outside = mark('outside')
        assert outside['scene'] == 4
        act(10, [270,130]); act(1, left=True); act(1200); returned = mark('returned')
        assert returned['scene'] == 5 and any(o['type'] == 2 for o in returned['objects'])
        act(10, center()); act(1, left=True); act(100); mark('toy-reused')
        report.update(complete=True, passed=True, snapshot_boundary_version=native.snapshot_boundary_version)
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        if native:
            native.close()
        (output/'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
