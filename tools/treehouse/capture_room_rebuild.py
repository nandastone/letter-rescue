"""Observe room-rebuild operation boundaries on the ordinary maze-return path."""
from pathlib import Path
import argparse,ctypes as C,json
from capture import Recorder,digest
from capture_maze_navigation import DATA
from trace_nature_redraw import TraceRecorder


def capture(output,control=False):
    output.mkdir(parents=True,exist_ok=False)
    reference=DATA/'maze-activity-tour-native-a';origin=reference/'state/initial.state'
    actions=json.loads((reference/'run.json').read_text(encoding='utf-8'))['actions'][:15]
    core=DATA/'trace-core-work-b/dosbox_pure_trace.dll';content=DATA/'source/reference-v1.zip'
    report=dict(passed=False,control=control,origin_sha256=digest(origin),core_sha256=digest(core),content_sha256=digest(content),actions=actions,events=[]);native=None
    try:
        native=(Recorder if control else TraceRecorder)(core,content,output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544;native.save('initial',ram=True)
        if not control:
            pointer=next(p+o for s,p,o,l in native.memory if s==0 and p)
            os_pointer=next(p+o for s,p,o,l in native.memory if s==0x100000 and p)
            base=544+pointer-os_pointer
            labels={0x1f24:'rebuild.begin',0x1f65:'resources.invalidated',0x1f81:'sound.prepared',0x1fe0:'palettes.activated',0x1fee:'backing.allocated',0x203e:'catalogs.prepared',0x2053:'background.drawn',0x2196:'calendar.drawn',0x2238:'objects.drawn',0x223d:'timers.reset',0x2269:'cloud.drawn',0x2296:'backing.presented',0x530d:'return.begin',0x5437:'return.end',0x6416:'catalog.begin',0x6483:'catalog.end',0x64a4:'shape.begin',0xb8a3:'object.timer'}
            native.labels={base+address:name for address,name in labels.items()}
            addresses=(C.c_uint32*len(native.labels))(*native.labels)
            native.core.retro_treehouse_trace_configure(addresses,len(addresses),base+0x341ee)
        native.perform(actions);native.save('final',ram=True)
        report.update(passed=True,events=[] if control else native.events,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for e in report['events']:
        if e['label'] not in ['shape.begin','catalog.begin','catalog.end','object.timer']:print(e['label'],e['pit'],round(e['milliseconds'],3),flush=True)
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--control',action='store_true')
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.control) else 1)
