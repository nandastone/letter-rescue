"""Read isolated PIC probe ABI without changing any emulator state."""
import ctypes as C
import hashlib,json


class State(C.Structure):
    _fields_=[(n,C.c_int32) for n in ['cycles','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','count','head_handler','head_value','hash']]+[(n,C.c_float) for n in ['head_index','tick_index']]+[('milliseconds',C.c_double),('servicing',C.c_uint32),('service_index',C.c_float)]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['kind','handler','value']]+[('delay',C.c_float),('before',State),('after',State)]


class Entry(C.Structure):
    _fields_=[('handler',C.c_uint32),('value',C.c_uint32),('index',C.c_float)]


def fields(s):return {name:getattr(s,name) for name,_ in s._fields_}


class Stream:
    def __init__(self,core,folder):
        self.core=core;self.folder=folder;self.count=0;self.digest=hashlib.sha256();self.rows=(Row*32768)()
        for name,struct in [('state',State),('row',Row),('entry',Entry)]:
            if getattr(core,'retro_treehouse_pic_'+name+'_size')()!=C.sizeof(struct):raise ValueError('PIC '+name+' ABI differs')
        core.retro_treehouse_pic_configure(1)
        state=State();entries=(Entry*512)();count=core.retro_treehouse_pic_initial(C.byref(state),entries,len(entries))
        if not count:raise ValueError('Empty initial PIC queue')
        self.initial=folder/'pic-initial.json';self.initial.write_text(json.dumps(dict(state=fields(state),entries=[fields(e) for e in entries[:count]]),indent=2),encoding='utf-8')
        self.path=folder/'pic.jsonl';self.file=self.path.open('xb')

    def drain(self):
        if self.core.retro_treehouse_pic_status():raise ValueError('PIC probe overflow')
        while True:
            n=self.core.retro_treehouse_pic_read(self.rows,len(self.rows))
            if not n:break
            payload=''.join(json.dumps(dict(kind=r.kind,handler=r.handler,value=r.value,delay=r.delay,before=fields(r.before),after=fields(r.after)),separators=(',',':'))+'\n' for r in self.rows[:n]).encode()
            self.file.write(payload);self.digest.update(payload);self.count+=n

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('PIC probe is empty')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),operations=self.count,initial_path=self.initial.name,initial_sha256=hashlib.sha256(self.initial.read_bytes()).hexdigest())
