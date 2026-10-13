"""Offline complete resident sound-start instruction/clock and memory fixtures."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[('address',C.c_uint32)]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[('io',C.c_int64)]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done','flags']]+[('milliseconds',C.c_double)]+[(n,C.c_uint16) for n in ['sp','ss','ds','es','cs','ax','bx','cx','dx','si','di','bp']]+[('code',C.c_uint8*8)]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','sound_id','count','stack_low','entry_address']]+[(n,C.c_uint16) for n in ['data_segment','entry_ss','entry_sp']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('hardware_before',C.c_uint32*32),('hardware_after',C.c_uint32*32),('dma_autoinit_before',C.c_uint32),('dma_autoinit_after',C.c_uint32),('samples',Sample*32768),('before',C.c_uint8*0xb0000),('after',C.c_uint8*0xb0000)]


class Stream:
    def __init__(self,core,folder,base,sound_id):
        self.sound_id=sound_id;self.core=core;self.count=0;self.rows=(Row*1)();self.digest=hashlib.sha256();self.folder=folder/'sound-start';self.folder.mkdir()
        if core.retro_treehouse_sound_start_size()!=C.sizeof(Row):raise ValueError('Sound-start ABI differs')
        core.retro_treehouse_sound_start_configure(base,sound_id);self.path=folder/'sound-start.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_sound_start_status():raise ValueError('Sound-start observer failed: '+str(self.core.retro_treehouse_sound_start_status()))
            n=self.core.retro_treehouse_sound_start_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Sound-start ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['samples','before','after']}
                row['samples']=[{name:list(getattr(s,name)) if name=='code' else getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.count]]
                payload=bytes(r.before)+bytes(r.after);path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['memory']=dict(path='sound-start/'+path.name,sha256=hashlib.sha256(payload).hexdigest(),ram_size=0xb0000)
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No device calls captured')
        return dict(sound_id=self.sound_id,path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_sound_start_partial(),scope='Resident E5E2 entry through E5F6 pre-RETF, including preparation and driver calls. RAM, code bytes and ordered clocks are offline fixtures; the probe changes no guest state or scheduling.')
