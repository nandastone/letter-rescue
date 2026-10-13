"""Read-only MIDI/OPL call observations during the original's ordinary boot."""
import argparse
import ctypes as C
import json
from pathlib import Path

from capture import Recorder, digest
from trace_nature_redraw import TraceRecorder, DATA


class MusicRecorder(TraceRecorder):
    def before_load(self):
        base = 0x1a80
        self.labels = {base + offset: name for offset, name in {
            0x19cc9: 'midi.start', 0x1a256: 'midi.sequence',
            0x1a472: 'midi.event', 0x1a4b3: 'midi.cue',
            0x1f6be: 'fm.dispatch', 0x1fc9c: 'fm.write',
            0x1a43b: 'midi.tempo',
            0x1a35d: 'midi.irq',
        }.items()}
        addresses = (C.c_uint32 * len(self.labels))(*self.labels)
        self.core.retro_treehouse_trace_configure.argtypes = [C.POINTER(C.c_uint32), C.c_uint, C.c_uint32]
        self.core.retro_treehouse_trace_configure(addresses, len(addresses), base + 0x341ee)


def capture(output: Path, control: bool = False, frames: int = 1800):
    output.mkdir(parents=True, exist_ok=False)
    core = DATA / 'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    content = DATA / 'source/reference-startup-v2.zip'
    report = dict(passed=False, control=control, frames=frames, core_sha256=digest(core), content_sha256=digest(content))
    native = None
    try:
        native = (Recorder if control else MusicRecorder)(core, content, output)
        native.perform([dict(frames=frames, capture='selection')])
        pointer = next(p + o for s, p, o, length in native.memory if s == 0 and p)
        low = next(p + o for s, p, o, length in native.memory if s == 0x100000 and p)
        assert native.image_base + pointer - low == 0x1a80
        report.update(passed=True, capture_boundary_version=native.capture_boundary_version,
                      snapshot_boundary_version=native.snapshot_boundary_version)
        if not control:
            report['events'] = native.events
            assert any(e['label'] == 'fm.write' for e in native.events)
            assert [e['ax'] & 255 for e in native.events if e['label'] == 'midi.cue'][:6] == list(b'abcdef')
    except Exception as error:
        report.update(passed=False, error=str(error))
        raise
    finally:
        if native:
            native.close()
        (output / 'run.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], events=len(report.get('events', [])))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--frames', type=int, default=1800)
    args = parser.parse_args()
    capture(args.output, args.control, args.frames)
