"""Observe ordinary hunger warning state before, during and after its animation."""
from pathlib import Path
import argparse
import json
from capture import Recorder, digest
from capture_prize_object_journey import DATA, state


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    source = DATA/'robot-prize-native-a/state/shelf-return.state'
    core, content = DATA/'capture-core/dosbox_pure_libretro.dll', DATA/'source/reference-v1.zip'
    report = dict(complete=False, passed=False, restore_source=str(source), restore_sha256=digest(source),
                  core_sha256=digest(core), content_sha256=digest(content), tool_sha256=digest(Path(__file__)),
                  actions=[], checkpoints=[])
    native = None
    try:
        native = Recorder(core, content, output)
        native.perform([dict(frames=1800)])
        native.restore(source); native.image_base = 544
        native.perform([dict(frames=60)])
        pending = []

        def mark(name):
            native.save(name, ram=True)
            model = state(native)
            report['checkpoints'].append(dict(name=name, inputs=pending[:], after=model))
            pending.clear()
            print(name, model['tick'], model['hunger'], model['hungerDue'], flush=True)
            return model

        def wait(frames):
            before = state(native)
            native.perform([dict(frames=frames)])
            after = state(native)
            report['actions'].append(dict(frames=frames))
            pending.append(dict(from_tick=before['tick'], to_tick=after['tick'], point=after['pointer'], left=False))

        start = mark('initial')
        assert start['hunger']==3 and start['scene']==5
        # Stop before the deadline, then observe ordinary state changes without
        # patching RAM or invoking any original internal routine.
        while state(native)['tick'] < start['hungerDue']-120:
            wait(30)
        mark('before-warning')
        for _ in range(6000):
            wait(1)
            if state(native)['hungerDue'] != start['hungerDue']:
                break
        else:
            raise AssertionError('Warning did not begin')
        during = mark('warning-started')
        assert during['hunger']==3
        wait(60); middle = mark('warning-playing')
        assert middle['hunger']==3
        for _ in range(6000):
            wait(1)
            if state(native)['hunger']==4:
                break
        else:
            raise AssertionError('Warning did not complete')
        mark('warning-completed')
        wait(60); mark('settled')
        report.update(complete=True, passed=True, snapshot_boundary_version=native.snapshot_boundary_version)
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        if native:
            native.close()
        (output/'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
