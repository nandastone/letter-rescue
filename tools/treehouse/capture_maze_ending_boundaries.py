"""Observe semantic call boundaries during the last maze choice and victory.

Uses the existing observer core; no guest RAM writes or instruction profiling.
Control mode performs identical input on the same core with the probe disabled.
"""
from pathlib import Path
import argparse, ctypes as C, json
from capture import Recorder, digest
from trace_nature_redraw import Event, HeapSnapshot, TraceRecorder

DATA = Path(__file__).resolve().parents[2] / 'testing/output/treehouse'


class BoundaryRecorder(Recorder):
    def __init__(self, *args, sound_payloads=False):
        self.arm = False
        self.ready = False
        self.events = []
        self.labels = {}
        self.heap = sound_payloads
        super().__init__(*args)
        assert self.core.retro_treehouse_trace_size() == C.sizeof(Event)
        self.core.retro_treehouse_trace_configure.argtypes = [C.POINTER(C.c_uint32), C.c_uint, C.c_uint32]
        self.core.retro_treehouse_trace_read.argtypes = [C.POINTER(Event), C.c_uint]
        self.ready = True

    def video(self, *args):
        super().video(*args)
        if not self.ready:
            return
        batch = (Event * 16384)()
        count = self.core.retro_treehouse_trace_read(batch, len(batch))
        for event in batch[:count]:
            row = {name:list(value) if name == 'stack' else value
                for name, _ in Event._fields_ for value in [getattr(event, name)]}
            row.update(callback=self.callback_index-1, label=self.labels[event.address])
            self.events.append(row)
        assert not self.core.retro_treehouse_trace_overflow()
        if not self.arm:
            return
        self.arm = False
        pointer, length = next((p+o, n) for s, p, o, n in self.memory if s == 0 and p)
        low = next(p+o for s, p, o, n in self.memory if s == 0x100000 and p)
        shift = pointer - low
        ram = C.string_at(pointer, length)
        overlay = (DATA/'research-resources/overlay1.bin').read_bytes()
        signature = overlay[0x84c8:0x84f1]
        assert ram.count(signature) == 1
        overlay_base = ram.index(signature) - 0x84c8 + shift
        main = self.image_base + shift
        maze = {0x89c5:'frog.disappear', 0x89f4:'frog.disappear.return',
            0x5689:'last-note.after-disappear', 0x5696:'last-note.after-wait',
            0x7c84:'chooser', 0x7ec4:'chooser.opened',
            0x7f16:'chooser.highlighted', 0x7f29:'chooser.after-song',
            0x80da:'chooser.close.prepare', 0x8105:'chooser.close.sound',
            0x81ed:'chooser.closed', 0x8216:'chooser.cleaned',
            0x6c8f:'collected-song', 0x6dc1:'collected-song.restore-instrument',
            0x6dcb:'collected-song.restored', 0x6dd0:'collected-song.return',
            0x862d:'victory', 0x8727:'victory.frog-departed',
            0x874b:'victory.scene.begin', 0x886f:'victory.scene.drawn',
            0x8942:'victory.arrival', 0x896e:'victory.arrived',
            0x84c8:'full-song', 0x84fe:'full-song.instrument-ready', 0x8534:'full-song.return'}
        self.labels = {overlay_base+offset:label for offset,label in maze.items()}
        self.labels.update({main+offset:label for offset,label in {
            0x818b:'actor.remove', 0x81de:'actor.remove.return',
            0x83f0:'actor.animate', 0x844d:'actor.animate.return'}.items()})
        self.labels.update({main+0xd510+offset:label for offset,label in {
            0x56db:'wait', 0xe5e2:'sound.start', 0xe4aa:'sound.load',
            0xe4dc:'sound.load.return'}.items()})
        addresses = (C.c_uint32 * len(self.labels))(*self.labels)
        self.core.retro_treehouse_trace_configure(addresses, len(addresses), main+0x341ee)
        if self.heap:
            assert self.core.retro_treehouse_heap_snapshot_size() == C.sizeof(HeapSnapshot)
            self.core.retro_treehouse_heap_configure.argtypes = [C.c_uint32, C.c_uint32, C.c_uint32]
            self.core.retro_treehouse_heap_configure(main+0xd510+0xe4aa, main+0xd510+0xe4dc, 0)
        self.location = dict(main_base=main, overlay_base=overlay_base, physical_shift=shift)


def capture(output, control=False, sound_payloads=False):
    output.mkdir(parents=True, exist_ok=False)
    reference = DATA/'maze-audio-control-b'
    origin = reference/'state/correct-6.state'
    actions = json.loads((reference/'run.json').read_text(encoding='utf-8'))['actions'][-4:]
    core = DATA/'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    content = DATA/'source/reference-v1.zip'
    report = dict(passed=False, control=control, sound_payloads=sound_payloads, actions=actions,
        origin=str(origin), origin_sha256=digest(origin), core_sha256=digest(core),
        content_sha256=digest(content), tool_sha256=digest(Path(__file__)))
    native = None
    try:
        native = Recorder(core, content, output) if control else BoundaryRecorder(core, content, output, sound_payloads=sound_payloads)
        native.perform([dict(frames=1800)])
        native.restore(origin)
        native.image_base = 544
        if not control:
            native.arm = True
        native.perform(actions)
        report.update(passed=True, events=[] if control else native.events,
            location=None if control else native.location,
            capture_boundary_version=native.capture_boundary_version,
            snapshot_boundary_version=native.snapshot_boundary_version)
        if sound_payloads and not control:
            report['heap'] = TraceRecorder.read_heap(native)
    finally:
        if native:
            native.close()
        (output/'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], events=len(report.get('events', []))), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--sound-payloads', action='store_true')
    args = parser.parse_args()
    capture(args.output, args.control, args.sound_payloads)
