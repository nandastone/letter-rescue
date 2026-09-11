"""Read-only measurements of generated WR1 audio and the native PCM capture.

This measures amplitude, endpoint discontinuities and diagnostic spectral
agreement. Spectral agreement does not establish waveform or timing parity.
Requires NumPy and SciPy; the existing testing/output/python_packages works.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

sys.path.insert(0, str(Path('testing/output/python_packages').resolve()))
import numpy as np


def read_wave(path):
    with wave.open(str(path), 'rb') as reader:
        assert reader.getsampwidth() == 2
        data = np.frombuffer(reader.readframes(reader.getnframes()), '<i2')
        return reader.getframerate(), data.reshape(-1, reader.getnchannels()).astype(float)


def measure(assets, native):
    manifest = json.loads((assets / 'manifest.json').read_text())
    result = {'music': {}, 'effects': {}}
    for group in ['music', 'effects']:
        for key, entry in manifest[group].items():
            rate, stereo = read_wave(assets / entry['file'])
            data = stereo[:, 0]
            item = dict(frames=len(data), seconds=len(data)/rate,
                        peak=float(np.abs(data).max()), rms=float(np.sqrt(np.mean(data**2))),
                        first_sample=float(data[0]), last_sample=float(data[-1]),
                        tail_mean=float(data[-min(48, len(data)):].mean()))
            if group == 'music':
                begin, end = entry['loop_begin'], entry['loop_end']
                item['loop_jump'] = float(data[begin] - data[end - 1])
                item['natural_first_loop_jump'] = float(data[begin] - data[begin - 1])
                item['largest_adjacent_step'] = float(np.abs(np.diff(data)).max())
            result[group][key] = item
    result['unity_native_gain_peak_bound'] = (
        max(x['peak'] for x in result['music'].values()) * 1.5 +
        max(x['peak'] for x in result['effects'].values()))
    rate, stereo = read_wave(native)
    mono = stereo.mean(axis=1)
    result['native'] = dict(seconds=len(mono)/rate, peak=float(np.abs(stereo).max()),
                            stereo_difference=float(np.abs(stereo[:,0]-stereo[:,1]).max()))
    # Reuse the independently reported single phrase-alignment offset. Compare
    # magnitudes, which survive oscillator phase differences. Do not optimize
    # an amplitude scale, warp time or label this PCM fidelity.
    _, asset_stereo = read_wave(assets / manifest['music']['4']['file'])
    asset = asset_stereo[:, 0]
    offset = 0.9386666666666663
    intervals = []
    for start in np.arange(12, 29, .25):
        length = int(rate * .25)
        a = asset[int((start-offset)*rate):int((start-offset)*rate)+length]
        b = mono[int(start*rate):int(start*rate)+length]
        fa = np.abs(np.fft.rfft(a * np.hanning(length)))
        fb = np.abs(np.fft.rfft(b * np.hanning(length)))
        # Narrow oscillator-bin phase/timing differences are reduced by 40 Hz
        # power bands, while retaining harmonic structure. Exclude DC.
        bins = (length//2)//10
        pa = np.sqrt((fa[1:1+bins*10]**2).reshape(bins,10).sum(axis=1))
        pb = np.sqrt((fb[1:1+bins*10]**2).reshape(bins,10).sum(axis=1))
        cosine = float(pa@pb/(np.linalg.norm(pa)*np.linalg.norm(pb)))
        gain = float(pa@pb/(pa@pa))
        intervals.append(dict(start=float(start), cosine=cosine, gain=gain))
    selected = [x for x in intervals if x['cosine'] > .97]
    result['diagnostic_music_magnitude_gain'] = dict(
        offset_seconds=offset, windows=intervals, high_similarity_windows=len(selected),
        median_gain=float(np.median([x['gain'] for x in selected])) if selected else None)
    return result


def measure_tails(assets, events_directory, renderer, output):
    """Render isolated effects through the existing unchanged speaker kernel."""
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((assets / 'manifest.json').read_text())
    result = {}
    for name in manifest['effects']:
        lines = (events_directory / f'{name}.txt').read_text().splitlines()
        rate, _, count = map(int, lines[0].split())
        off_ms = float(lines[-1].split()[0])
        lines[0] = f'{rate} {math.ceil(off_ms)+6005} {count}'
        event_path, pcm_path = output/f'{name}.txt', output/f'{name}.pcm'
        event_path.write_text('\n'.join(lines)+'\n')
        subprocess.run([str(renderer), str(event_path), str(pcm_path)], check=True)
        data = np.frombuffer(pcm_path.read_bytes(), '<i2')
        _, old = read_wave(assets / manifest['effects'][name]['file'])
        compare_frames = min(len(data), len(old))
        nz = np.flatnonzero(data)
        last_nonzero_ms = int(nz[-1])*1000/rate
        result[name] = dict(off_ms=off_ms,
            existing_prefix_exact=bool(np.array_equal(data[:compare_frames], old[:compare_frames, 0])),
            last_negative_5000_ms=int(np.flatnonzero(data == -5000)[-1])*1000/rate,
            last_nonzero_ms=last_nonzero_ms, tail_ms=last_nonzero_ms-off_ms,
            final_sample=int(data[-1]),
            tail_max_step=int(np.abs(np.diff(data[int((off_ms+2)*rate/1000):].astype(int))).max()))
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, default=Path('assets/audio/original/playback'))
    parser.add_argument('--native', type=Path, default=Path('testing/output/audio-20260909/native-continuous.wav'))
    parser.add_argument('--output', type=Path, default=Path('testing/output/audio-20260909/fidelity-analysis.json'))
    parser.add_argument('--speaker-tail', action='store_true', help='Also run the offline speaker renderer for tail measurements')
    parser.add_argument('--speaker-renderer', type=Path, default=Path('testing/output/wr1_speaker_render.exe'))
    parser.add_argument('--events-directory', type=Path, default=Path('testing/output/audio-20260909/assets'))
    args = parser.parse_args()
    result = measure(args.assets, args.native)
    if args.speaker_tail:
        result['tail_analysis'] = measure_tails(args.assets, args.events_directory,
            args.speaker_renderer, args.output.parent/'tail-analysis')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'diagnostic_music_magnitude_gain'}, indent=2))
    print('Magnitude gain in high-similarity windows:', result['diagnostic_music_magnitude_gain']['median_gain'])
