"""Read-only interpreter work records, coalesced only when states/work agree."""
import ctypes as C
import hashlib,json


class State(C.Structure):
    _fields_=[(n,C.c_uint16) for n in ['instance','ds','context','display_count','sound_enabled','cue']]+[('wrapper',C.c_uint16*7),('drawing',C.c_uint16*9),('dimensions',C.c_uint16*60),('ticks',C.c_uint32),('memory',C.c_uint8*726),('code',C.c_uint8*256)]


class Payload(C.Structure):
    _fields_=[('before',State),('after',State),('counts',C.c_uint32*1533),('path_hash',C.c_uint32),('result',C.c_uint16),('reads',C.c_uint16),('tick_reads',C.c_uint32*16),('gap_count',C.c_uint32),('gap_hash',C.c_uint32),('gap_addresses',C.c_uint32*128),('drawing_counts',C.c_uint32*1462),('drawing_hash',C.c_uint32)]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double),('first_instruction',C.c_uint64),('last_instruction',C.c_uint64),('ordinal',C.c_uint32),('repeats',C.c_uint32),('payload',Payload)]


def state(s):
    return {n:bytes(getattr(s,n)).hex() if n in ['memory','code'] else list(getattr(s,n)) if n in ['wrapper','drawing','dimensions'] else getattr(s,n) for n,_ in State._fields_}


class Stream:
    def __init__(self,core,folder,base):
        self.core=core;self.count=0;self.calls=0;self.rows=(Row*64)();self.digest=hashlib.sha256()
        if core.retro_treehouse_script_size()!=C.sizeof(Row):raise ValueError('Script observer ABI differs')
        core.retro_treehouse_script_configure(base);self.path=folder/'script-work.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_script_status():raise ValueError('Script observer overflow/nested call')
            n=self.core.retro_treehouse_script_read(self.rows,len(self.rows))
            if not n:break
            rows=[]
            for r in self.rows[:n]:
                p=r.payload
                if r.ordinal!=self.calls or not r.repeats:raise ValueError('Script observer call sequence differs')
                rows.append(dict(begin=r.begin,end=r.end,first_instruction=r.first_instruction,last_instruction=r.last_instruction,ordinal=r.ordinal,repeats=r.repeats,before=state(p.before),after=state(p.after),counts={str(0xbda0+i):n for i,n in enumerate(p.counts) if n},path_hash=p.path_hash,result=p.result,tick_reads=list(p.tick_reads)[:p.reads],gap_count=p.gap_count,gap_hash=p.gap_hash,gap_addresses=list(p.gap_addresses)[:min(p.gap_count,128)]))
                rows[-1].update(drawing_counts={str(0xc78a+i):n for i,n in enumerate(p.drawing_counts) if n},drawing_hash=p.drawing_hash)
                self.calls+=r.repeats
            payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode();self.file.write(payload);self.digest.update(payload);self.count+=n

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No script interpreter calls')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),records=self.count,calls=self.calls,partial_final_calls=self.core.retro_treehouse_script_partial(),coalescing='Consecutive identical before/after memory, code, timer reads, return value and instruction counts/hash; timestamps and global CPU entry indices retain the first/last boundary.')
