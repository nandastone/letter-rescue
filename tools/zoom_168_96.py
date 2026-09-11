#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")
# Some spots to see at 16x
spots = [(168, 96), (0, 64), (240, 96), (144, 96)]
for x, y in spots:
    # Take a wider window to see if a sparkle is adjacent
    crop = chars.crop((x - 8, y, x + 24 + 8, y + 32))
    up = crop.resize((crop.size[0]*16, crop.size[1]*16), Image.NEAREST)
    up.save(ROOT / f"testing/output/_chars_{x}_{y}_16x_wide.png")
    print(f"Wrote _chars_{x}_{y}_16x_wide.png")
