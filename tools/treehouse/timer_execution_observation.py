"""Offline complete timer IRQ instruction/clock and memory fixtures."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[('address',C.c_uint32)]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[('io',C.c_int64)]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done','flags']]+[('milliseconds',C.c_double)]+[(n,C.c_uint16) for n in ['sp','ss','ds','es','ax','bx','cx','dx','si','di','bp']]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','count','stack_low','bios_address','user_address']]+[(n,C.c_uint16) for n in ['data_segment','entry_ss','entry_sp']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('bios_code',C.c_uint8*64),('user_code',C.c_uint8*64),('samples',Sample*4096),('before',C.c_uint8*0xb0000),('after',C.c_uint8*0xb0000)]


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.rows=(Row*1)();self.digest=hashlib.sha256();self.folder=folder/'timer-execution';self.folder.mkdir()
        if core.retro_treehouse_timer_execution_size()!=C.sizeof(Row):raise ValueError('Timer execution ABI differs')
        core.retro_treehouse_timer_execution_configure(base);self.path=folder/'timer-execution.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_timer_execution_status():raise ValueError('Timer execution observer failed: '+str(self.core.retro_treehouse_timer_execution_status()))
            n=self.core.retro_treehouse_timer_execution_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Timer ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['samples','before','after']}
                row['samples']=[{name:getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.count]]
                payload=bytes(r.before)+bytes(r.after);path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['memory']=dict(path='timer-execution/'+path.name,sha256=hashlib.sha256(payload).hexdigest(),ram_size=0xb0000)
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No timer calls captured')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_timer_execution_partial(),scope='Complete resident IRQ0 entry through pre-IRET, including chained BIOS instructions. RAM and ordered clocks are offline fixtures; the probe changes no guest memory or scheduling.')
