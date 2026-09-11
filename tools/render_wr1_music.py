"""Render reconstructed CMF music for listening, not native PCM parity claims.

Uses recovered MIDI/OPL rules and the pinned native synth. IRQs are placed at
the hardware period; intra-IRQ execution delays and DOSBox mixer resampling
are not yet modeled. The generated WAV is a research preview.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import wave

from wr1_music_reference import Music
from wr1_opl_reference import Opl


def sequence(data,tables,rate=48000):
    initial = dict(counter=0,beats=0,division=struct.unpack_from('<H',data,10)[0],
                   format=1,repeat=0,playing=1,data_offset=8,
                   tracks=[dict(active=1,delay=0,cursor=0,status=0)])
    music = Music(data,initial)
    music.restart()
    state = dict(mode=1,rhythm=192,percussion=0,transpose=244,
                 voices=[65535]*9,programs=[0]*16,volumes=[127]*16,
                 notes=[0]*9,levels=[tables['default_instruments'][0][3]]*9,bends=[0]*16)
    opl = Opl(tables,data,state)
    # CMF setup resets instruments before copying its new instrument bank.
    bank = opl.instruments
    opl.instruments = copy.deepcopy(tables['default_instruments'])
    events = [(0,register,value) for register,value in opl.restart()]
    opl.instruments = bank
    ticks = count = 0
    while music.state['playing']:
        ticks += 1
        if ticks>200000:
            raise ValueError('Song did not terminate within the research limit')
        sample = round(ticks*12428*rate/1193182)
        for midi in music.tick():
            count += 1
            events += [(sample,reg,value) for reg,value in opl.event(midi)]
    return events,sample+rate,ticks,count


def render(music_file,output,renderer,rate=48000):
    data = music_file.read_bytes()
    tables = json.loads(Path('assets/audio/original/driver_tables.json').read_text())
    events,total,ticks,count = sequence(data,tables,rate)
    output.parent.mkdir(parents=True,exist_ok=True)
    binary,pcm = output.with_suffix('.events.bin'),output.with_suffix('.pcm')
    binary.write_bytes(struct.pack('<III',rate,len(events),total)+b''.join(struct.pack('<IBB',*e) for e in events))
    subprocess.run([str(renderer.resolve()),str(binary.resolve()),str(pcm.resolve())],check=True)
    raw = pcm.read_bytes()
    if len(raw)!=total*2:
        raise ValueError('Rendered sample count differs from requested duration')
    with wave.open(str(output),'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(raw)
    manifest = dict(music_file=music_file.as_posix(),music_sha256=hashlib.sha256(data).hexdigest(),
                    wav_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),irq_ticks=ticks,
                    midi_events=count,register_writes=len(events),sample_rate=rate,samples=total,
                    timing='Ideal IRQ cadence; intra-IRQ CPU delays and native mixer output are unverified')
    output.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Rendered {music_file.name}: {ticks} IRQ ticks, {count} MIDI events, {total/rate:.2f}s')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('music',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--renderer',type=Path,default=Path('testing/output/wr1_opl_render.exe'))
    args = parser.parse_args()
    render(args.music,args.output,args.renderer)
