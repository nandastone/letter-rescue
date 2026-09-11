"""Read the BIOS font selected by a paused WR1 tracing instance (port 55445).

The game uses BIOS font 3 (8x8), not FONT.WR, for HUD text. DOSBox Pure maps
physical memory >= 640 KiB at exposed address 0x200000. No memory is written.
See testing/wr1_hud_books_research.md and wr1_runtime_research.md.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from wr1_trace import Reader

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--bios-source', type=Path,
        help='Extend the already measured first 128 glyphs from matching DOSBox int10_memory.cpp')
    args = parser.parse_args()
    exe = args.exe.read_bytes()
    digest = hashlib.sha256(exe).hexdigest()
    if digest != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        parser.error('Unsupported WR1 executable')
    if args.bios_source:
        target = ROOT/'data/wr1/bios_font.json'
        result = json.loads(target.read_text())
        source = args.bios_source.read_text()
        body = source.split('Bit8u int10_font_08[256 * 8] = {',1)[1].split('};',1)[0]
        font = bytes(int(value,16) for value in re.findall(r'0x([0-9A-Fa-f]{2})\b',body))
        assert len(font) == 2048
        assert list(font[:1024]) == [byte for row in result['rows'][:128] for byte in row]
        result['measured_prefix_sha256'] = hashlib.sha256(font[:1024]).hexdigest()
        result['bios_source_sha256'] = hashlib.sha256(args.bios_source.read_bytes()).hexdigest()
        result['font_sha256'] = hashlib.sha256(font).hexdigest()
        result['rows'] = [list(font[i:i+8]) for i in range(0,2048,8)]
        target.write_text(json.dumps(result),encoding='utf-8')
        print('Extracted 256 glyphs; measured first 128 unchanged:',result['font_sha256'])
        return
    reader = Reader(55445)
    try:
        reader.require_paused()
        base = reader.find_ds(exe)
        offset, segment = struct.unpack('<HH', reader.read(base + 0x43b0, 4))
        physical = segment * 16 + offset
        if not 0xa0000 <= physical <= 0x100000 - 1024:
            raise RuntimeError('Selected font is outside the mapped BIOS region')
        font = reader.read(0x200000 + physical - 0xa0000, 1024)
        result = {'exe_sha256': digest, 'font_sha256': hashlib.sha256(font).hexdigest(),
                  'physical_address': physical, 'width': 8, 'height': 8,
                  'rows': [list(font[i:i+8]) for i in range(0, 1024, 8)]}
        (ROOT/'data/wr1/bios_font.json').write_text(json.dumps(result), encoding='utf-8')
        print('Extracted selected 128-glyph BIOS font:', result['font_sha256'])
    finally:
        reader.socket.close()


if __name__ == '__main__':
    main()
