"""Capture a continuous original yard and squirrel-hollow journey."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'research-exterior-audit/native/state/outside.state'
    report=dict(complete=False,passed=False,core_sha256=digest(core),
        content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),
        tool_sha256=digest(Path(__file__)),actions=[],checkpoints=[])
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary()
            pointer,length=next((p+o,l) for s,p,o,l in native.memory if s==0 and p)
            ram=C.string_at(pointer,length);ds=0x323f0;shared=0x318b0
            w=lambda off:struct.unpack_from('<h',ram,ds+off)[0]
            u=lambda off:struct.unpack_from('<I',ram,ds+off)[0]
            words=lambda off,n:list(struct.unpack_from('<'+str(n)+'h',ram,shared+off))
            return dict(tick=u(0x201e),seed=u(0x5290),pointer=[w(0x2066),w(0x2064)],scene=words(0xb34,1)[0],
                selected=bool(w(0x5692)),sex=words(0xa14,1)[0],cloud=words(0xb4,1)[0],outsideCycle=w(0x5570),
                pose=w(0x5688),hunger=w(0x5282),fatigue=w(0x581c),windowRemaining=w(0x201a),
                ambientDue=u(0x531c),longDue=u(0x5318),hungerDue=u(0x568e),fatigueDue=u(0x5576),
                objects=[dict(type=w(0x5830+20*i),state=w(0x5832+20*i),inside=bool(w(0x5834+20*i)),
                    rect=[w(0x5836+20*i+2*j) for j in range(4)],due=u(0x5840+20*i)) for i in range(w(0x556c))])
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a])
            after=state();pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True)
            after=state();report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear()
            print(name,after['scene'],after['seed'],after['cloud'],after['outsideCycle'],flush=True)
            return after
        def click(point,name,wait=450):
            action(10,point);action(1,left=True);action(wait);return checkpoint(name)
        native.perform([dict(frames=60)]);s=checkpoint('initial');assert s['scene']==4 and s['selected']
        s=click([218,142],'hollow',100);assert s['scene']==14
        for i in range(1,5):click([229,145],f'nut-{i}',400)
        click([158,95],'squirrel-one',900)
        click([126,113],'squirrel-two',900)
        click([180,40],'sign-reading',10)
        click([180,40],'sign-interrupted',100)
        s=click([10,190],'yard-again',100);assert s['scene']==4
        for i in range(1,4):click([80,25],f'cloud-{i}',80)
        click([25,18],'sun',800)
        click([150,90],'birdhouse',800)
        for i in range(1,4):click([50,190],f'pond-{i}',800)
        click([237,45],'friend-window',1600)
        s=click([218,142],'hollow-revisit',100);assert s['scene']==14
        click([229,145],'revisit-nut',400)
        s=click([10,190],'yard-return',100);assert s['scene']==4
        s=click([270,130],'room-return',300);assert s['scene']==5
        report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index)
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
