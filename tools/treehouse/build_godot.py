"""Export recovered Treehouse resources to the independent Godot project."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from build_demo import ROOT, decode_assets
from executable import unpack
from midi import extract
from resource_startup_inputs import extract as extract_resource_startup


def build(source: Path, output: Path) -> dict:
    assets = decode_assets(source)
    assets['resource_ownership'] = extract_resource_startup(source)
    midi = extract(source)
    title = midi['tracks']['midisnd:20200']
    with zipfile.ZipFile(source) as archive:
        image, _ = unpack(archive.read('TheTreeh/treehse.exe'))
    ds = 0x321d0
    assets['startup'] = dict(
        origin=list(reversed(struct.unpack_from('<2h', image, ds + 0x14b4))),
        wipe_bounds=list(struct.unpack_from('<4h', image, ds + 0x14b8)),
        sparkles=[list(reversed(struct.unpack_from('<2h', image, ds + 0x14c0 + 4*i))) for i in range(3)],
        cues=[dict(value=e['data'][0], irq=e['irq']) for e in title['native']['events']
              if e['kind'] == 'meta' and e['meta'] == 7 and e['data']],
        end_irq=title['native']['duration_irqs'],
        source_sha256=title['source_sha256'], pit_divisor=4971, pit_hz=1193182)
    title_wav = ROOT / 'treehouse-godot/data/title.wav'
    title_manifest = ROOT / 'treehouse-godot/data/title-music.build.json'
    if not title_wav.exists() or not title_manifest.exists():
        raise ValueError('Generate title music with render_title_music.py --install before building Godot')
    manifest = json.loads(title_manifest.read_text(encoding='utf-8'))
    if (manifest['source_sha256'] != assets['provenance']['source_sha256'] or
            manifest['title_source_sha256'] != title['source_sha256'] or
            manifest['wav_sha256'] != hashlib.sha256(title_wav.read_bytes()).hexdigest()):
        raise ValueError('Title music asset does not match its original-source manifest')
    selection_wav = ROOT / 'treehouse-godot/data/selection.wav'
    selection_manifest = json.loads((ROOT / 'treehouse-godot/data/selection-music.build.json').read_text(encoding='utf-8'))
    if (selection_manifest['source_sha256'] != assets['provenance']['source_sha256'] or
            selection_manifest['title_source_sha256'] != midi['tracks']['midisnd:20000']['source_sha256'] or
            selection_manifest['wav_sha256'] != hashlib.sha256(selection_wav.read_bytes()).hexdigest()):
        raise ValueError('Selection music asset does not match its original-source manifest')
    for name in ('title', 'selection'):
        if 'compress/mode=0' not in (ROOT / f'treehouse-godot/data/{name}.wav.import').read_text(encoding='utf-8'):
            raise ValueError(f'{name} WAV must be imported without lossy compression')
    assets['fm_music'] = {}
    for sound in (20000, 20001, 20100, 20101, 20102, 20103):
        name = 'selection' if sound == 20000 else f'music-{sound}'
        track = midi['tracks'][f'midisnd:{sound}']
        wav = ROOT / f'treehouse-godot/data/{name}.wav'
        provenance = json.loads((ROOT / f'treehouse-godot/data/{name}-music.build.json').read_text(encoding='utf-8'))
        if (provenance['source_sha256'] != assets['provenance']['source_sha256'] or
                provenance['title_source_sha256'] != track['source_sha256'] or
                provenance['wav_sha256'] != hashlib.sha256(wav.read_bytes()).hexdigest() or
                provenance['end_irq'] != track['native']['duration_irqs'] or
                provenance['loop'] != track['loop']):
            raise ValueError(f'{name} music does not match its original-source manifest')
        if 'compress/mode=0' not in wav.with_suffix('.wav.import').read_text(encoding='utf-8'):
            raise ValueError(f'{name} WAV must be imported without lossy compression')
        assets['fm_music'][str(sound)] = dict(path=f'res://data/{name}.wav', loop=track['loop'],
                                             end_irq=track['native']['duration_irqs'])
    # Godot strings reject U+0000; retain the exact table as Unicode integers.
    assets['music']['cp437_codes'] = [ord(c) for c in assets['music'].pop('cp437')]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(assets, separators=(',', ':'), ensure_ascii=True), encoding='utf-8')
    report = dict(output=str(output.resolve()), sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  source_sha256=assets['provenance']['source_sha256'],
                  shapes=len(assets['shapes']), scripts=len(assets['scripts']),
                  title_wav_sha256=manifest['wav_sha256'], selection_wav_sha256=selection_manifest['wav_sha256'])
    output.with_suffix('.build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip')
    parser.add_argument('--output', type=Path, default=ROOT/'treehouse-godot/data/original.json')
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
