"""Cursor helper inputs, state and intrinsic work; never modifies guest memory."""
import ctypes as C
import hashlib,json


class Sample(C.Structure):
    _fields_=[(n,C.c_int32) for n in ['budget','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done']]+[('milliseconds',C.c_double)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double)]+[(n,C.c_uint32) for n in ['ordinal','kind','edge','path_hash','last']]+[('counts',C.c_uint32*1080),('parent',C.c_int32)]+[(n,C.c_uint16*size) for n,size in [('pointer',2),('rect',4),('before',42),('after',42)]]+[('samples',Sample*2),('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('handles',C.c_uint16*4)]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.seen=set();self.rows=(Row*64)();self.digest=hashlib.sha256()
        if core.retro_treehouse_cursor_size()!=C.sizeof(Row):raise ValueError('Cursor observer ABI differs')
        core.retro_treehouse_cursor_configure(base);self.path=folder/'cursors.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_cursor_status():raise ValueError('Cursor observer failed: '+str(self.core.retro_treehouse_cursor_status()))
            n=self.core.retro_treehouse_cursor_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal in self.seen:raise ValueError('Duplicate cursor ordinal')
                self.seen.add(r.ordinal)
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['counts','samples']}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples]
                row['counts']={str(0x857a+i):v for i,v in enumerate(r.counts) if v}
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No cursor calls captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_cursor_partial(),scope='Nested cursor helpers, intrinsic work and 42 words of state. No guest writes.')
