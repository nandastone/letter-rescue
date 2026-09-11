#!/usr/bin/env python3
"""Render each row of CHARS.WR as a labeled strip to see the full layout."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")
W, H = chars.size
print(f"CHARS.WR size: {W}x{H}")

# Build a visualization: scale 4x and draw y-labels
up = chars.resize((W*4, H*4), Image.NEAREST)
out = Image.new("RGB", (up.size[0] + 60, up.size[1]), (20,20,20))
out.paste(up, (60, 0))
d = ImageDraw.Draw(out)
for y in range(0, H, 32):
    d.text((4, y*4 + 4), f"y={y}", fill=(220,220,220))
out.save(ROOT / "testing/output/_chars_labeled.png")
print("Wrote _chars_labeled.png", out.size)
