"""Offline DMA consumption, PCM and mixer phase/output fixtures."""
import ctypes as C
import hashlib,json


class Row(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ['ordinal','requested','ticks','frames']]+[(n,C.c_int32) for n in ['budget','left','maximum']]+[('io',C.c_int64)]+[(n,C.c_double) for n in ['milliseconds','last_before','last_after']]+[(n,C.c_uint32*32) for n in ['hardware_before','hardware_after']]+[(n,C.c_uint32*8) for n in ['dma_before','dma_after']]+[(n,C.c_int32*16) for n in ['channel_before','channel_after']]+[(n,C.c_uint32*10) for n in ['mixer_before','mixer_after']]+[(n,C.c_uint8*1024) for n in ['source','pcm']]+[('mixed_delta',C.c_int32*8192)]


class Stream:
    def __init__(self,core,folder):
        self.core=core;self.count=0;self.rows=(Row*16)();self.digest=hashlib.sha256()
        if core.retro_treehouse_audio_dma_size()!=C.sizeof(Row):raise ValueError('Audio DMA ABI differs')
        core.retro_treehouse_audio_dma_configure(1);self.path=folder/'audio-dma.jsonl';self.file=self.path.open('xb')

    def drain(self):
        while True:
            if self.core.retro_treehouse_audio_dma_status():raise ValueError('Audio DMA observer failed: '+str(self.core.retro_treehouse_audio_dma_status()))
            n=self.core.retro_treehouse_audio_dma_read(self.rows,len(self.rows))
            if not n:break
            for r in self.rows[:n]:
                if r.ordinal!=self.count:raise ValueError('Audio DMA ordinal differs')
                row={name:list(getattr(r,name)) if isinstance(getattr(r,name),C.Array) else getattr(r,name) for name,_ in Row._fields_ if name not in ['source','pcm','mixed_delta']}
                row['source']=bytes(r.source).hex();row['pcm']=bytes(r.pcm).hex();row['mixed_delta']=list(r.mixed_delta[:2*r.frames])
                raw=(json.dumps(row,separators=(',',':'))+'\n').encode();self.file.write(raw);self.digest.update(raw);self.count+=1

    def finish(self):
        self.drain();self.file.close()
        if not self.count:raise ValueError('No audio DMA calls')
        return dict(path=self.path.name,sha256=self.digest.hexdigest(),calls=self.count,scope='GenerateDMASound entry/exit, source and decoded/faded PCM, mixer phase and actual signed-32-bit output contribution. Initial state and resulting data are offline fixtures; no scheduling/input is changed.')
