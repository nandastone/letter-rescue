"""Extract gruzzle/slime sprites from WR1's executable sprite records."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image
from json_evidence import read as read_evidence
from native_sprite_image import decode as decode_native_sprite

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_dir', type=Path)
    args = parser.parse_args()
    exe = (args.game_dir / 'WR1.EXE').read_bytes()
    digest = hashlib.sha256(exe).hexdigest()
    if digest != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        parser.error('Unsupported WR1 executable')
    sheets = {2: Image.open(ROOT/'assets/extracted/wr1_1_png/CHARS.WR.png').convert('RGBA'),
              5: Image.open(ROOT/'assets/extracted/wr1_1_png/STATIC.WR.png').convert('RGBA')}
    slime = Image.open(ROOT/'assets/extracted/wr1_1_png/SLIME.WR.png').convert('RGBA')
    benny2 = Image.open(ROOT/'assets/extracted/wr1_1_png/BENNY2.WR.png').convert('RGBA')
    # This archive PNG expanded its six-bit palette with87/171. Gameplay uses
    # the same EGA registers as the other pages, including brown at index6.
    benny2.putdata([tuple({87:85,171:170}.get(c,c) for c in p) for p in benny2.getdata()])
    records = []
    native_slime = read_evidence(ROOT/'testing/fixtures/wr1_slime_assets.json')
    assert native_slime['exe_sha256'] == digest
    for kind, offset, count in [('gruzzle', 0x724, 16), ('slime', 0x65e, 9), ('drip', 0xcfc, 3)]:
        for index in range(count):
            values = struct.unpack_from('<11H', exe, 0x24f50 + offset + index*22)
            width, height, x1, y1, x2, y2, page = values[4:]
            # One x2 is inconsistent (type2/frame3 says131 rather than111).
            # Preserve the declared width; this variant still needs pixel checks.
            # Video page2 is reused: drips are built while BENNY2 is loaded.
            source = benny2 if kind == 'drip' else slime if kind == 'slime' else sheets[page]
            source_y = y1 - 80 if kind == 'slime' else y1
            sprite = source.crop((x1, source_y, x1+width, source_y+height))
            pixels = sprite.load()
            for y in range(height):
                for x in range(width):
                    if pixels[x,y][:3] == ((85,85,255) if kind in ('drip','slime') else (85,255,255)):
                        pixels[x,y] = (0,0,0,0)
            name = f'wr1_{kind}_{index}.png'
            if kind == 'slime':
                # Preserve the original generated AND mask too: frame 8 has
                # one opaque black pixel absent from a chroma-key extraction.
                sprite = decode_native_sprite(native_slime['images'][f'body_{index}'], native_slime['images'][f'mask_{index}'])
            sprite.save(ROOT/'assets/sprites'/name)
            records.append({'kind':kind,'index':index,'table_offset':offset+index*22,
                            'record':values,'file':name})
    (ROOT/'data/wr1/gruzzle_frames.json').write_text(json.dumps(
        {'exe_sha256':digest,'frames':records},indent=2)+'\n')
    rescue = []
    # These images are constructed explicitly at EXE 91bb..9258, outside
    # the normal sprite-record table. Coordinates are inclusive in DOS.
    for name, page, bounds in [('down',5,(208,72,272,136)),
                               ('girl',2,(72,128,144,200)),
                               ('boy',2,(0,128,73,200))]:
        sprite = sheets[page].crop(bounds)
        # The planar blit copies whole eight-pixel bytes. Boy's inclusive
        # source rectangle is73 wide, but its displayed image is72 (native verified).
        render_width = sprite.width // 8 * 8
        sprite = sprite.crop((0,0,render_width,sprite.height))
        sprite.putdata([(0,0,0,0) if p[:3] == (255,85,255) else
                        (170,85,0,p[3]) if p[:3] == (170,170,0) else p
                        for p in sprite.getdata()])
        filename = f'wr1_rescue_{name}.png'
        sprite.save(ROOT/'assets/sprites'/filename)
        rescue.append({'file':filename,'page':page,'bounds_exclusive':bounds,'render_width':render_width})
    (ROOT/'data/wr1/rescue_frames.json').write_text(json.dumps(
        {'exe_sha256':digest,'frames':rescue},indent=2)+'\n')
    benny = []
    for index in range(12):
        offset = 0x556 + index * 22
        values = struct.unpack_from('<11H', exe, 0x24f50 + offset)
        width, height, x1, y1, x2, y2, page = values[4:]
        sheet = 'BENNY1.WR.png' if index < 9 else 'BENNY2.WR.png'
        source = benny2 if index >= 9 else Image.open(ROOT/'assets/extracted/wr1_1_png'/sheet).convert('RGBA')
        sprite = source.crop((x1, y1, x1 + width, y1 + height))
        sprite.putdata([(0,0,0,0) if p[:3] == (255,85,255) else
                        (170,85,0,p[3]) if p[:3] == (170,170,0) else p for p in sprite.getdata()])
        filename = f'wr1_benny_{index}.png'
        sprite.save(ROOT/'assets/sprites'/filename)
        benny.append({'file':filename,'sheet':sheet,'table_offset':offset,'record':values})
    (ROOT/'data/wr1/benny_frames.json').write_text(json.dumps(
        {'exe_sha256':digest,'frames':benny},indent=2)+'\n')
    # 9b8a..9ba2 builds the mask from FONT.WR's top-left colour.
    letters = Image.open(ROOT/'assets/extracted/wr1_1_png/FONT.WR.png').convert('RGBA')
    key = letters.getpixel((0,0))[:3]
    letters.putdata([(0,0,0,0) if p[:3] == key else p for p in letters.getdata()])
    letters.save(ROOT/'assets/sprites/wr1_letters.png')


if __name__ == '__main__':
    main()
