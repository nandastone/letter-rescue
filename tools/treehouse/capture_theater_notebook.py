"""Capture original theater notebook drag, correction and performance interactions."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'theater-native-journey-e/state/editor.state'
    tables=json.loads((DATA/'research-theater/tables.json').read_text(encoding='utf-8'))
    rects=tables['ui_rects'];report=dict(complete=False,passed=False,core_sha256=digest(core),
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
                selection=words(0x40a,4),order=words(0x8ea,4),mixUp=bool(words(0x406,1)[0]),propsEnabled=bool(words(0x408,1)[0]),
                validation=words(0x930,1)[0],prop_counts=words(0x412,6),actor_drag=[words(0x8ce+4*i,2) for i in range(7)],
                props=[[dict(encoded=words(0x7de+2*(20*p+i),1)[0],rect=words(0x41e+8*(20*p+i),4)) for i in range(words(0x412+p*2,1)[0])] for p in range(6)])
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a])
            after=state();pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True)
            after=state();report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear()
            print(name,after['scene'],after['selection'],after['order'],after['validation'],flush=True)
            return after
        def click(point,name,wait=450):
            action(10,point);action(1,left=True);action(wait);return checkpoint(name)
        def center(r):return[(r[1]+r[3])//2,(r[0]+r[2])//2]
        def drag(a,b,name,wait=450):
            action(10,a);action(30,left=True);action(15,b,left=True);action(wait);return checkpoint(name)
        # Allow the restored editor to publish its own image before capture.
        native.perform([dict(frames=60)]);s=checkpoint('initial')
        assert s['scene']==2 and s['mixUp'] and s['selection']==[-1]*4
        s=drag(center(rects[8]),[300,100],'outside-notebook-drop')
        assert s['selection']==[-1]*4 and s['order']==[0,1,2,3]
        for category,slot in enumerate([2,0,3,1]):
            s=drag(center(rects[8+category]),center(rects[23+slot]),f'add-{category}')
            assert s['selection'][category]>=0
        s=click(center(rects[7]),'invalid-performance',1800)
        assert s['validation'] in [5,6]
        s=click(center(rects[22]),'corrected',450);assert s['validation']==0
        s=click(center(rects[7]),'valid-performance',1800)
        before=s['selection'][:];order=s['order'][:]
        s=drag(center(rects[8]),center(rects[26]),'selected-notebook-drag')
        assert s['selection']==before and s['order']==order
        slot=s['order'].index(0)
        s=drag(center(rects[23+slot]),[300,100],'outside-rail-drop')
        assert s['selection']==before and s['order']==order
        s=drag(center(rects[23+slot]),[35,74],'remove-subject')
        assert s['selection'][0]==-1 and s['order']==order
        s=drag(center(rects[8]),center(rects[23+slot]),'restore-subject')
        assert s['selection'][0]>=0 and s['order']==order
        click(center(rects[7]),'restored-performance',1800)
        report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index)
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
