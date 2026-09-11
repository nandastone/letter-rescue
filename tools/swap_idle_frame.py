#!/usr/bin/env python3
"""Replace player_idle.png with CHARS (168, 96) — girl with arm extended.

Pink (255, 85, 255) becomes alpha=0 for sprite transparency.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")

X, Y = 0, 64
W, H = 24, 32
crop = chars.crop((X, Y, X + W, Y + H)).convert("RGBA")

# Make pink transparent
out = []
for r, g, b, a in crop.getdata():
    if abs(r - 255) < 8 and abs(g - 85) < 8 and abs(b - 255) < 8:
        out.append((0, 0, 0, 0))
    else:
        out.append((r, g, b, 255))
crop.putdata(out)
crop.save(ROOT / "assets/sprites/player_idle.png")
print(f"Wrote assets/sprites/player_idle.png from CHARS ({X}, {Y})")
