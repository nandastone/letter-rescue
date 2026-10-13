"""Observe original replay/exit decisions near each telescope view's left edge."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest
from capture_maze_navigation import DATA, room_model


def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    report=dict(passed=False,core_sha256=digest(core),content_sha256=digest(content),cases=[]);native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)]);native.image_base=544
        def state():
            native.snapshot_boundary();ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            return room_model(ram),ram
        for view in range(4):
            origin=DATA/f'telescope-views-native-b/state/view-{view}.state'
            for inside in [False,True]:
                name=f'view-{view}-'+('inside' if inside else 'outside');native.restore(origin)
                before,ram=state();rect=list(struct.unpack_from('<4h',ram,0x323f0+0x358+8*view));point=[rect[1]+(1 if inside else -3),(rect[0]+rect[2])//2]
                actions=[dict(frames=20,mouse=dict(left=False,dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1])))]
                native.perform(actions);pressed,_=state()
                actions += [dict(frames=10,mouse=dict(left=True)),dict(frames=1200,mouse=dict(left=False))]
                native.perform(actions[1:]);native.save(name,ram=True);after,_=state()
                x,y=pressed['pointer'];hit=rect[1]<=x<rect[3] and rect[0]<=y<rect[2]
                case=dict(name=name,view=view,source=str(origin),source_sha256=digest(origin),rectangle=rect,point=pressed['pointer'],inside=hit,actions=actions,after=after,passed=hit==inside and after['scene']==(12 if inside else 5))
                report['cases'].append(case);print(name,case['point'],after['scene'],case['passed'],flush=True)
        report.update(passed=all(c['passed'] for c in report['cases']),capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
