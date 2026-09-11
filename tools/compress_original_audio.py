"""Encode the rendered original audio as Ogg Vorbis for the default game's build.

Legacy keeps the raw 48 kHz WAVs: wr1_audio.gd reads their bytes directly and the
parity suite depends on them. The default game only needs the same sound at a
fraction of the download, so this writes an `ogg/` folder beside `playback/`
with a manifest whose loop points are seconds rather than sample indices.
"""
import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/audio/original/playback'
TARGET = ROOT / 'assets/audio/original/ogg'


def encode(source: Path, target: Path, quality: str) -> None:
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                    '-c:a', 'libvorbis', '-q:a', quality, str(target)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--quality', default='4', help='libvorbis -q:a (default 4, ~128 kbps)')
    args = parser.parse_args()
    if shutil.which('ffmpeg') is None:
        print('ffmpeg is required', file=sys.stderr)
        return 2

    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    rate = int(manifest['sample_rate'])
    TARGET.mkdir(parents=True, exist_ok=True)
    output = {'sample_rate': rate, 'source_manifest_sha256': manifest.get('source_exe_sha256', ''),
              'music': {}, 'effects': {}}

    for key, info in sorted(manifest['music'].items()):
        source = SOURCE / info['file']
        target = TARGET / (Path(info['file']).stem + '.ogg')
        encode(source, target, args.quality)
        with wave.open(str(source)) as handle:
            frames = handle.getnframes()
        # AudioStreamOggVorbis loops the whole stream from an offset in seconds.
        output['music'][key] = {'file': target.name, 'loop_offset': int(info['loop_begin']) / rate,
                                'loop_end_seconds': int(info['loop_end']) / rate,
                                'source_frames': frames}
        print(f'{source.name}: {source.stat().st_size:,} -> {target.stat().st_size:,} bytes')

    for name, info in sorted(manifest['effects'].items()):
        source = SOURCE / info['file']
        target = TARGET / (Path(info['file']).stem + '.ogg')
        encode(source, target, args.quality)
        output['effects'][name] = {'file': target.name,
                                   'logical_duration_samples': info['logical_duration_samples']}
        print(f'{source.name}: {source.stat().st_size:,} -> {target.stat().st_size:,} bytes')

    (TARGET / 'manifest.json').write_text(json.dumps(output, indent=2) + '\n')
    total_source = sum(p.stat().st_size for p in SOURCE.glob('*.wav'))
    total_target = sum(p.stat().st_size for p in TARGET.glob('*.ogg'))
    print(f'\ntotal: {total_source:,} -> {total_target:,} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
