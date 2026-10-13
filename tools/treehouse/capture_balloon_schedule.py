"""Read balloon position/deadline at held video callbacks; never modify original RAM."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest
from capture_maze_navigation import DATA


class BalloonRecorder(Recorder):
    def __init__(self,*args):
        self.observe=False;self.events=[];self.last=None
        super().__init__(*args)

    def video(self,*args):
        super().video(*args)
        if not self.observe or self.capture_boundary_version!=1:return
        pointer=next(p+o for s,p,o,l in self.memory if s==0 and p)
        ram=C.string_at(pointer,0x40000);ds=0x323f0
        w=lambda off:struct.unpack_from('<h',ram,ds+off)[0]
        u=lambda off:struct.unpack_from('<I',ram,ds+off)[0]
        scene=struct.unpack_from('<h',ram,0x318b0+0xb34)[0]
        for i in range(w(0x556c)):
            offset=0x5830+20*i
            if w(offset)!=6:continue
            current=dict(scene=scene,rect=[w(offset+6+2*j) for j in range(4)],due=u(offset+16),pointer=[w(0x2066),w(0x2064)],returnDrawing=w(0x529c),actorDrawing=w(0x5254))
            if current!=self.last:
                self.events.append(dict(tick=u(0x201e),callback=self.callback_index-1,**current));self.last=current
            break


def capture(output,idle=False,control=False):
    output.mkdir(parents=True,exist_ok=False)
    reference=DATA/'maze-activity-tour-native-a'
    origin=reference/'state'/('board-room.state' if idle else 'initial.state')
    actions=[dict(frames=1500)] if idle else json.loads((reference/'run.json').read_text(encoding='utf-8'))['actions'][:15]
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    report=dict(passed=False,mode='idle' if idle else 'return',control=control,actions=actions,origin=str(origin),origin_sha256=digest(origin),core_sha256=digest(core),content_sha256=digest(content))
    native=None
    try:
        native=(Recorder if control else BalloonRecorder)(core,content,output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        native.save('initial',ram=True)
        if not control:native.observe=True
        native.perform(actions);native.save('final',ram=True)
        report.update(passed=True,events=[] if control else native.events,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(mode=report['mode'],passed=report['passed'],events=len(report.get('events',[]))),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--idle',action='store_true');p.add_argument('--control',action='store_true')
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.idle,a.control) else 1)
