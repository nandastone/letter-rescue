"""Normalize extracted WR1 backdrops to the native VGA EGA register values."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    records = []
    for index in (3, 4):
        source = ROOT / f'assets/extracted/wr1_1_png/DROP{index}.WR.png'
        target = ROOT / f'assets/tiles/backdrop_{index}.png'
        raster = Image.open(source).convert('RGB')
        # The archive extractor expanded six-bit PCX components as 87/171;
        # the original VGA output (also used by the other game pages) is 85/170.
        raster.putdata([tuple({87: 85, 171: 170}.get(c, c) for c in pixel) for pixel in raster.getdata()])
        raster.save(target)
        records.append({'index': index, 'source': source.relative_to(ROOT).as_posix(),
                        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'output': target.relative_to(ROOT).as_posix()})
    (ROOT / 'data/wr1/backdrops.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
