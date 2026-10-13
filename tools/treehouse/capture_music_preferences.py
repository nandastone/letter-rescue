"""Capture original listening preferences across songs and score modes."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'


def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'music-native-journey-c/state/listening.state'
    report=dict(complete=False,passed=False,core_sha256=digest(core),content_sha256=digest(content),
        restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),actions=[],checkpoints=[])
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary();ram=next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
            ds=0x323f0;word=lambda off:struct.unpack_from('<h',ram,off)[0];uint=lambda off:struct.unpack_from('<I',ram,off)[0]
            adjust=16*(word(ds+0x4a54)&65535)-(544+0x2f180)
            shared=16*(word(ds+0x4a22)&65535)-adjust;handle=word(ds+0x528e)&65535
            off,seg=struct.unpack_from('<HH',ram,ds+handle);song=seg*16+(off&15)+6-adjust
            return dict(tick=uint(ds+0x201e),seed=uint(ds+0x5290),pointer=[word(ds+0x2066),word(ds+0x2064)],
                song=list(ram[song:song+65]),title=ram[ds+0x56a0:ds+0x56a0+36].split(b'\0')[0].decode('cp437'),
                selection=list(ram[shared+0x9e:shared+0xa2]),composing=bool(word(shared+0xa2)),advanced=bool(word(shared+0xa4)),marker=word(shared+0xa12))
        pending=[]
        def action(frames,point=None,left=False,keys=None):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse,keys=keys or []);report['actions'].append(a);native.perform([a]);after=state()
            pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left,keys=keys or []))
        def checkpoint(name):
            native.save(name,ram=True);after=state();report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear()
            print(name,after['advanced'],after['composing'],after['song'][:5],after['marker'],flush=True);return after
        def click(point,name,wait=100):
            action(10,point);action(10,left=True);action(wait);return checkpoint(name)
        def drag(a,b,name):
            action(10,a);action(30,left=True);action(20,b,left=True);action(100);return checkpoint(name)
        native.perform([dict(frames=60)]);s=checkpoint('initial');assert not s['composing'] and not s['advanced']
        click([300,14],'next-song')
        click([46,124],'slow-next-song')
        click([285,20],'previous-song')
        click([300,14],'next-song-restored')
        click([274,149],'long-song')
        click([111,124],'long-notation')
        click([274,149],'short-song-restored')
        click([274,149],'long-notation-restored')
        click([285,20],'long-previous')
        click([274,149],'short-previous')
        report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index)
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
