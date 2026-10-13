"""Offline complete resident activity-backdrop instruction/clock and memory fixtures."""
import ctypes as C
import gzip,hashlib,json


class Sample(C.Structure):
    _fields_=[('address',C.c_uint32)]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[('io',C.c_int64)]+[(n,C.c_uint32) for n in ['ticks','parts_left','lines_done','flags']]+[('milliseconds',C.c_double)]+[(n,C.c_uint16) for n in ['sp','ss','ds','es','cs','ax','bx','cx','dx','si','di','bp']]+[('code',C.c_uint8*8)]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','attribute','count','stack_low','entry_address']]+[(n,C.c_uint16) for n in ['data_segment','entry_ss','entry_sp']]+[('video_delays',C.c_float*5)]+[(n,C.c_uint32) for n in ['parts_total','parts_lines','lines_total']]+[('hardware_before',C.c_uint32*32),('hardware_after',C.c_uint32*32),('dma_autoinit_before',C.c_uint32),('dma_autoinit_after',C.c_uint32),('samples',Sample*262144),('checkpoint_count',C.c_uint32),('checkpoint_instruction',C.c_uint32*8),('checkpoint_address',C.c_uint32*8),('checkpoint_ram',(C.c_uint8*0xb0000)*8),('before',C.c_uint8*0xb0000),('after',C.c_uint8*0xb0000)]


class Stream:
    def __init__(self,core,folder,base,attribute=0):
        self.attribute=attribute;self.core=core;self.count=0;self.rows=(Row*1)();self.digest=hashlib.sha256();self.folder=folder/'activity-backdrop';self.folder.mkdir()
        if core.retro_treehouse_activity_backdrop_size()!=C.sizeof(Row):raise ValueError('Activity-backdrop ABI differs')
        core.retro_treehouse_activity_backdrop_configure(base,attribute);self.path=folder/'activity-backdrop.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_activity_backdrop_status():raise ValueError('Activity-backdrop observer failed: '+str(self.core.retro_treehouse_activity_backdrop_status()))
            n=self.core.retro_treehouse_activity_backdrop_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Activity-backdrop ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['samples','before','after','checkpoint_count','checkpoint_instruction','checkpoint_address','checkpoint_ram']}
                row['samples']=[{name:list(getattr(s,name)) if name=='code' else getattr(s,name) for name,_ in Sample._fields_} for s in r.samples[:r.count]]
                row['checkpoints']=[]
                for i in range(r.checkpoint_count):
                    payload=bytes(r.checkpoint_ram[i]);path=self.folder/f'{r.ordinal:04d}-checkpoint-{i}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0))
                    row['checkpoints'].append(dict(instruction=r.checkpoint_instruction[i],address=r.checkpoint_address[i],path='activity-backdrop/'+path.name,sha256=hashlib.sha256(payload).hexdigest()))
                payload=bytes(r.before)+bytes(r.after);path=self.folder/f'{r.ordinal:04d}.bin.gz';path.write_bytes(gzip.compress(payload,mtime=0));row['memory']=dict(path='activity-backdrop/'+path.name,sha256=hashlib.sha256(payload).hexdigest(),ram_size=0xb0000)
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No device calls captured')
        return dict(attribute=self.attribute,path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_activity_backdrop_partial(),scope='Main 4E15 entry through 4E9B pre-RETF, including overlay and temporary surface work. RAM, code bytes and ordered clocks are offline fixtures; the probe changes no guest state or scheduling.')
