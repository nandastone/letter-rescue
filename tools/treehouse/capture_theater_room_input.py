"""Observe original theater entrance decisions at every edge of its room hotspot."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest
from capture_maze_navigation import DATA, room_model


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    core = DATA/'capture-core/dosbox_pure_libretro.dll'
    content = DATA/'source/reference-v1.zip'
    origin = DATA/'maze-activity-tour-native-a/state/board-room.state'
    points = [('left-outside',47,133),('left-inside',52,133),
              ('right-outside',79,133),('right-inside',74,133),
              ('top-outside',63,118),('top-inside',63,124),
              ('bottom-outside',63,147),('bottom-inside',63,142)]
    report = dict(passed=False, core_sha256=digest(core), content_sha256=digest(content),
                  origin=str(origin), origin_sha256=digest(origin), cases=[])
    native = None
    try:
        native = Recorder(core, content, output)
        native.perform([dict(frames=1800)]); native.image_base=544
        def state():
            native.snapshot_boundary()
            ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            return room_model(ram), ram
        for name,x,y in points:
            native.restore(origin); before,ram=state()
            # Original room table: entry 13, top/left/bottom/right, image-relative.
            rect=list(struct.unpack_from('<4h',ram,544+0x2e938+13*8))
            actions=[dict(frames=20,mouse=dict(left=False,dx=2*(x-before['pointer'][0]),dy=2*(y-before['pointer'][1])))]
            native.perform(actions); pressed,_=state()
            actions += [dict(frames=10,mouse=dict(left=True)),dict(frames=1200,mouse=dict(left=False))]
            native.perform(actions[1:]); native.save(name,ram=True); after,_=state()
            px,py=pressed['pointer']; hit=rect[1]<=px<rect[3] and rect[0]<=py<rect[2]
            case=dict(name=name,rectangle=rect,point=pressed['pointer'],inside=hit,actions=actions,
                      before=before,after=after,passed=hit==name.endswith('-inside') and after['scene']==(13 if hit else 5))
            report['cases'].append(case)
            print(name,rect,case['point'],after['scene'],case['passed'],flush=True)
        report.update(passed=all(c['passed'] for c in report['cases']),
                      capture_boundary_version=native.capture_boundary_version,
                      snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
