"""Observe original nature draw calls without changing guest instructions/RAM.

Use the isolated trace DLL. Captures retain the same ordinary-input route as
the existing robot turn so instrumentation can be checked for side effects.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, struct
from PIL import Image
from capture import Recorder, digest

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'testing/output/treehouse'


class Event(C.Structure):
    _fields_=[('milliseconds',C.c_double),('address',C.c_uint32),('pit',C.c_uint32)]+[(n,C.c_uint16) for n in 'ax bx cx dx si di bp sp ss ds es cs'.split()]+[('stack',C.c_uint16*16)]


class WorkCall(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double),('ordinal',C.c_uint32),('stack',C.c_uint16*16),('header',C.c_uint16*3)]


class WorkCount(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['call','address','entries','repetitions']]


class WorkSlice(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['call','address','remaining']]+[('budget',C.c_int32)]


class WorkBlock(C.Structure):
    _fields_=[('call',C.c_uint32),('header',C.c_uint16*3)]


class WorkResult(C.Structure):
    _fields_=[('call',C.c_uint32)]+[(n,C.c_uint16) for n in ['ax','cx','dx']]


class TimerState(C.Structure):
    _fields_=[('call',C.c_uint32),('before',C.c_uint16*9),('after',C.c_uint16*9)]


class HeapSnapshot(C.Structure):
    _fields_=[('milliseconds',C.c_double),('phase',C.c_uint32),('requested',C.c_uint32),('ss',C.c_uint16),('sp',C.c_uint16),('ds',C.c_uint16)]


class DosTransfer(C.Structure):
    _fields_=[(n,C.c_int32) for n in ['bytes','cycles_before','cycles_after']]+[(n,C.c_int64) for n in ['io_before','io_after']]


class TraceRecorder(Recorder):
    def __init__(self,*args):
        self.configure=False;self.labels={};self.events=[];self.boundaries=[];self.probe_ready=False;self.profile='redraw';self.work=None;self.heap=False;self.heap_size=9612;self.dos_work=False;self.pic_work=False
        super().__init__(*args)
        assert self.core.retro_treehouse_trace_version()==1
        assert self.core.retro_treehouse_trace_size()==C.sizeof(Event)
        self.core.retro_treehouse_milliseconds.restype=C.c_double
        self.core.retro_treehouse_trace_configure.argtypes=[C.POINTER(C.c_uint32),C.c_uint,C.c_uint32]
        self.core.retro_treehouse_trace_read.argtypes=[C.POINTER(Event),C.c_uint]
        self.core.retro_treehouse_video_timing.argtypes=[C.POINTER(C.c_double)]
        self.core.retro_treehouse_live_rgb.argtypes=[C.POINTER(C.c_uint8),C.c_uint]
        self.probe_ready=True

    def video(self,*args):
        super().video(*args)
        if not self.probe_ready:return
        boundary=dict(run=self.run_index,milliseconds=self.core.retro_treehouse_milliseconds())
        if 1815<=self.run_index<=2800:
            timing=(C.c_double*16)();self.core.retro_treehouse_video_timing(timing)
            boundary['video_timing']=list(timing)
            rgb=(C.c_uint8*192000)();count=self.core.retro_treehouse_live_rgb(rgb,len(rgb))
            if count:
                raw=bytes(rgb);boundary['live_rgb_sha256']=hashlib.sha256(raw).hexdigest()
                if self.frame and raw!=self.frame.tobytes():
                    image=self.evidence/'live'/f'{self.run_index}.png';image.parent.mkdir(exist_ok=True)
                    Image.frombytes('RGB',(320,200),raw).save(image)
        self.boundaries.append(boundary)
        if getattr(self,'pic_stream',None):self.pic_stream.drain()
        if getattr(self,'cpu_run_stream',None):self.cpu_run_stream.drain()
        if getattr(self,'irq_stream',None):self.irq_stream.drain()
        if getattr(self,'poll_stream',None):self.poll_stream.drain()
        if getattr(self,'script_stream',None):self.script_stream.drain()
        if getattr(self,'blit_stream',None):self.blit_stream.drain()
        if getattr(self,'sprite_stream',None):self.sprite_stream.drain()
        if getattr(self,'cursor_stream',None):self.cursor_stream.drain()
        if getattr(self,'geometry_stream',None):self.geometry_stream.drain()
        if getattr(self,'frame_stream',None):self.frame_stream.drain()
        if getattr(self,'timer_execution_stream',None):self.timer_execution_stream.drain()
        if getattr(self,'device_execution_stream',None):self.device_execution_stream.drain()
        if getattr(self,'interrupt_entry_stream',None):self.interrupt_entry_stream.drain()
        if getattr(self,'animation_loop_stream',None):self.animation_loop_stream.drain()
        if getattr(self,'sound_start_stream',None):self.sound_start_stream.drain()
        if getattr(self,'activity_backdrop_stream',None):self.activity_backdrop_stream.drain()
        if getattr(self,'audio_dma_stream',None):self.audio_dma_stream.drain()
        batch=(Event*16384)();count=self.core.retro_treehouse_trace_read(batch,len(batch))
        for event in batch[:count]:
            row={name:list(value) if name=='stack' else value for name,_ in Event._fields_ for value in [getattr(event,name)]}
            row.update(before_callback=self.run_index,label=self.labels.get(event.address,hex(event.address)))
            self.events.append(row)
        if self.core.retro_treehouse_trace_overflow():raise ValueError('Trace overflow')
        if self.configure:
            self.configure=False
            pointer,length=next((p+o,l) for s,p,o,l in self.memory if s==0 and p)
            os_pointer=next(p+o for s,p,o,l in self.memory if s==0x100000 and p)
            physical_shift=pointer-os_pointer
            if not 0<=physical_shift<0xa0000:raise ValueError('Unexpected core memory map')
            ram=C.string_at(pointer,length);overlay=(DATA/'research-resources/overlay2.bin').read_bytes()
            signature=overlay[0x3adb:0x3b17]
            if ram.count(signature)!=1:raise ValueError('Nature overlay signature is not unique')
            overlay_base=ram.index(signature)-0x3adb+physical_shift
            nature={0x2f8f:'turn.switch',0x287e:'turn.actor',0x394a:'turn.answers',0x1e82:'cards.begin',0x1eb9:'card.draw',0x2fd5:'turn.offers',0x303e:'turn.ready',0x3206:'question.begin',0x32ad:'question.scr',0x32b2:'question.scr.done',0x3346:'answer.wait',0x3414:'answer.eliminate',0x342f:'answer.final.wait',0x3adb:'cleanup.begin',0x391d:'cleanup.answered',0x3e27:'reminder.begin',0x3e57:'reminder.wait',0x3e63:'reminder.restore',0x198a:'question.draw'}
            main={0x7f08:'rect.fill',0x56db:'wait',0x57a9:'sound.block',0xe5e2:'sound.start',0xe566:'sound.stop',0x7688:'resource.find'}
            self.labels={overlay_base+offset:name for offset,name in nature.items()}
            main_base=self.image_base+physical_shift
            self.labels.update({main_base+0xd510+offset:name for offset,name in main.items()})
            self.labels.update({main_base+offset:name for offset,name in {0x64a4:'shape.draw',0x6c2e:'shape.center',0x6416:'resource.group',0xc78a:'scr.display.begin',0xbe36:'scr.display.end',0xc7fb:'scr.copy.begin',0xc800:'scr.copy.end',0xc9ed:'scr.compose.begin'}.items()})
            if self.profile=='resources':
                # Matched entry/return points delimit dynamic costs. Includes
                # cache lookup, relocation, shape conversion and SCR preload;
                # these are observations, not a recorded runtime schedule.
                resident={0x7668:'resource.handle',0x7684:'resource.handle.return',
                    0x76f3:'resource.find.return',0x7a30:'resource.entry',
                    0x7aef:'resource.read',0x7bc9:'resource.lookup',
                    0x6510:'memory.lock',0x658a:'memory.retain',
                    0xe33c:'shape.load',0xe42a:'shape.load.return',
                    0xd580:'shape.convert',0xe42e:'palette.load',
                    0x8806:'cursor.set',0x8272:'shape.blit',
                    0x7e32:'rect.copy',0x7f08:'rect.fill',
                    0x7c96:'surface.allocate',0x7d9f:'surface.allocate.return',
                    0x65fa:'memory.raw.allocate',0x661f:'memory.raw.allocate.return',
                    0x652a:'memory.handle.allocate',0x6554:'memory.handle.allocate.return',
                    0x003d:'memory.near.allocate',0x0075:'memory.near.allocate.return',
                    0x6e8d:'memory.far.allocate',0x6ea2:'memory.far.allocate.return'}
                resident.update({0x64ce:'memory.handle.free',0x64fa:'memory.handle.free.return',
                    0x65d0:'memory.unlock',0x65e1:'memory.unlock.return',
                    0x65e4:'memory.raw.free',0x65f7:'memory.raw.free.return',
                    0x659e:'memory.discardable',0x65b2:'memory.flags',
                    0x756e:'memory.discard',0x75a8:'memory.discard.return',
                    0x75c6:'memory.address',0x75f0:'memory.address.return',
                    0x001c:'memory.near.free',0x003c:'memory.near.free.return'})
                resident.update({0x70e8:'memory.resize',0x7196:'memory.resize.return',
                    0xec54:'memory.promote',0xecc2:'memory.promote.move',0xec6b:'memory.promote.return',
                    0xecfa:'memory.reallocate',0xed3b:'memory.reallocate.return',
                    0x7a38:'memory.catalog.pin',0x7a61:'memory.catalog.restore',
                    0x7a6e:'memory.catalog.pin.outer',0x7ae0:'memory.catalog.restore.outer',
                    0x7aae:'memory.resource.restore',0x7ab7:'memory.resource.cached',
                    0x76b7:'memory.catalog.pin.find',0x76c9:'memory.catalog.restore.find'})
                resident.update({0xed67:'memory.grow.pin',0xed7e:'memory.grow.unpin',0xed85:'memory.grow.move',
                    0xec40:'memory.keep.resident'})
                resident.update({0xe4aa:'sound.load',0xe4dc:'sound.load.return',
                    0xe6e6:'sound.prepare',0xe960:'sound.prepare.return'})
                self.labels.update({main_base+0xd510+offset:name for offset,name in resident.items()})
                main={0x415f:'wrapper.begin',0x41f2:'wrapper.script.loaded',
                    0xc39d:'scr.allocate',0x4400:'wrapper.allocated',
                    0xc5dd:'scr.preload',0xc5e2:'scr.preload.return',
                    0xc787:'scr.allocate.return',
                    0xc3c9:'scr.object.allocated',0xc70c:'scr.backup.allocated',
                    0xbd14:'scr.free',0xbd9d:'scr.free.return',
                    0x4444:'wrapper.cursor',0x44a9:'wrapper.prepare',
                    0x44b1:'wrapper.prepared'}
                self.labels.update({main_base+offset:name for offset,name in main.items()})
            addresses=(C.c_uint32*len(self.labels))(*self.labels)
            self.core.retro_treehouse_trace_configure(addresses,len(addresses),main_base+0x341ee)
            self.location=dict(main_base=main_base,overlay_base=overlay_base,physical_shift=physical_shift,labels={str(k):v for k,v in self.labels.items()})
            if self.dos_work:
                assert self.core.retro_treehouse_dos_size()==C.sizeof(DosTransfer)
                self.core.retro_treehouse_dos_configure(1)
            if self.pic_work:
                from pic_observation import Stream
                self.pic_stream=Stream(self.core,self.evidence)
            if getattr(self,'cpu_runs',False):
                from cpu_run_observation import Stream
                self.cpu_run_stream=Stream(self.core,self.evidence)
            if getattr(self,'irq_work',False):
                from irq_observation import Stream
                self.irq_stream=Stream(self.core,self.evidence)
            if getattr(self,'poll_work',False):
                from poll_observation import Stream
                self.poll_stream=Stream(self.core,self.evidence,main_base+0xd510,lambda address,length:C.string_at(os_pointer+address,length))
            if getattr(self,'script_work',False):
                from script_observation import Stream
                self.script_stream=Stream(self.core,self.evidence,main_base)
            if getattr(self,'blit_work',False):
                from blit_observation import Stream
                self.blit_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if getattr(self,'frame_work',False):
                from frame_observation import Stream
                self.frame_stream=Stream(self.core,self.evidence,main_base)
            if getattr(self,'timer_execution',False):
                from timer_execution_observation import Stream
                self.timer_execution_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if getattr(self,'audio_dma',False):
                from audio_dma_observation import Stream
                self.audio_dma_stream=Stream(self.core,self.evidence)
            if getattr(self,'activity_backdrop',False):
                from activity_backdrop_observation import Stream
                self.activity_backdrop_stream=Stream(self.core,self.evidence,main_base)
            if getattr(self,'sound_start',False):
                from sound_start_observation import Stream
                self.sound_start_stream=Stream(self.core,self.evidence,main_base+0xd510,self.sound_start)
            if getattr(self,'animation_loop',False):
                from animation_loop_observation import Stream
                self.animation_loop_stream=Stream(self.core,self.evidence,main_base)
            if getattr(self,'interrupt_entry',False):
                from interrupt_entry_observation import Stream
                self.interrupt_entry_stream=Stream(self.core,self.evidence)
            if getattr(self,'device_execution',False):
                from device_execution_observation import Stream
                self.device_execution_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if getattr(self,'geometry_work',False):
                from geometry_observation import Stream
                self.geometry_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if getattr(self,'cursor_work',False):
                from cursor_observation import Stream
                self.cursor_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if getattr(self,'sprite_work',False):
                from sprite_observation import Stream
                self.sprite_stream=Stream(self.core,self.evidence,main_base+0xd510)
            if self.heap:
                assert self.core.retro_treehouse_heap_snapshot_size()==C.sizeof(HeapSnapshot)
                resident=main_base+0xd510
                self.core.retro_treehouse_heap_configure(resident+0x6b06,resident+0x6bb2,self.heap_size)
            if self.work:
                assert self.core.retro_treehouse_work_version()==1
                assert self.core.retro_treehouse_work_call_size()==C.sizeof(WorkCall)
                # Observe one original function's work. Header pointer word 5
                # applies only to DE10's in-place VGA nibble expansion.
                start,end,length,header={'nibbles':(0xde10,0xde77,0x6a,5),
                    'lzrows':(0xdf85,0xdfab,0xb9,0),
                    'lzcolumns':(0xe03e,0xe064,0xe2,0),
                    'heap':(0x6b06,0x6bb2,0x573,0),
                    'resource-read':(0x7aef,0x7bb7,0xda,0),
                    'resource-open':(0x794c,0x79cf,0x84,0),
                    'resource-lookup':(0x7bc9,0x7c52,0xcd,0),
                    'resource-cache':(0x7a66,0x7ae5,0xbf,16),
                    'resource-direct':(0x7688,0x76f3,0x90,0),
                    'lookup-address':(0x7bc9,0x7c52,0x166e,0),
                    'entry-memory':(0x7a30,0x7a65,0x7c97,16),
                    'sound-decode':(0xe964,0xe9d3,0x72,0),
                    'sound-prepare':(0xe6e6,0xe960,0x27d,0),
                    'memory-copy':(0x6c18,0x6ca1,0x114,0),
                    'first-fit':(0x6d47,0x6e31,0x3ca,0),
                    'memory-resize':(0x70e8,0x7196,0x120,0),
                    'handle-resize':(0xed3e,0xedc1,0x92,0),
                    'resource-total':(0x7a66,0x7ae5,0x10000,16),
                    'near-allocation':(0x003d,0x0075,0x5cf,0),
                    'timer':(0x6447,0x6487,0x41,17)}[self.work]
                resident=main_base+0xd510
                profile_base={'resource-cache':0x7a30,'lookup-address':0x6628,'entry-memory':0x6fa9,'resource-total':0}.get(self.work,start)
                self.core.retro_treehouse_work_configure(resident+start,resident+end,resident+profile_base,length,header)
                if self.work in ('entry-memory','first-fit','near-allocation'):
                    regions=([(0x7a30,0x7a66),(0x75c6,0x7668),(0xec14,0xec40),(0x6fa9,0x6fd8)] if self.work=='entry-memory' else [(0x6d47,0x6e8d),(0x6fd8,0x7011)] if self.work=='first-fit' else [(0x003d,0x0076),(0x0590,0x060c)])
                    pairs=(C.c_uint32*(2*len(regions)))(*[resident+p for pair in regions for p in pair])
                    self.core.retro_treehouse_work_regions(pairs,len(regions))

    def read_heap(self):
        if not self.heap:return None
        if self.core.retro_treehouse_heap_status():raise ValueError('Incomplete/overflowing heap snapshots')
        count=self.core.retro_treehouse_heap_count()
        if not count or count%2:raise ValueError('Unpaired heap snapshots')
        rows=[];folder=self.evidence/'heap';folder.mkdir()
        for index in range(count):
            header=HeapSnapshot();memory=(C.c_uint8*0xa0000)()
            size=self.core.retro_treehouse_heap_read(index,C.byref(header),memory,len(memory))
            if size!=len(memory) or header.phase!=index%2:raise ValueError('Invalid heap snapshot')
            row={name:getattr(header,name) for name,_ in HeapSnapshot._fields_}
            filename=f'heap/{index:02d}.bin';payload=bytes(memory)
            (self.evidence/filename).write_bytes(payload)
            rows.append(dict(**row,path=filename,sha256=hashlib.sha256(payload).hexdigest()))
        return rows

    def read_dos(self):
        if not self.dos_work:return None
        if self.core.retro_treehouse_dos_status():raise ValueError('DOS observation overflow')
        rows=(DosTransfer*4096)();count=self.core.retro_treehouse_dos_read(rows,len(rows))
        if not count:raise ValueError('No DOS transfers observed')
        return [{name:getattr(row,name) for name,_ in DosTransfer._fields_} for row in rows[:count]]

    def read_work(self):
        if not self.work:return None
        self.core.retro_get_system_av_info(C.byref(self.av))
        if self.core.retro_treehouse_work_status():raise ValueError('Incomplete/overflowing work profile')
        calls=(WorkCall*4096)();counts=(WorkCount*524288)();slices=(WorkSlice*2048)()
        n=self.core.retro_treehouse_work_read_calls(calls,len(calls))
        m=self.core.retro_treehouse_work_read_counts(counts,len(counts))
        read_slices=getattr(self.core,'retro_treehouse_work_read_slices',None)
        k=read_slices(slices,len(slices)) if read_slices else 0
        blocks=[]
        if getattr(self.core,'retro_treehouse_work_read_blocks',None):
            if self.core.retro_treehouse_work_block_size()!=C.sizeof(WorkBlock):raise ValueError('Work block observer ABI differs')
            rows=(WorkBlock*4096)();count=self.core.retro_treehouse_work_read_blocks(rows,len(rows))
            if count!=n:raise ValueError('Incomplete block-header observations')
            blocks=[dict(call=r.call,header=list(r.header)) for r in rows[:count]]
        results=[]
        if getattr(self.core,'retro_treehouse_work_read_results',None):
            if self.core.retro_treehouse_work_result_size()!=C.sizeof(WorkResult):raise ValueError('Work return observer ABI differs')
            rows=(WorkResult*4096)();count=self.core.retro_treehouse_work_read_results(rows,len(rows))
            if count!=n:raise ValueError('Incomplete work return observations')
            results=[{name:getattr(r,name) for name,_ in WorkResult._fields_} for r in rows[:count]]
        timer_states=[]
        if self.work=='timer':
            if self.core.retro_treehouse_timer_state_size()!=C.sizeof(TimerState):raise ValueError('Timer state ABI differs')
            rows=(TimerState*4096)();count=self.core.retro_treehouse_timer_read_states(rows,len(rows))
            if count!=n:raise ValueError('Incomplete timer states')
            timer_states=[dict(call=r.call,before=list(r.before),after=list(r.after)) for r in rows[:count]]
        if not n or not m:raise ValueError('Work profile observed nothing')
        return dict(routine={'nibbles':'resident:DE10','lzrows':'resident:DF85','lzcolumns':'resident:E03E','heap':'resident:6B06','resource-read':'resident:7AEF','resource-open':'resident:794C','resource-lookup':'resident:7BC9','resource-cache':'resident:7A66','resource-direct':'resident:7688','lookup-address':'resident:7BC9+6628','entry-memory':'resident:7A30+memory','sound-decode':'resident:E964','sound-prepare':'resident:E6E6','memory-copy':'resident:6C18','first-fit':'resident:6D47','memory-resize':'resident:70E8','handle-resize':'resident:ED3E','resource-total':'resident:7A66+all','near-allocation':'resident:003D+0590','timer':'resident:6447'}[self.work],scope='Instruction entries inside selected code region; elapsed time includes interruptions, counts exclude callees and interrupt handlers outside the selected region',
            calls=[dict(begin=c.begin,end=c.end,ordinal=c.ordinal,stack=list(c.stack),header=list(c.header)) for c in calls[:n]],
            counts=[{name:getattr(c,name) for name,_ in WorkCount._fields_} for c in counts[:m]],
            slices=[{name:getattr(c,name) for name,_ in WorkSlice._fields_} for c in slices[:k]],blocks=blocks,results=results,timer_states=timer_states)


def run(core,output,no_probe=False,profile='redraw',work=None,heap=False,heap_size=9612,dos_work=False,pic_work=False,cpu_runs=False,irq_work=False,poll_work=False,script_work=False,blit_work=False,sprite_work=False,cursor_work=False,geometry_work=False,frame_work=False,timer_execution=False,device_execution=False,interrupt_entry=False,animation_loop=False,sound_start=False,audio_dma=False,activity_backdrop=False):
    if irq_work or poll_work or script_work:cpu_runs=True
    output.mkdir(parents=True,exist_ok=False);native=None
    origin=DATA/'research-nature/quiz-answer-capture/state/quiz-answer.state'
    try:
        native=TraceRecorder(core,DATA/'source/reference-v1.zip',output)
        native.profile=profile;native.work=work;native.heap=heap;native.heap_size=heap_size;native.dos_work=dos_work;native.pic_work=pic_work;native.cpu_runs=cpu_runs;native.irq_work=irq_work;native.poll_work=poll_work
        native.script_work=script_work
        native.blit_work=blit_work;native.sprite_work=sprite_work;native.cursor_work=cursor_work;native.geometry_work=geometry_work;native.frame_work=frame_work;native.timer_execution=timer_execution;native.device_execution=device_execution;native.interrupt_entry=interrupt_entry;native.animation_loop=animation_loop;native.sound_start=sound_start;native.audio_dma=audio_dma;native.activity_backdrop=activity_backdrop
        native.perform([dict(frames=1800)]);native.restore(origin);native.configure=not no_probe
        pointer=next(p+o for s,p,o,l in native.memory if s==0 and p)
        py,px=struct.unpack('<hh',C.string_at(pointer+0x34454,4))
        actions=[dict(frames=15,mouse=dict(dx=2*(150-px),dy=2*(20-py)),capture='before'),dict(frames=1,mouse=dict(left=True)),dict(frames=1300,capture='after')]
        native.perform(actions)
        native.core.retro_get_system_av_info(C.byref(native.av))
        work_report=native.read_work()
        heap_report=native.read_heap()
        dos_report=native.read_dos()
        pic_report=None
        if pic_work:
            pic_report=native.pic_stream.finish()
        cpu_report=native.cpu_run_stream.finish() if cpu_runs else None
        irq_report=native.irq_stream.finish() if irq_work else None
        poll_report=native.poll_stream.finish() if poll_work else None
        script_report=native.script_stream.finish() if script_work else None
        blit_report=native.blit_stream.finish() if blit_work else None
        sprite_report=native.sprite_stream.finish() if sprite_work else None
        cursor_report=native.cursor_stream.finish() if cursor_work else None
        geometry_report=native.geometry_stream.finish() if geometry_work else None
        frame_report=native.frame_stream.finish() if frame_work else None
        timer_execution_report=native.timer_execution_stream.finish() if timer_execution else None
        device_execution_report=native.device_execution_stream.finish() if device_execution else None
        interrupt_entry_report=native.interrupt_entry_stream.finish() if interrupt_entry else None
        audio_dma_report=native.audio_dma_stream.finish() if audio_dma else None
        activity_backdrop_report=native.activity_backdrop_stream.finish() if activity_backdrop else None
        sound_start_report=native.sound_start_stream.finish() if sound_start else None
        animation_loop_report=native.animation_loop_stream.finish() if animation_loop else None
    finally:
        if native:native.close()
    report=dict(core_sha256=digest(core),origin_sha256=digest(origin),actions=actions,snapshot_boundary_version=native.snapshot_boundary_version,snapshot_boundary='finish pending frame before restore/save',profile=profile,no_probe=no_probe,location=getattr(native,'location',None),events=native.events,boundaries=native.boundaries,work=work_report,heap=heap_report,dos=dos_report,pic=pic_report,cpu_runs=cpu_report,irq=irq_report,polling=poll_report,script_work=script_report,blits=blit_report,sprites=sprite_report,cursors=cursor_report,geometry=geometry_report,frames_work=frame_report,timer_execution=timer_execution_report,device_execution=device_execution_report,interrupt_entry=interrupt_entry_report,animation_loop=animation_loop_report,sound_start=sound_start_report,audio_dma=audio_dma_report,activity_backdrop=activity_backdrop_report)
    (output/'trace.json').write_text(json.dumps(report,indent=2));print('Captured',len(native.events),'entries')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-probe',action='store_true');p.add_argument('--profile',choices=['redraw','resources'],default='redraw');p.add_argument('--work',choices=['nibbles','lzrows','lzcolumns','heap','resource-read','resource-open','resource-lookup','resource-cache','resource-direct','lookup-address','entry-memory','sound-decode','sound-prepare','memory-copy','first-fit','memory-resize','handle-resize','resource-total','near-allocation','timer']);p.add_argument('--heap',action='store_true');p.add_argument('--heap-size',type=int,default=9612,help='Requested payload size to snapshot; zero observes all calls')
    p.add_argument('--dos-work',action='store_true');p.add_argument('--pic-work',action='store_true');p.add_argument('--cpu-runs',action='store_true');p.add_argument('--irq-work',action='store_true');p.add_argument('--poll-work',action='store_true');p.add_argument('--script-work',action='store_true');p.add_argument('--blit-work',action='store_true');p.add_argument('--sprite-work',action='store_true');p.add_argument('--cursor-work',action='store_true');p.add_argument('--geometry-work',action='store_true');p.add_argument('--frame-work',action='store_true');p.add_argument('--timer-execution',action='store_true');p.add_argument('--device-execution',action='store_true');p.add_argument('--interrupt-entry',action='store_true');p.add_argument('--animation-loop',action='store_true');p.add_argument('--sound-start',type=int,metavar='RESOURCE_ID');p.add_argument('--audio-dma',action='store_true');p.add_argument('--activity-backdrop',action='store_true');a=p.parse_args()
    if a.sound_start is not None and not 1<=a.sound_start<=65535:p.error('Sound-start RESOURCE_ID must be 1..65535')
    if a.no_probe and (a.work or a.heap or a.dos_work or a.pic_work or a.cpu_runs or a.irq_work or a.poll_work or a.script_work or a.blit_work or a.sprite_work or a.cursor_work or a.geometry_work or a.frame_work or a.timer_execution or a.device_execution or a.interrupt_entry or a.animation_loop or a.sound_start or a.audio_dma or a.activity_backdrop):p.error('Work/heap/DOS/PIC/CPU/IRQ/polling/script/blit observations require probes enabled')
    run(a.core,a.output,a.no_probe,a.profile,a.work,a.heap,a.heap_size,a.dos_work,a.pic_work,a.cpu_runs,a.irq_work,a.poll_work,a.script_work,a.blit_work,a.sprite_work,a.cursor_work,a.geometry_work,a.frame_work,a.timer_execution,a.device_execution,a.interrupt_entry,a.animation_loop,a.sound_start,a.audio_dma,a.activity_backdrop)
