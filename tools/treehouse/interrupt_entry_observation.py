"""Read-only hardware interrupt entry/return register and stack fixtures."""
import ctypes as C
import hashlib,json


class State(C.Structure):
    _fields_=[(n,C.c_int32) for n in ['cycles','left','maximum']]+[('io',C.c_int64),('ticks',C.c_uint32),('milliseconds',C.c_double)]+[(n,C.c_uint32) for n in ['eip','flags']]+[('registers',C.c_uint32*8),('segments',C.c_uint32*6)]+[(n,C.c_uint32) for n in ['ss_base','cs_base','stack_mask','stack_notmask','code_big','extflags_toggle']]+[('direction',C.c_int32)]


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','kind','parent','vector','old_eip','vector_base','vector_ip','vector_cs']]+[('stack_addresses',C.c_uint32*3),('stack_before',C.c_uint16*3),('stack_after',C.c_uint16*3),('before',State),('after',State)]


def plain(value):
    if isinstance(value,C.Structure):return {n:plain(getattr(value,n)) for n,_ in value._fields_}
    if isinstance(value,C.Array):return list(value)
    return value


class Stream:
    def __init__(self,core,folder):
        self.core=core;self.count=0;self.rows=(Row*128)();self.digest=hashlib.sha256()
        if core.retro_treehouse_interrupt_entry_size()!=C.sizeof(Row):raise ValueError('Interrupt entry ABI differs')
        core.retro_treehouse_interrupt_entry_configure();self.path=folder/'interrupt-entry.jsonl';self.file=self.path.open('xb')

    def drain(self):
        if self.core.retro_treehouse_interrupt_entry_status():raise ValueError('Interrupt entry observer failed')
        while n:=self.core.retro_treehouse_interrupt_entry_read(self.rows,len(self.rows)):
            for row in self.rows[:n]:
                if row.ordinal!=self.count:raise ValueError('Interrupt entry ordinal differs')
                raw=(json.dumps(plain(row),separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No interrupt entry observations')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),boundaries=self.count,partial_final_calls=self.core.retro_treehouse_interrupt_entry_partial(),scope='Real-mode hardware IRQ0/7/12 entry after FillFlags, and matching outer IRET. Read-only stack/register/CPU snapshots; no guest work or timing mutation.')
