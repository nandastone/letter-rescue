"""Capture ordinary original day/night collage editing without RAM writes."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'nature-native-journey-c/state/back-to-nature.state'
    tables=json.loads((DATA/'research-nature/tables.json').read_text(encoding='utf-8'))
    rects=tables['rectangles']
    report=dict(complete=False,passed=False,core_sha256=digest(core),content_sha256=digest(content),
        restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),actions=[],checkpoints=[])
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary()
            ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            ds=0x323f0;shared=0x318b0
            word=lambda off:struct.unpack_from('<h',ram,off)[0]
            uint=lambda off:struct.unpack_from('<I',ram,off)[0]
            objects=[]
            for time in range(2):
                items=[]
                for i in range(word(shared+0xca+2*time)):
                    slot=2*i+time;at=shared+0x16e+8*slot
                    items.append(dict(id=word(shared+0xce+2*slot),rect=[word(at+2*j) for j in range(4)]))
                objects.append(items)
            return dict(tick=uint(ds+0x201e),seed=uint(ds+0x5290),pointer=[word(ds+0x2066),word(ds+0x2064)],
                scene=word(shared+0xb34),time=word(shared+0xb6),attribute=word(shared+0xb8),category=word(shared+0xba),
                values=[word(shared+0xbc+2*i) for i in range(7)],objects=objects)
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a]);after=state()
            pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True);after=state()
            report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear()
            print(name,after['time'],after['category'],[len(x) for x in after['objects']],flush=True)
            return after
        def center(r):return [(r[1]+r[3])//2,(r[0]+r[2])//2]
        def click(point,name,wait=100):
            action(10,point);action(1,left=True);action(wait);return checkpoint(name)
        def drag(a,b,name):
            action(10,a);action(30,left=True);action(15,b,left=True);action(100);return checkpoint(name)
        native.perform([dict(frames=60)]);s=checkpoint('initial')
        assert s['scene']==1 and s['time']==0 and not any(s['objects'])
        s=drag([12,112],[220,115],'day-animal');assert len(s['objects'][0])==1
        click(center(rects[26]),'day-fact-dismissed')
        box=s['objects'][0][0]['rect'];s=drag(center(box),[260,150],'day-animal-moved')
        click(center(rects[26]),'moved-fact-dismissed')
        click(center(rects[10]),'day-clear-question')
        s=click([97,159],'day-clear-declined');assert len(s['objects'][0])==1
        s=click(center(rects[13]),'night');assert s['time']==1
        click(center(rects[14+3]),'night-insects')
        s=drag([12,112],[210,110],'night-animal');assert len(s['objects'][1])==1
        click(center(rects[26]),'night-fact-dismissed')
        box=s['objects'][1][0]['rect'];s=drag(center(box),[60,130],'night-animal-removed');assert len(s['objects'][1])==0
        s=drag([12,112],[250,140],'night-animal-replaced');assert len(s['objects'][1])==1
        click(center(rects[26]),'night-replaced-fact-dismissed')
        s=click(center(rects[13]),'day-restored');assert s['time']==0 and len(s['objects'][0])==1
        click(center(rects[10]),'day-erase-question')
        s=click([33,159],'day-erased',300);assert len(s['objects'][0])==0 and len(s['objects'][1])==1
        s=click(center(rects[13]),'night-preserved');assert s['time']==1 and len(s['objects'][1])==1
        # Exercise filter/value/class changes after editing, without altering the collage.
        click(center(rects[7]),'food-filter')
        click(center(rects[12]),'food-next-value')
        s=click(center(rects[14]),'night-mammals');assert len(s['objects'][1])==1
        report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index)
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
