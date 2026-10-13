"""Capture listening-key notation and its lifetime through ordinary controls."""
from pathlib import Path
import argparse,ctypes as C,json,struct,math
from capture import Recorder,digest
from capture_maze_navigation import room_model,DATA
from verify_maze_generation import model

def capture(output,held=False):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'maze-activity-tour-native-a/state/piano-revisit.state'
    keys=json.loads((Path(__file__).resolve().parents[2]/'treehouse-demo/music-tables.json').read_text())['keys']
    report=dict(complete=False,passed=False,actions=[],checkpoints=[],core_sha256=digest(core),content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)))
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary();ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p);return room_model(ram)
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a]);after=state()
            pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True);after=state();after['maze']=model(output/'state'/f'{name}.ram-0')
            report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear();print(name,flush=True)
        def click(point,name,wait=80):
            action(10,point);action(10,left=True);action(wait);checkpoint(name)
        def key(pitch,name):
            r=next(k['rectangle'] for k in keys if k['pitch']==pitch)
            point=[(r[1]+r[3])//2,150 if pitch in [1,3,6,8,10,13,15] else 183]
            action(10,point);action(10,left=True);checkpoint(name+'-held');action(100);checkpoint(name+'-released')
        native.perform([dict(frames=10)]);checkpoint('initial')
        if held:
            for pitch,label in [(9,'long-white'),(1,'long-black')]:
                r=next(k['rectangle'] for k in keys if k['pitch']==pitch)
                point=[(r[1]+r[3])//2,150 if pitch==1 else 183]
                action(10,point);action(10,left=True);checkpoint(label+'-start')
                for step in range(2):action(600,left=True);checkpoint(label+f'-held-{step}')
                action(1);checkpoint(label+'-released');action(120);checkpoint(label+'-expiry')
                action(700);checkpoint(label+'-idle')
            # Press a new key after the original idle animation has begun.
            native.snapshot_boundary();ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            due=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]
            ticks=max(0,due+8-state()['tick'])
            action(math.ceil(ticks*70.086304/(1193181/19886)),[185,183]);checkpoint('idle-before-new-key')
            action(10,left=True);checkpoint('idle-interrupted-key')
            action(300,left=True);checkpoint('idle-interrupted-held')
            action(120);checkpoint('idle-interrupted-release')
            report.update(complete=True,passed=state()['scene']==0,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
            return report['passed']
        key(9,'a');action(600);checkpoint('idle-after-a')
        key(1,'sharp-c');click([106,123],'flat-preference');key(1,'flat-d')
        click([60,124],'speed-change')
        for x in [54,55,63,64,72,73,81,82]:click([x,124],f'speed-x-{x}')
        click([274,149],'long-score')
        key(9,'long-a');key(16,'long-e')
        click([300,14],'next-page');key(4,'next-page-e')
        click([311,28],'contents');key(0,'contents-c')
        click([271,12],'contents-dismissed')
        report.update(complete=True,passed=state()['scene']==0,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--held',action='store_true')
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.held) else 1)
