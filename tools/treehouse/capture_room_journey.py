"""Capture a continuous original calendar, clock and chalkboard journey."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'entry-verified-a/state/after-click.state'
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
                date=[w(0x52ce),ram[ds+0x52cd],ram[ds+0x52cc]],calendarOpen=bool(w(0x5262)),chalkTool=w(0x15e8)-1,
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
            print(name,after['date'],after['calendarOpen'],after['chalkTool'],after['seed'],flush=True)
            return after
        def click(point,name,wait=450):
            action(10,point);action(1,left=True);action(wait);return checkpoint(name)
        native.perform([dict(frames=60)]);s=checkpoint('initial');assert s['scene']==5 and s['selected']
        # Pop the movable balloon through ordinary input before drawing.
        for i in range(3):
            o=next(o for o in s['objects'] if o['type']==6);r=o['rect']
            s=click([(r[1]+r[3])//2,(r[0]+r[2])//2],f'balloon-{i+1}',60)
        assert not any(o['type']==6 for o in s['objects'])
        s=click([220,25],'calendar-open',150);assert s['calendarOpen']
        s=click([200,55],'calendar-dismissed-by-cloud',200);assert not s['calendarOpen']
        click([151,34],'next-day',1800)
        click([134,23],'previous-day',1800)
        s=click([220,50],'calendar-closed',300);assert not s['calendarOpen']
        click([200,55],'cloud-changed',100)
        click([103,113],'clock',650)
        click([38,15],'spider',650)
        click([245,87],'nest-chirp',500)
        click([220,98],'nest',650)
        s=click([68,95],'white-chalk',60);assert s['chalkTool']==0
        action(10,[80,62]);action(10,left=True)
        for x in range(82,101,2):action(5,[x,62],left=True)
        action(10);action(20,[170,115]);s=checkpoint('white-stroke');assert s['chalkTool']==-1
        s=click([80,95],'red-chalk',60);assert s['chalkTool']==1
        action(10,[88,55]);action(10,left=True)
        for y in range(57,76,2):action(5,[88,y],left=True)
        action(10);action(20,[170,115]);checkpoint('red-stroke')
        click([54,90],'erase-question',200)
        click([260,77],'erase-declined',200)
        click([54,90],'erase-again',200)
        click([194,77],'erase-confirmed',200)
        click([220,25],'calendar-after-erase',150)
        click([220,50],'calendar-final-closed',150)
        report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index)
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
