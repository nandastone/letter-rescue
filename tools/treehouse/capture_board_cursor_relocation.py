"""Observe resource operations around the default cursor's board-game relocation."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest
from trace_nature_redraw import TraceRecorder,HeapSnapshot,DATA


class CursorRecorder(TraceRecorder):
    def __init__(self,*args):
        self.observe=False;self.cursor_events=[];self.previous_cursor=None
        super().__init__(*args)

    def video(self,*args):
        super().video(*args)
        if not self.observe:return
        pointer=next(p+o for s,p,o,l in self.memory if s==0 and p)
        handle=C.c_uint16.from_address(pointer+544+0x31660+25+13).value
        state,segment=struct.unpack('<HH',C.string_at(pointer+0x323f0+handle,4))
        cursor=dict(handle=handle,offset=(state&15)+6,segment=segment)
        if cursor!=self.previous_cursor:
            self.cursor_events.append(dict(callback=self.callback_index-1,milliseconds=self.core.retro_treehouse_milliseconds(),**cursor))
            self.previous_cursor=cursor


def capture(output,control=False,heap=False,allocation=False,shape=False):
    output.mkdir(parents=True,exist_ok=False)
    reference=DATA/'board-native-loss-a';origin=reference/'state/step-20.state'
    core=DATA/('trace-core-activity-backdrop-b/dosbox_pure_trace.dll' if heap or allocation or shape else 'trace-core-work-b/dosbox_pure_trace.dll');content=DATA/'source/reference-v1.zip'
    report=dict(passed=False,control=control,origin_sha256=digest(origin),core_sha256=digest(core),content_sha256=digest(content));native=None
    try:
        native=(Recorder if control else CursorRecorder)(core,content,output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        native.save('initial',ram=True)
        native.snapshot_boundary();pointer=next(p+o for s,p,o,l in native.memory if s==0 and p)
        ram=C.string_at(pointer,0x40000);py,px=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        decision=json.loads((reference/'run.json').read_text(encoding='utf-8'))['decisions'][21];x,y=decision['point']
        actions=[dict(frames=10,mouse=dict(dx=2*(x-px),dy=2*(y-py))),dict(frames=1,mouse=dict(left=True)),dict(frames=2000,mouse=dict(left=False))]
        report['actions']=actions
        if not control:
            low=next(p+o for s,p,o,l in native.memory if s==0x100000 and p);base=544+pointer-low
            resident={0x7668:'resource.handle',0x7684:'resource.handle.return',0x7aef:'resource.read',0xe5e2:'sound.start',0xe33c:'shape.load',0x6b06:'heap.prepare',0x6d47:'heap.allocate',0x6fd8:'heap.coalesce',0x6652:'heap.pack',0x66f0:'heap.pack.return',0x652a:'memory.handle.allocate',0x6554:'memory.handle.allocate.return',0x65fa:'memory.raw.allocate',0x661f:'memory.raw.allocate.return',0x8806:'cursor.set',0x85b1:'cursor.convert',0x85c8:'cursor.source'}
            native.labels={base+0xd510+address:name for address,name in resident.items()}
            native.labels[base+0xd510+0xe42a]='shape.load.return'
            addresses=(C.c_uint32*len(native.labels))(*native.labels)
            native.core.retro_treehouse_trace_configure(addresses,len(addresses),base+0x341ee)
            if heap or allocation or shape:
                assert native.core.retro_treehouse_heap_snapshot_size()==C.sizeof(HeapSnapshot)
                native.heap=True
                begin,end,requested=(0x652a,0x6554,24961) if allocation else (0x6652,0x66f0,0)
                if shape:begin,end,requested=0xe33c,0xe42a,1+65536*26254
                native.core.retro_treehouse_heap_configure.argtypes=[C.c_uint32,C.c_uint32,C.c_uint32]
                native.core.retro_treehouse_heap_configure(base+0xd510+begin,base+0xd510+end,requested)
            native.observe=True
        native.perform(actions);native.save('final',ram=True)
        report.update(passed=True,events=[] if control else native.events,cursor_events=[] if control else native.cursor_events,
                      capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
        if (heap or allocation or shape) and not control:report['heap']=native.read_heap()
        report['snapshot_operation']='shape' if shape else 'allocation' if allocation else 'packing' if heap else None
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],events=len(report['events']),cursor_events=report['cursor_events']),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--control',action='store_true')
    group=p.add_mutually_exclusive_group();group.add_argument('--heap',action='store_true');group.add_argument('--allocation',action='store_true');group.add_argument('--shape',action='store_true')
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.control,a.heap,a.allocation,a.shape) else 1)
