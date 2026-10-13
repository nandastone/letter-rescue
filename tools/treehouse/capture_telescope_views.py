"""Capture all four telescope views through original room clicks, without RAM writes."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest
from capture_maze_navigation import room_model, DATA


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll'; content=DATA/'source/reference-v1.zip'
    origin=DATA/'maze-activity-tour-native-a/state/board-room.state'
    report=dict(passed=False, actions=[], checkpoints=[], core_sha256=digest(core), content_sha256=digest(content),
                restore_source=str(origin), restore_sha256=digest(origin), tool_sha256=digest(Path(__file__)))
    native=None
    try:
        native=Recorder(core,content,output); native.perform([dict(frames=1800)]); native.restore(origin); native.image_base=544
        def state():
            native.snapshot_boundary()
            ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            return dict(**room_model(ram), visited_mask=struct.unpack_from('<H',ram,0x323f0+0x52f6)[0])
        def action(frames,point=None,left=False):
            before=state(); mouse=dict(left=left)
            if point: mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a])
        def checkpoint(name,view=None):
            native.save(name,ram=True); after=state()
            report['checkpoints'].append(dict(name=name,view=view,after=after));print(name,after['scene'],after['visited_mask'],flush=True)
            return after
        before=checkpoint('initial');assert before['scene']==5 and before['visited_mask']==0
        for visit in range(4):
            # Room narration/ambient actions may consume the first click.
            # Retry through ordinary input after waiting; never alter state.
            for attempt in range(3):
                action(20,[195,130]);action(10,left=True);action(1800)
                if state()['scene']==12:break
            after=state();added=after['visited_mask']^before['visited_mask']
            assert added in [1,2,4,8] and after['scene']==12, after
            view=added.bit_length()-1;checkpoint(f'view-{view}',view)
            action(20,[311,10]);action(10,left=True);action(900)
            before=checkpoint(f'returned-{visit}');assert before['scene']==5
        assert before['visited_mask']==15
        report.update(passed=True,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(parser.parse_args().output) else 1)
