"""Observe the original resource arenas at startup without instruction profiling."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest
from trace_nature_redraw import TraceRecorder,HeapSnapshot,DATA


class StartupRecorder(TraceRecorder):
    def __init__(self,core,content,output,stage,allocation_bytes=0):
        self.stage=stage;self.allocation_bytes=allocation_bytes
        super().__init__(core,content,output)

    def before_load(self):
        # retro_load_game runs startup before returning the first video frame.
        # Configure observers here, before that synchronous startup begins.
        base=0x1a80
        labels={0xd5cc:'near.initialize',0xd5f1:'near.initialize.return',0x13d8b:'heap.initialize',0x13e9d:'heap.initialize.return',
                0:'game.main',0xd54d:'near.allocate',0xd582:'near.allocate.return',0xd52c:'near.free',
                0x13db2:'arena.request',0x13dc5:'arena.allocated',0x13de2:'arena.headers',
                0xdb1c:'near.grow',0xdba5:'near.grow.return',0xdba8:'near.break',0xdbf8:'near.break.return',
                0x13c9b:'arena.grow',0x13d1c:'arena.grow.return',0x13ccb:'arena.resize.request',0x13cd3:'arena.resize.return',
                0x13a3a:'handle.allocate',0x13a64:'handle.allocate.return',0x13b0a:'raw.allocate',0x13b2f:'raw.allocate.return',
                0x15648:'font.source',0x1564d:'font.source.return',0x15653:'font.activate.return',
                0x15d25:'cursor.source',0x15d29:'cursor.source.return',0x15d2e:'cursor.activate.return',
                0x14d18:'catalog.open',0x14d8e:'catalog.open.return',0x33e:'startup.sound',0x34d:'startup.sound.return',
                0xc39d:'animation.create',0xc77c:'animation.create.return',0x6416:'palette.load',0x6483:'palette.load.return',
                0xace:'entrance.prepare',0xd0e:'entrance.prepare.return',
                0x805:'entrance.select',0x930:'entrance.select.return',
                0x1f24:'room.prepare',0x22d9:'room.prepare.return',
                0x2196:'room.objects.before',0x21b1:'room.objects.after',
                0x5204:'room.transfer',0x530a:'room.transfer.return',
                0x3217:'room.release',0x3289:'room.release.return',
                # Pinned overlay slot; original signature checked after capture.
                0x24fc0+0xb2b:'board.options.prepare',0x24fc0+0xbf3:'board.options.painted'}
        self.labels={base+a:n for a,n in labels.items()}
        addresses=(C.c_uint32*len(labels))(*self.labels)
        self.core.retro_treehouse_trace_configure.argtypes=[C.POINTER(C.c_uint32),C.c_uint,C.c_uint32]
        self.core.retro_treehouse_trace_configure(addresses,len(labels),base+0x341ee)
        assert self.core.retro_treehouse_heap_snapshot_size()==C.sizeof(HeapSnapshot)
        self.heap=True
        begin,end={'near':(0xd5cc,0xd5f1),'heap':(0x13d8b,0x13e9d),'near-growth':(0xdb1c,0xdba5),'arena-growth':(0x13c9b,0x13d1c),'handle-allocation':(0x13a3a,0x13a64),'raw-allocation':(0x13b0a,0x13b2f),'font-source':(0x15648,0x1564d),'font-activation':(0x1564d,0x15653),'cursor-source':(0x15d25,0x15d29),'cursor-activation':(0x15d29,0x15d2e),'catalog':(0x14d18,0x14d8e),'startup-sound':(0x33e,0x34d),'animation':(0xc39d,0xc77c),'palette':(0x6416,0x6483),'entrance':(0xace,0xd0e),'selection':(0x805,0x930),'room':(0x1f24,0x22d9),'room-objects':(0x2196,0x21b1),'room-transfer':(0x5204,0x530a),'room-release':(0x3217,0x3289),'board-options':(0x24fc0+0xb2b,0x24fc0+0xbf3)}[self.stage]
        self.core.retro_treehouse_heap_configure.argtypes=[C.c_uint32,C.c_uint32,C.c_uint32]
        self.core.retro_treehouse_heap_configure(base+begin,base+end,self.allocation_bytes)


def capture(output,stage,fixed_clock=False,allocation_bytes=0,choose=None,board=False):
    if board and (choose!='boy' or not fixed_clock):raise ValueError('Board route currently requires fixed-clock boy startup')
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    content=DATA/('source/reference-startup-v2.zip' if fixed_clock else 'source/reference-v1.zip')
    report=dict(passed=False,stage=stage,fixed_clock=fixed_clock,allocation_bytes=allocation_bytes,core_sha256=digest(core),content_sha256=digest(content),actions=[dict(frames=1800)])
    if choose:
        # From the untouched initial pointer (160,100), choose via ordinary
        # mouse input. No game/resource state is installed for this capture.
        x=90 if choose=='boy' else 140
        report['actions'].extend([dict(frames=10,mouse=dict(dx=2*(x-160),dy=60)),dict(frames=4,mouse=dict(left=True)),dict(frames=1800)])
        report['choose']=choose
    if board:
        # Ordinary input at the first completed room display in the pinned
        # recording. This capture schedule is never browser runtime input.
        report['actions'][-1]=dict(frames=663)
        report['actions'].extend([dict(frames=1,mouse=dict(dx=180,dy=120)),dict(frames=1,mouse=dict(left=True)),dict(frames=1800)])
        report['activity']='board'
    native=None
    try:
        native=Recorder(core,content,output) if stage=='control' else StartupRecorder(core,content,output,stage,allocation_bytes)
        # This pinned DOS startup loads the executable at physical 1A80.
        # Confirm its independently located signatures after startup; these
        # addresses configure offline observers, never the browser runtime.
        base=0x1a80
        native.perform(report['actions']);native.save('final',ram=True)
        pointer=next(p+o for s,p,o,l in native.memory if s==0 and p)
        low=next(p+o for s,p,o,l in native.memory if s==0x100000 and p)
        assert native.image_base+pointer-low==base,'Unexpected original executable location'
        if board:
            length=next(l for s,p,o,l in native.memory if s==0 and p)
            ram=C.string_at(pointer,length)
            report['board_options_scene']=struct.unpack_from('<h',ram,native.image_base+0x31690+0xb34)[0]
            assert report['board_options_scene']==10,'Board options were not reached'
            if stage=='board-options':
                overlay=(DATA/'research-resources/overlay3.bin').read_bytes();signature=overlay[0x986:0x99b]
                assert ram.count(signature)==1 and ram.index(signature)-0x986+pointer-low==base+0x24fc0,'Unexpected board overlay slot'
        report.update(passed=True,main_base=base,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
        if stage!='control':
            report.update(events=native.events,heap_count=native.core.retro_treehouse_heap_count(),heap_status=native.core.retro_treehouse_heap_status())
            report['heap']=native.read_heap()
            if stage in ['near','heap']:assert len(report['heap'])==2,'Expected one startup operation'
    except Exception as error:
        report.update(passed=False,error=str(error));raise
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],stage=stage,events=len(report.get('events',[])),snapshots=len(report.get('heap',[]))),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',choices=['heap','near','near-growth','arena-growth','handle-allocation','raw-allocation','font-source','font-activation','cursor-source','cursor-activation','catalog','startup-sound','animation','palette','entrance','selection','room','room-objects','room-transfer','room-release','board-options','control'],required=True)
    p.add_argument('--fixed-clock',action='store_true')
    p.add_argument('--allocation-bytes',type=int,default=0)
    p.add_argument('--choose',choices=['boy','girl'])
    p.add_argument('--board',action='store_true')
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.stage,a.fixed_clock,a.allocation_bytes,a.choose,a.board) else 1)
