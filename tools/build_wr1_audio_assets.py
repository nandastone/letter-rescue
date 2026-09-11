"""Build audible assets from original CMF music and executable speaker tables.

Music has an initial pass and a repeat segment, without the preview's extra
second of silence. Timing uses the recovered PIT cadence; PCM equality to the
complete native mixer is not claimed.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

from wr1_music_reference import Music
from wr1_opl_reference import Opl

RATE = 48000
IRQ = 12428 / 1193182
EXE_HASH = 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f'
SOUNDS = {'mystery_complete':0x336, 'recap':0x3e2, 'correct':0x43a,
          'wrong':0x456, 'slime':0x472, 'death':0x492, 'book':0x4ba,
          'slime_miss':0x4da, 'step':0x4ea, 'jump':0x4f6}


def music_events(data, tables):
    state = dict(counter=0, beats=0, division=struct.unpack_from('<H', data, 10)[0],
                 format=1, repeat=1, playing=1, data_offset=8,
                 tracks=[dict(active=1, delay=0, cursor=0, status=0)])
    music = Music(data, state)
    music.restart()
    opl = Opl(tables, data, dict(mode=1, rhythm=192, percussion=0, transpose=244,
              voices=[65535]*9, programs=[0]*16, volumes=[127]*16, notes=[0]*9,
              levels=[tables['default_instruments'][0][3]]*9, bends=[0]*16))
    bank = opl.instruments
    opl.instruments = copy.deepcopy(tables['default_instruments'])
    events = [(0, r, v) for r, v in opl.restart()]
    opl.instruments = bank
    boundaries = []
    for tick in range(1, 200001):
        sample = round(tick * IRQ * RATE)
        for midi in music.tick():
            events.extend((sample, r, v) for r, v in opl.event(midi))
        if music.restarted:
            events.extend((sample, r, v) for r, v in opl.restart())
            boundaries.append(sample)
            if len(boundaries) == 2:
                return events, boundaries
    raise ValueError('CMF did not complete two passes')


def write_wave(path, raw):
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(raw)


def build(exe, output, work, opl_renderer, speaker_renderer):
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXE_HASH:
        raise ValueError('Unsupported WR1.EXE')
    output.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    tables = json.loads(Path('assets/audio/original/driver_tables.json').read_text())
    result = dict(source_exe_sha256=EXE_HASH, sample_rate=RATE,
                  opl_renderer_sha256=hashlib.sha256(opl_renderer.read_bytes()).hexdigest(),
                  speaker_renderer_sha256=hashlib.sha256(speaker_renderer.read_bytes()).hexdigest(),
                  timing='Ideal original PIT cadence; native mixer PCM parity remains unverified',
                  music={}, effects={})
    for track in range(4, 7):
        cmf = Path(f'assets/audio/original/wr1_{track}.cmf')
        events, boundaries = music_events(cmf.read_bytes(), tables)
        event_file, pcm = work/f'music_{track}.bin', work/f'music_{track}.pcm'
        event_file.write_bytes(struct.pack('<III', RATE, len(events), boundaries[-1]) +
                               b''.join(struct.pack('<IBB', *e) for e in events))
        subprocess.run([str(opl_renderer.resolve()), str(event_file.resolve()), str(pcm.resolve())], check=True)
        wav = output/f'music_{track}.wav'
        write_wave(wav, pcm.read_bytes())
        result['music'][str(track)] = dict(file=wav.name, loop_begin=boundaries[0],
            loop_end=boundaries[1], cmf_sha256=hashlib.sha256(cmf.read_bytes()).hexdigest(),
            wav_sha256=hashlib.sha256(wav.read_bytes()).hexdigest())
    for name, offset in SOUNDS.items():
        entries = []
        for i in range(256):
            word, duration = struct.unpack_from('<HH', data, 0x24f50 + offset + i*4)
            entries.append([word, duration])
            if duration == 0:
                break
        else:
            raise ValueError('Unterminated speaker table')
        # Index zero is a delay sentinel: the IRQ increments before programming
        # the next entry. The EXE sends high byte first to PIT2's low-byte latch.
        events, ticks = [], entries[0][1]
        for word, duration in entries[1:]:
            divisor = ((word & 255) << 8) | (word >> 8)
            events.append((ticks * IRQ * 1000, divisor if duration else 0))
            ticks += duration
        # Native OFF holds its DC level for one second, then slews to zero
        # over five seconds. This tail does not keep the effect logically busy.
        logical_duration_samples = round(ticks * IRQ * RATE)
        total_ms = math.ceil(ticks * IRQ * 1000) + 6005
        event_file, pcm = work/f'{name}.txt', work/f'{name}.pcm'
        event_file.write_text(f'{RATE} {total_ms} {len(events)}\n' +
                              ''.join(f'{ms:.12f} {divisor}\n' for ms, divisor in events))
        subprocess.run([str(speaker_renderer.resolve()), str(event_file.resolve()), str(pcm.resolve())], check=True)
        wav = output/f'{name}.wav'
        write_wave(wav, pcm.read_bytes())
        result['effects'][name] = dict(file=wav.name, offset=offset, entries=entries,
            logical_duration_samples=logical_duration_samples,
            wav_sha256=hashlib.sha256(wav.read_bytes()).hexdigest())
    (output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Built three looping songs and', len(SOUNDS), 'original speaker effects')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('assets/audio/original/playback'))
    parser.add_argument('--work', type=Path, default=Path('testing/output/audio-20260909/assets'))
    parser.add_argument('--opl-renderer', type=Path, default=Path('testing/output/wr1_opl_render.exe'))
    parser.add_argument('--speaker-renderer', type=Path, default=Path('testing/output/wr1_speaker_render.exe'))
    args = parser.parse_args()
    build(args.exe, args.output, args.work, args.opl_renderer, args.speaker_renderer)
