"""Replay the pinned maze choices through the completed victory song."""
from pathlib import Path
import argparse, json, struct
from capture import Recorder, digest
from capture_theater_audio_journey import AudioRecorder
from verify_maze_generation import model

DATA = Path(__file__).resolve().parents[2] / 'testing/output/treehouse'


def capture(output, observe=False):
    output.mkdir(parents=True, exist_ok=False)
    original = DATA / 'research-music-maze/playthrough'
    prior = json.loads((original / 'run.json').read_text(encoding='utf-8'))
    origin = original / 'state/settled.state'
    # Restoring RAM does not replace the frontend's cached video frame. Allow
    # a fresh video callback before taking the initial image.
    actions = [dict(frames=10, capture='settled')] + prior['actions'][1:] + [dict(frames=200, capture='victory')]
    core = DATA / 'capture-core/dosbox_pure_libretro.dll'; content = DATA / 'source/reference-v1.zip'
    report = dict(complete=False, passed=False, actions=actions, checkpoints=[],
        core_sha256=digest(core), content_sha256=digest(content), restore_source=str(origin), restore_sha256=digest(origin),
        tool_sha256=digest(Path(__file__)), adapter_sha256=digest(Path(__file__).with_name('libretro.py')), observe_audio=observe)
    native = None
    try:
        native = (AudioRecorder if observe else Recorder)(core, content, output)
        native.perform([dict(frames=1800)])
        native.restore(origin); native.image_base = 544
        for action in actions:
            native.perform([action])
            if name := action.get('capture'):
                path = output / 'state' / (name + '.ram-0'); ram = path.read_bytes()
                state = model(path)
                state.update(tick=struct.unpack_from('<I', ram, 0x323f0 + 0x201e)[0],
                    phase=struct.unpack_from('<H', ram, 0x318b0 + 0xb34)[0], earned=ram[0x318b0 + 0x9e6])
                report['checkpoints'].append(dict(name=name, after=state))
                print(name, 'node', state['node'], 'notes', state['earned'], 'phase', state['phase'], flush=True)
        expected = model(DATA / 'maze-victory-tail-b/state/tail-0.ram-0')
        actual = report['checkpoints'][-1]['after']
        report.update(complete=True, passed=all(actual[k] == v for k, v in expected.items()),
            capture_boundary_version=native.capture_boundary_version, snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native: native.close()
        (output / 'run.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--observe-audio', action='store_true')
    args = parser.parse_args(); raise SystemExit(0 if capture(args.output, args.observe_audio) else 1)
