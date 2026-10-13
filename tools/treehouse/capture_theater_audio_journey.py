"""Observe the digital sound sequence during the ordinary theater journey.

Reads the current source at existing safe video boundaries. It does not patch
the game or replace inputs. The full recording can be checked against the
previous uninstrumented journey before using these observations as evidence.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,struct
import capture_theater_journey as journey
from capture import Recorder,digest


class AudioRecorder(Recorder):
    def __init__(self,core,content,output):
        self.sound_rows=[];self.sound_signature=None;self.sound_output=output
        super().__init__(core,content,output)

    def video(self,data,width,height,pitch):
        super().video(data,width,height,pitch)
        if self.capture_boundary_version!=1 or not self.game_ready():return
        ptr,length=next((p+o,l) for s,p,o,l in self.memory if s==0 and p)
        ds=ptr+0x323f0
        active=struct.unpack('<h',C.string_at(ds+0x211c,2))[0]
        off,seg=struct.unpack('<HH',C.string_at(ds+0x2120,4))
        address=seg*16+off-0x1860
        header=None;pcm_sha=None
        if active and 0<=address<=length-10:
            header=list(struct.unpack('<BHBHHH',C.string_at(ptr+address,10)))
        signature=(active,address,tuple(header or []))
        if signature==self.sound_signature:return
        self.sound_signature=signature
        if header and 0<header[3]<=length-address-10:
            pcm_sha=hashlib.sha256(C.string_at(ptr+address+10,header[3])).hexdigest()
        self.sound_rows.append(dict(callback=self.callback_index-1,run=self.run_index,
            audio_sample=len(self.audio)//4,tick=struct.unpack('<I',C.string_at(ds+0x201e,4))[0],
            active=active,source=[off,seg],header=header,pcm_sha256=pcm_sha))

    def close(self):
        super().close()
        (self.sound_output/'sound-observations.json').write_text(json.dumps(dict(
            tool_sha256=digest(Path(__file__)),rows=self.sound_rows,
            scope='Read-only source observations at safe video boundaries; short events between callbacks may be absent. Audio sample indices are observation boundaries, not exact start timestamps.'
        ),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    journey.Recorder=AudioRecorder
    raise SystemExit(0 if journey.capture(a.output) else 1)
