"""Whole animation-frame before/after RAM, work and clock comparisons."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['address','remaining']]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done']]+[('milliseconds',C.c_double)]


class Stage(C.Structure):
    _fields_=[('address',C.c_uint32),('stack_low',C.c_uint32),('args',C.c_uint16*12)]+[(n,C.c_uint16) for n in ['ax','bx','cx','dx','si','di','ds','es']]+[('memory',C.c_uint8*0xb0000)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double)]+[(n,C.c_uint32) for n in ['ordinal','path_hash','instructions','sample_count']]+[(n,C.c_uint16) for n in ['ds','ss','sp','instance']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('samples',Sample*4096),('addresses',C.c_uint32*262144),('before',C.c_uint8*0xb0000),('after',C.c_uint8*0xb0000),('conversion_source',C.c_uint32),('conversion_palette',C.c_uint32),('conversion',C.c_uint8*0xb0000)]+[(n,C.c_uint32) for n in ['stack_low','conversion_stack_low','stage_count']]+[('stages',Stage*5)]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.rows=(Row*1)();self.digest=hashlib.sha256();self.folder=folder/'frame-work';self.folder.mkdir()
        if core.retro_treehouse_frame_size()!=C.sizeof(Row):raise ValueError('Frame observer ABI differs')
        core.retro_treehouse_frame_configure(base);self.path=folder/'frame-work.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_frame_status():raise ValueError('Frame observer failed: '+str(self.core.retro_treehouse_frame_status()))
            n=self.core.retro_treehouse_frame_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Frame ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['samples','addresses','before','after','conversion','stages']}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.sample_count]]
                row['stages']=[{name:list(getattr(s,name)) if name=='args' else getattr(s,name) for name,_ in Stage._fields_ if name!='memory'} for s in r.stages[:r.stage_count]]
                payload=bytes(r.before)+bytes(r.after)+bytes(r.conversion)+b''.join(bytes(s.memory) for s in r.stages[:r.stage_count])+bytes(r.addresses)[:4*r.instructions];path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['memory']=dict(path='frame-work/'+path.name,sha256=hashlib.sha256(payload).hexdigest(),ram_size=0xb0000,ram_images=3+r.stage_count)
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No animation frames captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_frame_partial(),scope='Complete C78A frame calls, before/after RAM and all ordered guest instruction addresses. Comparison fixtures only; no guest writes.')
