"""Import the verified registered WR2/WR3 builds without altering WR1 assets.

python tools/import_episodes.py "D:/path/to/registered/files"
The existing recovered engine supplies behaviour; these are content imports,
not native timing checkpoints. See testing/wr2_wr3_source_research.md.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image
from convert_levels import parse_level, convert_to_game_format
from decode_wr1_demo import decode as decode_demo

ROOT = Path(__file__).resolve().parents[1]
BUILDS = {
    2: dict(sha256='6bd51a4c199bee7ebe18f8b6da040a9a1e4dd10ffcc9ed2e8367d28187329ab1',
            ds=0x24eb0, title=0xc0, shift=0x36, demos=[5, 1, 11, 13, 15, 20]),
    3: dict(sha256='551b40a25931b392980d49e2f61367536b614e42b1362aedd3693d16b973b236',
            ds=0x24ef0, title=0xbc, shift=0x32, demos=[3, 7, 9, 10, 19, 20]),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def archive(data):
    assert struct.unpack_from('<H', data)[0] == 0xca01
    result = {}
    for i in range(struct.unpack_from('<H', data, 0x5e)[0]):
        at = 0x80 + i * 26
        name = data[at + 1:at + 14].split(b'\0')[0].decode('ascii').replace(' ', '').upper()
        start, length = struct.unpack_from('<II', data, at + 14)
        assert start + length <= len(data)
        result[name] = data[start:start + length]
    return result


def image(data):
    raster = Image.open(io.BytesIO(data)).convert('RGBA')
    # PCX six-bit expansion differs from EGA registers; index 6 is brown.
    pixels = []
    for rgba in raster.getdata():
        rgb = tuple({87: 85, 171: 170}.get(c, c) for c in rgba[:3])
        if rgb == (170, 170, 0):
            rgb = (170, 85, 0)
        pixels.append((*rgb, rgba[3]))
    raster.putdata(pixels)
    return raster


def masked(raster, key):
    raster.putdata([(0, 0, 0, 0) if p[:3] == key else p for p in raster.getdata()])
    return raster


def titles(exe, build):
    rows = []
    for index in range(20):
        values = []
        for column in range(2):
            offset, segment = struct.unpack_from('<HH', exe, build['ds'] + build['title'] + index * 8 + column * 4)
            assert segment * 16 + 0x2a00 == build['ds']
            start = build['ds'] + offset
            values.append(exe[start:exe.index(b'\0', start)].decode('ascii'))
        assert values[0] == f'Level {index + 1}'
        rows.append(dict(heading=values[0], name=values[1]))
    return dict(source_sha256=digest(exe), titles=rows)


def import_episode(source, number):
    build = BUILDS[number]
    prefix = f'wr{number}'
    exe = (source / f'{prefix}.exe').read_bytes()
    if digest(exe) != build['sha256']:
        raise ValueError(f'Unsupported {prefix}.exe: refusing to use offsets from another build')
    data_root = ROOT / f'data/episodes/{prefix}'
    art_root = ROOT / f'assets/episodes/{prefix}'
    manifest = dict(episode=number, level_count=20, source_exe_sha256=digest(exe),
                    sources={}, sprites=[], map_edge_markers=[])
    sheets = {}
    for suffix, folder in [('1', 'art'), ('2', 'pictures')]:
        raw = (source / f'{prefix}.{suffix}').read_bytes()
        manifest['sources'][f'{prefix}.{suffix}'] = digest(raw)
        for name, payload in archive(raw).items():
            raster = image(payload)
            target = art_root / folder / f'{name}.png'
            target.parent.mkdir(parents=True, exist_ok=True)
            raster.save(target)
            if folder == 'art':
                sheets[name] = raster
    # Registered packages reuse the same publisher logo.
    logo = source / f'{prefix}.7'
    if not logo.exists():
        logo = source / 'WORD/WR1.7'
    image(logo.read_bytes()).save(art_root / 'art' / f'WR{number}.7.png')

    words_raw = (source / f'{prefix}.3').read_bytes()
    text = words_raw.decode('ascii')
    assert all(w.isalpha() and 1 <= len(w) <= 7 for w in text.split())
    save(data_root / 'word_list.json', dict(source_sha256=digest(words_raw), text=text))
    save(data_root / 'level_titles.json', titles(exe, build))
    for index in range(20):
        raw = (source / f'{prefix}.s{index}').read_bytes()
        parsed = parse_level(raw)
        # Native 6bd6..6c37 caches locations column-major. Three source maps
        # contain an eighth marker in their final cell, but the drawing loop
        # consumes only seven locations. Preserve that raw attr, not a new block.
        markers = sorted(parsed['question_blocks'], key=lambda b: tuple(b['pos_px']))
        if len(markers) > 7:
            assert len(markers) == 8
            assert markers[-1]['pos_px'] == [(parsed['map_width_16'] * 2 - 1) * 8,
                                             (parsed['map_height_16'] * 2 - 1) * 8]
            manifest['map_edge_markers'].append(dict(level=index + 1, ignored_draw_location=markers[-1]))
        parsed['question_blocks'] = sorted(markers[:7], key=lambda b: b['index'])
        assert [b['index'] for b in parsed['question_blocks']] == list(range(7))
        save(data_root / f'levels/level_{index + 1:02}.json', convert_to_game_format(parsed, text.split(), index))
        save(data_root / f'rules/level_{index + 1:02}.json', dict(
            source_sha256=digest(raw), attributes=parsed['attributes'],
            background_tiles=parsed['original_background_tiles'],
            books=[[v // 16 for v in position] for position in parsed['books_px']],
            start=[v // 8 for v in parsed['player_start_px']],
            slots=[dict(slot=b['index'], grid=[v // 8 for v in b['pos_px']]) for b in parsed['question_blocks']]))
        manifest['sources'][f'{prefix}.s{index}'] = digest(raw)

    def sprite(name, raster):
        target = art_root / 'sprites' / f'{name}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        raster.save(target)
        manifest['sprites'].append(name)

    # Table geometry is verified identical; use each episode's actual STATIC.
    for index in range(16):
        values = struct.unpack_from('<11H', exe, build['ds'] + 0x724 + build['shift'] + index * 22)
        width, height, x, y, _, _, page = values[4:]
        sheet = sheets['CHARS.WR' if page == 2 else 'STATIC.WR']
        sprite(f'wr1_gruzzle_{index}', masked(sheet.crop((x, y, x + width, y + height)), (85, 255, 255)))
    for gender, name in enumerate(['boy', 'girl']):
        atlas = Image.new('RGBA', (26 * 24, 32))
        for frame in range(26):
            values = struct.unpack_from('<11H', exe, build['ds'] + 0x884 + build['shift'] + gender * 572 + frame * 22)
            width, height, x, y, _, _, page = values[4:]
            assert (width, height) == (24, 32)
            sheet = sheets['CHARS.WR' if page == 2 else 'STATIC.WR']
            atlas.paste(masked(sheet.crop((x, y, x + width, y + height)), (255, 85, 255)), (frame * 24, 0))
        sprite(f'wr1_{name}', atlas)
    sprite('spawn_doorway', sheets['STATIC.WR'].crop((16, 73, 48, 113)))
    sprite('wr1_rescue_down', masked(sheets['STATIC.WR'].crop((208, 72, 272, 136)), (255, 85, 255)))

    frontend = json.loads((ROOT / 'data/wr1/frontend.json').read_text(encoding='utf-8'))
    frontend['shared_template'] = 'data/wr1/frontend.json: common menu/instruction layouts; original offsets describe that template'
    frontend['episode_source_sha256'] = digest(exe)
    frontend['startup']['title_overlays'] = []
    ending = [f'WR{number}.10', f'WR{number}.11'] if number == 2 else ['WR3.10', 'FSTORY1.WR', 'FSTORY2.WR', 'FSTORY3.WR']
    frontend['ending']['screens'] = [dict(asset=name, x=0, y=0, key_advances=True) for name in ending]
    frontend['ending']['after'] = 'Reset episode progress and return to menu.'
    frontend['demo_order'] = [build['demos'][i % 6] for i in range(20)]
    # Metadata structure/common instructions are shared. Resource resolution
    # remaps WR1.* artwork names to the selected episode's archive.
    save(data_root / 'frontend.json', frontend)
    for level in build['demos']:
        raw = (source / f'{prefix}.d{level - 1}').read_bytes()
        decoded = decode_demo(raw)
        controls = decoded.pop('inputs')
        save(data_root / f'demos/level{level}.json', dict(
            episode=number, fps=70, level=level, difficulty=2, character='boy', events=[],
            total_frames=(len(controls) + 100) * 8, original_demo_inputs=controls,
            demo_provenance=decoded, content_demo=True))
    manifest['music_tracks'] = {'4': 5, '5': None, '6': 4} if number == 2 else {'4': 6, '5': 4, '6': 5}
    if number == 2:
        raw_music = (source / 'wr2.5').read_bytes()
        manifest['sources']['wr2.5'] = digest(raw_music)
        manifest['unavailable_music'] = {
            '5': 'Supplied wr2.5 lacks the CTMF header and is rejected by the original executable. This slot is silent.'}
    save(data_root / 'episode.json', manifest)
    print(f'{prefix}: 20 levels, {len(text.split())} word tokens, {len(build["demos"])} native input demos')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    for episode in BUILDS:
        import_episode(args.source, episode)
