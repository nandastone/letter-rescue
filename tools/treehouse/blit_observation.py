"""Surface-copy inputs, intrinsic work and copy-loop output, kept offline."""
import ctypes as C
import gzip,hashlib,json


class Slice(C.Structure):
    _fields_=[('address',C.c_uint32),('remaining',C.c_uint32)]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done']]+[('milliseconds',C.c_double)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double),('ordinal',C.c_uint32),('path_hash',C.c_uint32),('counts',C.c_uint32*496),('slice_count',C.c_uint32)]+[(n,C.c_uint16) for n in ['mode','context','source_id','destination_id']]+[(n,C.c_uint16*size) for n,size in [('source',16),('destination',16),('source_rect',4),('destination_rect',4),('source_rows',256),('destination_rows',256)]]+[(n,C.c_uint32) for n in ['source_size','destination_size','copied']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('slices',Slice*512)]+[(n,C.c_uint8*65536) for n in ['source_pixels','before_pixels','after_pixels']]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.seen=set();self.rows=(Row*8)();self.digest=hashlib.sha256();self.folder=folder/'blits';self.folder.mkdir()
        if core.retro_treehouse_blit_size()!=C.sizeof(Row):raise ValueError('Surface-copy ABI differs')
        core.retro_treehouse_blit_configure(base);self.path=folder/'blits.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_blit_status():raise ValueError('Surface-copy observer failed: '+str(self.core.retro_treehouse_blit_status()))
            n=self.core.retro_treehouse_blit_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal in self.seen:raise ValueError('Repeated surface-copy ordinal')
                self.seen.add(r.ordinal)
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['counts','slices','source_pixels','before_pixels','after_pixels']}
                row['counts']={str(0x9a68+i):n for i,n in enumerate(r.counts) if n}
                row['slices']=[{name:getattr(s,name) for name,_ in Slice._fields_} for s in r.slices[:r.slice_count]]
                if r.copied:
                    payload=bytes(r.source_pixels[:r.source_size])+bytes(r.before_pixels[:r.destination_size])+bytes(r.after_pixels[:r.destination_size])
                    path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['pixels']=dict(path='blits/'+path.name,sha256=hashlib.sha256(payload).hexdigest())
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No surface copies captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_blit_partial(),scope='Intrinsic VGA copy instructions and REP budgets. Surface metadata at call entry; pixels after cursor preparation and before cursor restoration. No guest writes.')
