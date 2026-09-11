#!/usr/bin/env python3
"""Scan clone frame 10 for any pixels matching idle sprite colors."""
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
sprite = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")

# look for GIRL skin tone (red-ish) AND cyan shirt
found = []
W, H = clone.size
for y in range(H):
    for x in range(W):
        r, g, b = clone.getpixel((x, y))
        # cyan shirt color: ~ (85, 255, 255)
        if abs(r-85) < 15 and abs(g-255) < 15 and abs(b-255) < 15:
            found.append((x, y, "cyan"))
print(f"Cyan pixels in clone frame 10: {len(found)}")
for p in found[:20]:
    print(" ", p)

# also check sprite colors
pxs = list(sprite.getdata())
cols = {}
for p in pxs:
    if p[3] > 0:
        cols[p[:3]] = cols.get(p[:3], 0) + 1
print("\nSprite colors (top 10):")
for c, n in sorted(cols.items(), key=lambda x: -x[1])[:10]:
    print(f"  {c}: {n}")
