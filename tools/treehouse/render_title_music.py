"""Generate title PCM from original MIDI, independent FM logic and pinned DBOPL."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import wave
import zipfile

from build_demo import ROOT, SOURCE_SHA
from executable import unpack
from fm_music import MelodicDriver
from midi import extract

CORE_HASHES = {
    'dbopl.cpp': '53a8f2759a93f0d5252131f59812f60095a35e1db36f6ad97bdcacca6c3853aa',
    'dbopl.h': '5177a45aa8efbf2f8bbbceb51a325f9b5d9af98457b131cdb2421699248e1da4',
}


def build(source: Path, output: Path, compiler: Path, core: Path, sound: int = 20200, after_title: bool = False):
    output.mkdir(parents=True, exist_ok=False)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    music = extract(source)
    with zipfile.ZipFile(source) as archive:
        image, _ = unpack(archive.read('TheTreeh/treehse.exe'))
    frequencies = list(struct.unpack_from('<14H', image, 0x31130))
    operators = list(image[0x31297:0x312a9])
    title = music['tracks'][f'midisnd:{sound}']
    name = 'title' if sound == 20200 else 'selection' if sound == 20000 else f'music-{sound}'
    driver = MelodicDriver(music['bank'], frequencies, operators)
    if after_title:
        for event in music['tracks']['midisnd:20200']['native']['events']:
            driver.event(event)
        driver.irq = 0
        driver.writes = []
        driver.reset()
    initial_cursor = driver.cursor
    for event in title['native']['events']:
        driver.event(event)
    writes = driver.writes
    # At end-of-track the original resets the driver, releasing every note.
    end = title['native']['duration_irqs']
    for voice in range(9):
        writes.extend([dict(irq=end, register=0xa0 + voice, value=0),
                       dict(irq=end, register=0xb0 + voice, value=0)])
    rate = 48000
    # Source timer setup uses integer PIT division; reference hardware uses this
    # oscillator rate. Intra-interrupt driver execution time is not modeled here.
    sample = lambda irq: (irq * 4971 * rate + 1193181) // 1193182
    total = sample(end) + (0 if title['loop'] else rate)
    schedule = output / 'registers.txt'
    schedule.write_text(f'{rate} {total} {len(writes)}\n' + ''.join(
        f"{sample(w['irq'])} {w['register']} {w['value']}\n" for w in writes), encoding='ascii')
    for source_name, expected in CORE_HASHES.items():
        raw = (core / 'src/hardware' / source_name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, f'Unpinned {source_name}'
        (output / source_name).write_bytes(raw)
    shutil.copyfile(core / 'LICENSE', output / 'DBOPL-LICENSE.txt')
    for source_name in ('dosbox.h', 'adlib.h', 'render.cpp'):
        shutil.copyfile(Path(__file__).with_name('opl_standalone') / source_name, output / source_name)
    executable = output / 'render.exe'
    command = [str(compiler), '-std=c++17', '-O2', '-static', str(output / 'render.cpp'),
               str(output / 'dbopl.cpp'), '-o', str(executable)]
    environment = dict(os.environ, PATH=str(compiler.resolve().parent) + os.pathsep + os.environ.get('PATH', ''))
    result = subprocess.run(command, capture_output=True, text=True, env=environment)
    (output / 'compile.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    result.check_returncode()
    pcm = output / f'{name}.pcm'
    subprocess.run([str(executable), str(schedule), str(pcm)], check=True)
    assert pcm.stat().st_size == total * 2
    target = output / f'{name}.wav'
    with wave.open(str(target), 'wb') as audio:
        audio.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        audio.writeframes(pcm.read_bytes())
    report = dict(source_sha256=SOURCE_SHA, synth_sources=CORE_HASHES, rate=rate,
                  title_source_sha256=title['source_sha256'], frames=total,
                  sound=sound, name=name, loop=title['loop'], initial_cursor=initial_cursor,
                  wav_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  registers=len(writes), end_irq=end,
                  limitations=['Waveform/mixer parity unverified', 'Register writes within each timer interrupt share a sample boundary'])
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'testing/output/treehouse/source/The_Treehouse_1991.zip')
    parser.add_argument('--core', type=Path, default=ROOT / 'testing/output/treehouse/capture-core')
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--install', action='store_true', help='Install generated WAV and provenance into the Godot data directory')
    parser.add_argument('--sound', type=int, default=20200)
    parser.add_argument('--after-title', action='store_true', help='Derive initial FM allocation state from the complete source title track')
    args = parser.parse_args()
    report = build(args.source, args.output, args.compiler, args.core, args.sound, args.after_title)
    if args.install:
        destination = ROOT / 'treehouse-godot/data'
        destination.mkdir(parents=True, exist_ok=True)
        name = report['name']
        shutil.copyfile(args.output / f'{name}.wav', destination / f'{name}.wav')
        shutil.copyfile(args.output / 'report.json', destination / f'{name}-music.build.json')
        settings = destination / f'{name}.wav.import'
        if settings.exists():
            text = settings.read_text(encoding='utf-8')
            if 'compress/mode=' not in text:
                raise ValueError('Existing WAV import settings have no compression setting')
            text = re.sub(r'compress/mode=\d+', 'compress/mode=0', text)
        else:
            text = '[remap]\nimporter="wav"\ntype="AudioStreamWAV"\n\n[params]\ncompress/mode=0\nedit/trim=false\nedit/normalize=false\n'
        settings.write_text(text, encoding='utf-8')
    print(json.dumps(report, indent=2))
