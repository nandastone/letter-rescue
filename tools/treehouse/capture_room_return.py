"""Observe room-return operation boundaries and random callers, without RAM edits."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import digest
from trace_nature_redraw import TraceRecorder

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    origin=DATA/'nature-native-journey-c/state/back-to-nature.state'
    core=DATA/'trace-core-work-b/dosbox_pure_trace.dll'
    report=dict(passed=False,origin_sha256=digest(origin),core_sha256=digest(core),tool_sha256=digest(Path(__file__)))
    native=None
    try:
        native=TraceRecorder(core,DATA/'source/reference-v1.zip',output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        pointer,length=next((p+o,l) for s,p,o,l in native.memory if s==0 and p)
        os_pointer=next(p+o for s,p,o,l in native.memory if s==0x100000 and p)
        base=544+pointer-os_pointer
        labels={0x1f24:'room.rebuild',0xb95c:'room.reset',0xbb48:'room.long',0xbc43:'room.ambient',
                0xb8a3:'object.timer',0x530d:'return.begin',0x5437:'return.end'}
        native.labels={base+k:v for k,v in labels.items()}
        native.labels[base+0xd510+0x3ba6]='random'
        addresses=(C.c_uint32*len(native.labels))(*native.labels)
        native.core.retro_treehouse_trace_configure(addresses,len(addresses),base+0x341ee)
        before=C.string_at(pointer,length);py,px=struct.unpack_from('<hh',before,0x323f0+0x2064)
        actions=[dict(frames=10,mouse=dict(dx=2*(312-px),dy=2*(12-py))),dict(frames=1,mouse=dict(left=True)),dict(frames=1800,capture='back-to-room')]
        native.perform(actions)
        ram=C.string_at(pointer,length)
        report.update(actions=actions,events=native.events,location=dict(main_base=base),
                      seed=struct.unpack_from('<I',ram,0x323f0+0x5290)[0],
                      snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
    reference=DATA/'nature-native-journey-c/state/back-to-room.png'
    report['exact_reference_png']=digest(output/'state/back-to-room.png')==digest(reference)
    report['passed']=report['exact_reference_png'] and report['seed']==4163058334
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='events'},indent=2))
    for e in report['events']:
        if e['label'] not in ['balloon.move','clock.read']:print(e['label'],e['pit'],[hex(x) for x in e['stack'][:4]])
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if capture(p.parse_args().output) else 1)
