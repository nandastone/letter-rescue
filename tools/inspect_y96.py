#!/usr/bin/env python3
"""Inspect every girl frame at y=64 and y=96 at 6x upscale."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")

cols = 13
for row_y in (64, 96):
    strip = Image.new("RGB", (24 * cols + 20, 32 + 20), (20,20,20))
    d = ImageDraw.Draw(strip)
    for i in range(cols):
        x = i * 24
        tile = chars.crop((x, row_y, x + 24, row_y + 32))
        strip.paste(tile, (2 + i * 24, 16))
        d.text((2 + i * 24, 2), f"{x}", fill=(220,220,220))
    up = strip.resize((strip.size[0]*6, strip.size[1]*6), Image.NEAREST)
    up.save(ROOT / f"testing/output/_chars_y{row_y}_6x.png")
    print(f"Wrote _chars_y{row_y}_6x.png")
