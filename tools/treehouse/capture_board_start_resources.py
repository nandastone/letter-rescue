"""Observe Play-button resource lifetimes using ordinary original-game input.

Restores the existing fixed-clock options capture. Observer addresses identify
original semantic boundaries only; no guest memory or allocation state is edited.
"""
from pathlib import Path
import argparse
import ctypes as C
import json
import struct

from capture import Recorder, digest
from trace_nature_redraw import TraceRecorder, HeapSnapshot, DATA


def capture(output, stage):
    output.mkdir(parents=True, exist_ok=False)
    rolling = stage in ['first-roll','roll-faces','roll-control']
    moving = stage in ['move','movement','move-control']
    control = stage in ['control','roll-control','move-control']
    origin = DATA / ('resource-board-roll-control-a/state/final.state' if moving else 'resource-board-play-control-a/state/final.state' if rolling else 'resource-board-options-a/state/final.state')
    core = DATA / 'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    content = DATA / 'source/reference-startup-v2.zip'
    report = dict(passed=False, stage=stage, control=control, fixed_clock=True,
                  tool_sha256=digest(Path(__file__)),
                  origin_sha256=digest(origin), core_sha256=digest(core), content_sha256=digest(content))
    native = None
    try:
        native = (Recorder if control else TraceRecorder)(core, content, output)
        native.perform([dict(frames=1800)])
        native.restore(origin)
        native.save('initial', ram=True)
        pointer, length = next((p+o, n) for s, p, o, n in native.memory if s == 0 and p)
        low = next(p+o for s, p, o, n in native.memory if s == 0x100000 and p)
        ram = C.string_at(pointer, length)
        base = native.image_base+pointer-low
        assert base == 0x1a80
        overlay = (DATA / 'research-resources/overlay3.bin').read_bytes()
        signature = overlay[0x986:0x99b]
        assert ram.count(signature) == 1
        slot = ram.index(signature)-0x986+pointer-low
        assert slot == base+0x24fc0
        py, px = struct.unpack_from('<hh', ram, native.image_base+0x321d0+0x2064)
        tables = json.loads((Path(__file__).resolve().parents[2] / 'treehouse-demo/boardgame-tables.json').read_text(encoding='utf-8'))
        top, left, bottom, right = tables['game_rects'][2] if rolling else tables['options_rects'][17]
        if moving:
            ds = native.image_base+0x321d0
            player = struct.unpack_from('<h',ram,ds+0x52d8)[0]
            node = struct.unpack_from('<h',ram,ds+0x52c4+2*player)[0]
            types = struct.unpack_from('<24h',ram,ds+0x59da)
            target = max((n for n in tables['adjacency'][node] if n>=0),key=lambda n:types[n])
            top, left, bottom, right = tables['node_rects'][target]
            report['move_target'] = target
        x, y = (left+right)//2, (top+bottom)//2
        actions = [dict(frames=10, mouse=dict(dx=2*(x-px), dy=2*(y-py))),
                   dict(frames=1, mouse=dict(left=True)), dict(frames=300 if rolling else 1200)]
        report['actions'] = actions
        if not control:
            native.labels = {slot+a: n for a, n in {
                0xdd7:'play.begin', 0x90a:'board.restart', 0x625:'board.draw',
                0x16d7:'pawn.draw', 0x39d4:'dashboard.begin', 0x3a1a:'dashboard.end',
                0x932:'board.restart.end', 0x17b:'roll.click',0x11a4:'roll.faces',
                0x12d1:'roll.faces.end',0x12d2:'hint.draw',0x2d5:'roll.complete',
                0x14d8:'node.flash',0x17ee:'movement.begin',0x1726:'pawn.paint',
                0x19d0:'movement.end',0x1ccc:'landing.begin'}.items()}
            native.labels.update({base+a: n for a, n in {
                0x6416:'palette.load', 0x6483:'palette.loaded', 0x64a4:'shape.draw',
                0xc39d:'animation.create', 0xc77c:'animation.created',
                0x5b9b:'click.sound', 0x7159:'background.save', 0x70f5:'button.draw'}.items()})
            native.labels.update({base+0xd510+a: n for a, n in {
                0xe5e2:'sound.play', 0xe33c:'shape.load', 0x7668:'resource.load',
                0x7688:'resource.copy', 0x8806:'cursor.set'}.items()})
            addresses = (C.c_uint32*len(native.labels))(*native.labels)
            native.core.retro_treehouse_trace_configure(addresses, len(addresses), base+0x341ee)
            assert native.core.retro_treehouse_heap_snapshot_size() == C.sizeof(HeapSnapshot)
            begin, end = {'play':(0xdd7, 0xcb), 'restart':(0x90a, 0x932),
                          'redraw':(0x625, 0x16d7), 'dashboard':(0x39d4, 0x3a1a),
                          'first-roll':(0x17b,0x2d5),'roll-faces':(0x11a4,0x12d1),
                          'move':(0x14d8,0x1ccc),'movement':(0x17ee,0x19d0)}[stage]
            native.heap = True
            native.core.retro_treehouse_heap_configure.argtypes = [C.c_uint32, C.c_uint32, C.c_uint32]
            native.core.retro_treehouse_heap_configure(slot+begin, slot+end, 0)
        native.perform(actions)
        native.save('final', ram=True)
        if not control:
            report['heap'] = native.read_heap()
            assert len(report['heap']) == 2, 'Expected one complete operation'
            report['events'] = native.events
        report.update(passed=True, main_base=base, overlay_base=slot,
                      capture_boundary_version=native.capture_boundary_version,
                      snapshot_boundary_version=native.snapshot_boundary_version)
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        if native:
            native.close()
        (output / 'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], stage=stage, snapshots=len(report.get('heap', [])))))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=['control', 'play', 'restart', 'redraw', 'dashboard','first-roll','roll-faces','roll-control','move','movement','move-control'], required=True)
    args = parser.parse_args()
    raise SystemExit(0 if capture(args.output, args.stage) else 1)
