#!/usr/bin/env python3
"""Dump actual pixels in upper diff cluster to understand what entity is there."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

print("REF at y=60..72, x=44..64:")
print("     " + "".join(f"{x%10:3}" for x in range(44, 64)))
for y in range(58, 74):
    row = f"y={y:2d}: "
    for x in range(44, 64):
        r, g, b = REF.getpixel((x, y))
        # Char-encode color
        if (r, g, b) == (255, 85, 85): ch = "p"   # salmon pink (doorway)
        elif (r, g, b) == (170, 0, 0): ch = "d"    # dark red
        elif (r, g, b) == (170, 85, 0): ch = "B"   # brown (wall/rock)
        elif (r, g, b) == (0, 0, 0): ch = "#"      # black outline
        elif (r, g, b) == (255, 255, 255): ch = "W"  # white
        elif (r, g, b) == (85, 85, 85): ch = "g"   # dark grey
        elif (r, g, b) == (170, 170, 170): ch = "G"  # light grey
        elif (r, g, b) == (0, 170, 0): ch = "v"    # dark green
        elif (r, g, b) == (85, 255, 85): ch = "V"  # bright green
        elif (r, g, b) == (170, 85, 255): ch = "U"  # purple
        elif (r, g, b) == (255, 255, 85): ch = "Y"  # yellow
        elif (r, g, b) == (255, 85, 255): ch = "P"  # pink
        else: ch = "?"
        row += f" {ch:2}"
    print(row)

print("\nCLONE same region:")
print("     " + "".join(f"{x%10:3}" for x in range(44, 64)))
for y in range(58, 74):
    row = f"y={y:2d}: "
    for x in range(44, 64):
        r, g, b = CLONE.getpixel((x, y))
        if (r, g, b) == (255, 85, 85): ch = "p"
        elif (r, g, b) == (170, 0, 0): ch = "d"
        elif (r, g, b) == (170, 85, 0): ch = "B"
        elif (r, g, b) == (0, 0, 0): ch = "#"
        elif (r, g, b) == (255, 255, 255): ch = "W"
        elif (r, g, b) == (85, 85, 85): ch = "g"
        elif (r, g, b) == (170, 170, 170): ch = "G"
        elif (r, g, b) == (0, 170, 0): ch = "v"
        elif (r, g, b) == (85, 255, 85): ch = "V"
        elif (r, g, b) == (170, 85, 255): ch = "U"
        elif (r, g, b) == (255, 255, 85): ch = "Y"
        elif (r, g, b) == (255, 85, 255): ch = "P"
        else: ch = "?"
        row += f" {ch:2}"
    print(row)
