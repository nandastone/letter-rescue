"""Stream completed CPU/callback boundary records at safe video callbacks."""
import ctypes as C
import hashlib,json


class Event(C.Structure):
    _fields_=[('milliseconds',C.c_double),('instructions',C.c_uint64),('strings',C.c_uint64),('credits',C.c_uint64),('io',C.c_int64)]+[(n,C.c_int32) for n in ['cycles','left','maximum','result']]+[(n,C.c_uint32) for n in ['kind','id','ticks','eip','last_address','flags']]+[(n,C.c_uint16) for n in ['cs','ax','bx','cx','dx','ss','sp']]+[('opcode',C.c_uint8*4)]


class Stream:
    def __init__(self,core,folder):
        self.core=core;self.count=0;self.digest=hashlib.sha256();self.rows=(Event*32768)();self.callbacks=set()
        if core.retro_treehouse_cpu_run_size()!=C.sizeof(Event):raise ValueError('CPU boundary ABI differs')
        core.retro_treehouse_cpu_callback_description.restype=C.c_char_p
        core.retro_treehouse_cpu_run_configure(1)
        self.path=folder/'cpu-runs.jsonl';self.file=self.path.open('xb')

    def drain(self):
        if self.core.retro_treehouse_cpu_run_status():raise ValueError('CPU boundary probe overflow')
        while True:
            n=self.core.retro_treehouse_cpu_run_read(self.rows,len(self.rows))
            if not n:break
            rows=[]
            for e in self.rows[:n]:
                if e.kind in [3,4]:self.callbacks.add(e.id)
                rows.append({name:list(e.opcode) if name=='opcode' else getattr(e,name) for name,_ in Event._fields_})
            payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode()
            self.file.write(payload);self.digest.update(payload);self.count+=n

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('Empty CPU boundary probe')
        labels={}
        for id in sorted(self.callbacks):
            raw=self.core.retro_treehouse_cpu_callback_description(id);labels[str(id)]=raw.decode('utf-8',errors='replace') if raw else None
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),events=self.count,callback_descriptions=labels)
