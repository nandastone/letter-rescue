"""Offline rectangle, clipping and short memory helper operands and work."""
import ctypes as C
import hashlib,json


class Sample(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['address','remaining']]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done']]+[('milliseconds',C.c_double)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double)]+[(n,C.c_uint32) for n in ['ordinal','kind','path_hash','count_size']]+[('addresses',C.c_uint32*128),('counts',C.c_uint32*128),('sample_count',C.c_uint32),('data',C.c_uint32),('output',C.c_uint32),('parent',C.c_int32),('args',C.c_uint16*8),('context',C.c_uint16)]+[(n,C.c_uint16*size) for n,size in [('surface',16),('after_surface',16),('a',4),('b',4),('before',4),('after',4),('result',2)]]+[(n,C.c_uint8*64) for n in ['source_bytes','before_bytes','after_bytes']]+[('samples',Sample*32)]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.seen=set();self.rows=(Row*64)();self.digest=hashlib.sha256()
        if core.retro_treehouse_geometry_size()!=C.sizeof(Row):raise ValueError('Geometry observer ABI differs')
        core.retro_treehouse_geometry_configure(base);self.path=folder/'geometry.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_geometry_status():raise ValueError('Geometry observer failed: '+str(self.core.retro_treehouse_geometry_status()))
            n=self.core.retro_treehouse_geometry_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal in self.seen:raise ValueError('Duplicate geometry ordinal')
                self.seen.add(r.ordinal)
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['counts','addresses','samples']}
                row['counts']={str(r.addresses[i]):r.counts[i] for i in range(r.count_size)}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.sample_count]]
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No geometry helpers captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_geometry_partial(),scope='Rectangle/clipping helpers and near copy/fill up to 64 bytes. Intrinsic work, input/output operands and CPU samples; no guest writes.')
