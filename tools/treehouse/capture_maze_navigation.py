"""Observe maze global exit and piano return through original canvas controls."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest
from capture_theater_audio_journey import AudioRecorder
from verify_maze_generation import model

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'


def room_model(ram):
    ds=0x323f0;s=0x318b0
    w=lambda off:struct.unpack_from('<h',ram,ds+off)[0]
    u=lambda off:struct.unpack_from('<I',ram,ds+off)[0]
    sw=lambda off:struct.unpack_from('<h',ram,s+off)[0]
    return dict(tick=u(0x201e),seed=u(0x5290),pointer=[w(0x2066),w(0x2064)],scene=sw(0xb34),
        date=[w(0x52ce),ram[ds+0x52cd],ram[ds+0x52cc]],calendarOpen=bool(w(0x5262)),chalkTool=w(0x15e8)-1,
        selected=bool(w(0x5692)),sex=sw(0xa14),cloud=sw(0xb4),cloudX=sw(0xa18),outsideCycle=w(0x5570),
        pose=w(0x5688),hunger=w(0x5282),fatigue=w(0x581c),windowRemaining=w(0x201a),
        ambientDue=u(0x531c),longDue=u(0x5318),hungerDue=u(0x568e),fatigueDue=u(0x5576),
        objects=[dict(type=w(0x5830+20*i),state=w(0x5832+20*i),inside=bool(w(0x5834+20*i)),
            rect=[w(0x5836+20*i+2*j) for j in range(4)],due=u(0x5840+20*i)) for i in range(w(0x556c))])


def capture(output,control='global',victory=False,observe=False,tour=False):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/('maze-victory-tail-b/state/tail-0.state' if victory else 'maze-entry-control-a/state/intro-39.state')
    report=dict(complete=False,passed=False,actions=[],checkpoints=[],control=control,victory=victory,tour=tour,core_sha256=digest(core),content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)))
    native=None
    try:
        native=(AudioRecorder if observe else Recorder)(core,content,output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary();ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            return room_model(ram)
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a]);after=state()
            pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True);after=state();after['maze']=model(output/'state'/f'{name}.ram-0')
            report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear();print(name,after['scene'],after['seed'],flush=True)
            return after
        native.perform([dict(frames=10)]);checkpoint('initial')
        point=[311,10] if control=='global' else [285,60] if victory else [291,10]
        action(20,point);action(10,left=True);action(40);checkpoint('activated')
        for i in range(12):action(100);checkpoint(f'return-{i:02}')
        if tour:
            assert control=='global' and state()['scene']==5
            def click(point,name,wait=700):
                action(20,point);action(10,left=True);action(wait);return checkpoint(name)
            assert click([50,188],'piano-revisit')['scene']==0
            click([170,183],'piano-key',100)
            assert click([311,10],'piano-room')['scene']==5
            click([134,110],'nature-visit')
            assert click([311,10],'nature-room')['scene']==5
            click([63,133],'theater-visit',1800)
            assert click([311,10],'theater-room')['scene']==5
            click([180,188],'board-visit',1800)
            assert click([311,10],'board-room')['scene']==5
            click([195,130],'telescope-visit',1200)
            assert click([311,10],'telescope-room')['scene']==5
            assert click([50,188],'piano-final')['scene']==0
            assert click([31,157],'maze-reentered',1800)['scene']==8
        report.update(complete=True,passed=report['checkpoints'][-1]['after']['scene']==(8 if tour else 5 if control=='global' else 0),capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--control',choices=['global','piano'],default='global');parser.add_argument('--victory',action='store_true');parser.add_argument('--observe-audio',action='store_true');parser.add_argument('--tour',action='store_true')
    a=parser.parse_args();raise SystemExit(0 if capture(a.output,a.control,a.victory,a.observe_audio,a.tour) else 1)
