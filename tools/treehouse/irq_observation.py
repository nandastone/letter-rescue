"""Read-only dual PIC controller observation stream."""
import ctypes as C
import hashlib,json


class Controller(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['icw_words','icw_index','special','auto_eoi','rotate','single','request_isr','vector','irr','imr','imrr','isr','isrr','active']]


class State(C.Structure):
    _fields_=[('cycles',C.c_int32),('left',C.c_int32)]+[(n,C.c_uint32) for n in ['check','interrupt_enabled','trap']]+[('controllers',Controller*2)]


class Row(C.Structure):
    _fields_=[('milliseconds',C.c_double),('context',C.c_uint64*5),('io',C.c_int64)]+[(n,C.c_uint32) for n in ['kind','arg','value']]+[('vector',C.c_int32),('before',State),('after',State)]


def state(s):
    return {**{n:getattr(s,n) for n,_ in State._fields_ if n!='controllers'},'controllers':[{n:getattr(c,n) for n,_ in Controller._fields_} for c in s.controllers]}


class Stream:
    def __init__(self,core,folder):
        self.core=core;self.count=0;self.digest=hashlib.sha256();self.rows=(Row*8192)()
        if core.retro_treehouse_irq_state_size()!=C.sizeof(State) or core.retro_treehouse_irq_row_size()!=C.sizeof(Row):raise ValueError('IRQ observer ABI differs')
        core.retro_treehouse_irq_configure(1);initial=State();core.retro_treehouse_irq_initial(C.byref(initial))
        self.initial=folder/'irq-initial.json';self.initial.write_text(json.dumps(state(initial),indent=2),encoding='utf-8')
        self.path=folder/'irq.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_irq_status():raise ValueError('IRQ probe overflow or incomplete operation')
            n=self.core.retro_treehouse_irq_read(self.rows,len(self.rows))
            if self.core.retro_treehouse_irq_status():raise ValueError('IRQ probe drain interrupted an operation')
            if not n:break
            rows=[dict(milliseconds=r.milliseconds,context=list(r.context),io=r.io,kind=r.kind,arg=r.arg,value=r.value,vector=r.vector,before=state(r.before),after=state(r.after)) for r in self.rows[:n]]
            payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode();self.file.write(payload);self.digest.update(payload);self.count+=n

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('Empty IRQ observations')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),operations=self.count,initial_path=self.initial.name,initial_sha256=hashlib.sha256(self.initial.read_bytes()).hexdigest())
