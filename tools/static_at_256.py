#!/usr/bin/env python3
"""Check whether STATIC(256,72..118) is all pink (giving a vacuous wildcard
match) or genuinely contains the girl sprite."""
from PIL import Image
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
S = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGB")

# Dump color histogram for x=256..280, y=72..118
colors = Counter()
for y in range(72, 119):
    for x in range(256, 281):
        colors[S.getpixel((x, y))] += 1
print("STATIC(256..280, 72..118) color histogram:")
for c, n in colors.most_common(10):
    print(f"  {c}: {n}")

# Also just dump x=256 column y=72..118 to visualize
print("\nSTATIC x=256, y=72..118 column:")
for y in range(72, 119):
    px = S.getpixel((256, y))
    mark = " pink" if px == (255, 85, 255) else ""
    print(f"  y={y}: {px}{mark}")

# Render zoom of STATIC's top-left 320x100 so we can see what's there
big = S.crop((0, 0, 320, 160)).resize((320*4, 160*4), Image.NEAREST)
out_path = ROOT / "testing/output/_static_top.png"
big.save(out_path)
print(f"\nwrote {out_path} {big.size}")
