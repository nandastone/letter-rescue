#!/usr/bin/env python3
"""Dump pixels at the girl cluster (y=104..136, x=44..70) ref vs clone."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

COLORS = {
    (255, 85, 85): "p", (170, 0, 0): "d", (170, 85, 0): "B",
    (0, 0, 0): "#", (255, 255, 255): "W", (85, 85, 85): "g",
    (170, 170, 170): "G", (0, 170, 0): "v", (85, 255, 85): "V",
    (170, 85, 255): "U", (255, 255, 85): "Y", (255, 85, 255): "P",
    (0, 170, 170): "c", (85, 255, 255): "C", (0, 0, 170): "b",
    (85, 85, 255): "L", (170, 0, 170): "m",
}

def dump(img, label, xs, ys):
    print(f"{label}:")
    print("       " + "".join(f"{x%10:3}" for x in xs))
    for y in ys:
        row = f"y={y:3d}: "
        for x in xs:
            c = img.getpixel((x, y))
            ch = COLORS.get(c, "?")
            row += f" {ch:2}"
        print(row)

xs = range(44, 71)
ys = range(104, 138)
dump(REF, "REF", xs, ys)
print()
dump(CLONE, "CLONE", xs, ys)
