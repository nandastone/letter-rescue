"""Stream completed polling calls; guest data is an offline verification fixture."""
from pathlib import Path
import ctypes as C
import hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_16

ROOT=Path(__file__).resolve().parents[2]


class State(C.Structure):
    _fields_=[(n,C.c_uint16) for n in ['mouse_present','joystick','modifier']]+[('edges',C.c_uint16*2),('bindings',C.c_uint16*96),('keys',C.c_uint8*96),('latches',C.c_uint8*96)]


class Cpu(C.Structure):
    _fields_=[('context',C.c_uint64*5),('io',C.c_int64)]+[(n,C.c_int32) for n in ['cycles','left','maximum']]+[(n,C.c_uint32) for n in ['ticks','flags']]+[(n,C.c_uint16) for n in ['cs','ss','sp','bp']]+[('stack',C.c_uint16*16),('caller',C.c_uint16*16)]


class GapCount(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','address','entries']]


class Row(C.Structure):
    _fields_=[('begin',C.c_double),('end',C.c_double),('ordinal',C.c_uint32),('path_hash',C.c_uint32),('gap_count',C.c_uint32),('gap_hash',C.c_uint32),('gap_addresses',C.c_uint32*256),('result',C.c_uint16),('mouse_count',C.c_uint16),('mouse_buttons',C.c_uint16*2),('cpu_before',Cpu),('cpu_after',Cpu),('before',State),('after',State),('counts',C.c_uint32*512)]


def state(s):
    return {n:list(getattr(s,n)) if n in ['edges','bindings','keys','latches'] else getattr(s,n) for n,_ in State._fields_}


def cpu(s):
    return {n:list(getattr(s,n)) if n in ['context','stack','caller'] else getattr(s,n) for n,_ in Cpu._fields_}


class Stream:
    def __init__(self,core,folder,resident,read):
        self.core=core;self.count=0;self.digest=hashlib.sha256();self.rows=(Row*128)()
        if core.retro_treehouse_poll_size()!=C.sizeof(Row):raise ValueError('Polling observer ABI differs')
        if core.retro_treehouse_poll_gap_size()!=C.sizeof(GapCount):raise ValueError('Polling gap ABI differs')
        self.gap_rows=(GapCount*4096)();self.gap_count=0;self.gap_digest=hashlib.sha256();self.gap_path=folder/'poll-gaps.jsonl';self.gap_file=self.gap_path.open('xb')
        unpacked=(ROOT/'testing/output/treehouse/research-resources/unpacked.bin').read_bytes()
        if hashlib.sha256(unpacked).hexdigest()!='f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f':raise ValueError('Original EXE differs')
        decoder=Cs(CS_ARCH_X86,CS_MODE_16);addresses=[];self.labels=[]
        for lo,hi in [(0x5466,0x546e),(0x54c5,0x54e8),(0x57d3,0x5994),(0x5bb0,0x5c0f),(0x5c52,0x5c65)]:
            instructions=list(decoder.disasm(unpacked[0xd510+lo:0xd510+hi],lo))
            if instructions[-1].address+instructions[-1].size!=hi:raise ValueError('Polling range is not instruction aligned')
            for i in instructions:addresses.append(resident+i.address);self.labels.append(f'resident:{i.address:04x}')
        for vector,name,offsets in [(0x21,'dos',[0,1,5,6,7,8,11,13,14]),(0x33,'mouse',[0,9,13])]:
            offset,segment=struct.unpack('<HH',read(4*vector,4));base=segment*16+offset;code=read(base,15)
            if name=='dos' and code!=bytes.fromhex('fbfe382400cfcb51b94001e2fe59cf'):raise ValueError('DOS callback trampoline differs')
            if name=='mouse' and (code[:2]!=bytes.fromhex('eb07') or code[9:14]!=bytes.fromhex('fe381d00cf')):raise ValueError('Mouse callback trampoline differs')
            for offset in offsets:addresses.append(base+offset);self.labels.append(f'{name}:{offset:02x}')
        if len(addresses)>512:raise ValueError('Too many polling instruction addresses')
        points=(C.c_uint32*len(addresses))(*addresses);core.retro_treehouse_poll_configure(resident,points,len(addresses))
        self.path=folder/'polling.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            n=self.core.retro_treehouse_poll_gap_read(self.gap_rows,len(self.gap_rows))
            if not n:break
            payload=''.join(json.dumps([r.ordinal,r.address,r.entries],separators=(',',':'))+'\n' for r in self.gap_rows[:n]).encode();self.gap_file.write(payload);self.gap_digest.update(payload);self.gap_count+=n
        while True:
            if self.core.retro_treehouse_poll_status():raise ValueError('Polling probe overflow or nested call')
            n=self.core.retro_treehouse_poll_read(self.rows,len(self.rows))
            if not n:break
            rows=[]
            for r in self.rows[:n]:
                rows.append(dict(begin=r.begin,end=r.end,ordinal=r.ordinal,path_hash=r.path_hash,gap_count=r.gap_count,gap_hash=r.gap_hash,gap_addresses=list(r.gap_addresses)[:min(r.gap_count,256)],cpu_before=cpu(r.cpu_before),cpu_after=cpu(r.cpu_after),result=r.result,mouse_buttons=list(r.mouse_buttons)[:r.mouse_count],before=state(r.before),after=state(r.after),counts={label:r.counts[i] for i,label in enumerate(self.labels) if r.counts[i]}))
            payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode();self.file.write(payload);self.digest.update(payload);self.count+=n

    def finish(self):
        self.drain();self.file.close();self.gap_file.close()
        if not self.count:raise ValueError('No complete polling calls')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,partial_final_calls=self.core.retro_treehouse_poll_partial(),labels=self.labels,gap_path=self.gap_path.name,gap_sha256=self.gap_digest.hexdigest(),gap_rows=self.gap_count,gap_threshold=1024)
