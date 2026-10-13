"""Continuous animation loop initial/final memory and sparse clock fixtures."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['instruction','address']]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[('io',C.c_int64)]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done','flags']]+[('milliseconds',C.c_double)]+[(n,C.c_uint16) for n in ['ss','sp','bp','cs','ds','es','ax','bx','cx','dx','si','di']]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','instructions','path_hash','sample_count','stack_low']]+[(n,C.c_uint16) for n in ['instance','ds','ss','sp','bp','first_frame','base_id','activity']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('sound_initial',C.c_uint32*32),('mouse_initial',C.c_uint32*96),('dma_autoinit',C.c_uint32),('dma_initial',C.c_uint32*8),('mixer_initial',C.c_uint32*10),('channel_initial',C.c_int32*16),('last_dma_callback',C.c_double),('audio_frontend',C.c_double*7),('samples',Sample*131072),('before',C.c_uint8*0xb0000),('after',C.c_uint8*0xb0000)]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.rows=(Row*1)();self.digest=hashlib.sha256();self.folder=folder/'animation-loop';self.folder.mkdir()
        if core.retro_treehouse_animation_loop_size()!=C.sizeof(Row):raise ValueError('Animation loop ABI differs')
        core.retro_treehouse_animation_loop_configure(base);self.path=folder/'animation-loop.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_animation_loop_status():raise ValueError('Animation loop observer failed: '+str(self.core.retro_treehouse_animation_loop_status()))
            n=self.core.retro_treehouse_animation_loop_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Animation loop ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['samples','before','after']}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.sample_count]]
                payload=bytes(r.before)+bytes(r.after);path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['memory']=dict(path='animation-loop/'+path.name,sha256=hashlib.sha256(payload).hexdigest(),ram_size=0xb0000)
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No complete animation loops')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_animation_loop_partial(),scope='Main 4855 through pre-execution 48C0, including nested calls and IRQs. Full instruction count/hash and sparse clocks; initial/final RAM and initial device state. Offline comparison only.')
