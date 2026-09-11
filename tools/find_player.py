#!/usr/bin/env python3
"""Find where the player body is rendered in the clone frame by searching for cyan clusters."""
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
# look for a cyan patch (player shirt) that is NOT part of the sky/HUD
# sky is at y < ~24 (HUD), doorway is around (40-80, 100-140)
coords = []
for y in range(80, 160):
    for x in range(0, 120):
        r, g, b = clone.getpixel((x, y))
        if abs(r-85) < 15 and abs(g-255) < 15 and abs(b-255) < 15:
            coords.append((x, y))
if coords:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    print(f"Cyan pixels in playfield-left: {len(coords)}")
    print(f"  x range: {min(xs)} - {max(xs)}")
    print(f"  y range: {min(ys)} - {max(ys)}")

# Also do red skin tone (255, 85, 85)
coords2 = []
for y in range(80, 160):
    for x in range(0, 120):
        r, g, b = clone.getpixel((x, y))
        if abs(r-255) < 15 and abs(g-85) < 15 and abs(b-85) < 15:
            coords2.append((x, y))
if coords2:
    xs = [c[0] for c in coords2]
    ys = [c[1] for c in coords2]
    print(f"\nRed pixels in playfield-left: {len(coords2)}")
    print(f"  x range: {min(xs)} - {max(xs)}")
    print(f"  y range: {min(ys)} - {max(ys)}")

# black (0,0,0) clustered
coords3 = []
for y in range(80, 160):
    for x in range(0, 120):
        r, g, b = clone.getpixel((x, y))
        if r == 0 and g == 0 and b == 0:
            coords3.append((x, y))
if coords3:
    xs = [c[0] for c in coords3]
    print(f"\nBlack pixels: {len(coords3)}  x range: {min(xs)}-{max(xs)}")
