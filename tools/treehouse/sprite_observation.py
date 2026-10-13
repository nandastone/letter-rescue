"""Offline VGA sprite operands, work and pixels around its inner drawing loop."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[('address',C.c_uint32),('remaining',C.c_uint32)]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done']]+[('milliseconds',C.c_double)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double),('ordinal',C.c_uint32),('path_hash',C.c_uint32),('counts',C.c_uint32*1002),('sample_count',C.c_uint32)]+[(n,C.c_uint16) for n in ['kind','color','mode','x','y','context']]+[(n,C.c_uint16*size) for n,size in [('shape',3),('surface',16),('rows',256),('rect',4)]]+[(n,C.c_uint32) for n in ['source_size','destination_size','drawn']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('samples',Sample*512)]+[(n,C.c_uint8*65536) for n in ['source_pixels','before_pixels','after_pixels']]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.seen=set();self.rows=(Row*8)();self.digest=hashlib.sha256();self.folder=folder/'sprites';self.folder.mkdir()
        if core.retro_treehouse_sprite_size()!=C.sizeof(Row):raise ValueError('Sprite observer ABI differs')
        core.retro_treehouse_sprite_configure(base);self.path=folder/'sprites.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_sprite_status():raise ValueError('Sprite observer failed: '+str(self.core.retro_treehouse_sprite_status()))
            n=self.core.retro_treehouse_sprite_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal in self.seen:raise ValueError('Duplicate sprite ordinal')
                self.seen.add(r.ordinal)
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['counts','samples','source_pixels','before_pixels','after_pixels']}
                row['counts']={str(0x9ed6+i):n for i,n in enumerate(r.counts) if n}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.sample_count]]
                payload=bytes(r.source_pixels[:r.source_size])+(bytes(r.before_pixels[:r.destination_size])+bytes(r.after_pixels[:r.destination_size]) if r.drawn else b'')
                path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['pixels']=dict(path='sprites/'+path.name,sha256=hashlib.sha256(payload).hexdigest())
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No sprites captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_sprite_partial(),scope='VGA sprite intrinsic work, CPU samples and indexed pixel inputs/output. Cursor helper effects are outside pixel pairs. No guest writes.')
