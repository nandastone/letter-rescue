#!/usr/bin/env python3
"""Zoom individual candidate frames."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")

spots = [(288, 96), (288, 64), (264, 96), (240, 96), (168, 96), (0, 64), (264, 64)]
strip = Image.new("RGB", (24 * len(spots) + 20, 32 + 20), (20,20,20))
d = ImageDraw.Draw(strip)
for i, (x, y) in enumerate(spots):
    tile = chars.crop((x, y, x + 24, y + 32))
    strip.paste(tile, (2 + i * (24 + 1), 16))
    d.text((2 + i * (24 + 1), 2), f"{x},{y}", fill=(220,220,220))
up = strip.resize((strip.size[0]*10, strip.size[1]*10), Image.NEAREST)
up.save(ROOT / "testing/output/_chars_wand_candidates_10x.png")
print("Wrote", up.size)

# Also zoom on the ref girl crop at 10x for reference
sent = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
refcrop = sent.crop((40, 96, 80, 144))
refcrop.resize((refcrop.size[0]*10, refcrop.size[1]*10), Image.NEAREST).save(
    ROOT / "testing/output/_ref_girl_10x.png")
print("Wrote _ref_girl_10x.png")
