#!/usr/bin/env python3
"""Diagnose whether the player diff is palette, position, or pose.

Strategy:
  1. Find the bounding box of all differing pixels.
  2. Try shifting the clone +/- N pixels in x/y and recompute the diff count.
     If any shift drops it near zero, it's a position bug.
  3. Print the set of distinct (ref_color -> clone_color) mappings over the
     diff pixels. If it's a handful of fixed mappings, it's a palette bug.
  4. Specifically list hair-area, skin-area and dress-area pixels to see
     if one palette index is consistently remapped.
"""
from PIL import Image
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
W, H = REF.size

def diff_pixels(ref, clone, off=(0, 0)):
    ox, oy = off
    r = ref.load(); c = clone.load()
    count = 0
    bb = [W, H, -1, -1]
    for y in range(H):
        for x in range(W):
            cx, cy = x + ox, y + oy
            if not (0 <= cx < W and 0 <= cy < H):
                continue
            if r[x, y] != c[cx, cy]:
                count += 1
                bb[0] = min(bb[0], x); bb[1] = min(bb[1], y)
                bb[2] = max(bb[2], x); bb[3] = max(bb[3], y)
    return count, bb

print("=== position shift test ===")
for dx in range(-2, 3):
    for dy in range(-2, 3):
        n, _ = diff_pixels(REF, CLONE, (dx, dy))
        mark = "  <-- current" if (dx, dy) == (0, 0) else ""
        print(f"  shift ({dx:+d},{dy:+d}): {n} diff pixels{mark}")

print()
print("=== diff pixel bbox at (0,0) ===")
n, bb = diff_pixels(REF, CLONE, (0, 0))
print(f"  bbox: ({bb[0]}, {bb[1]}) .. ({bb[2]}, {bb[3]})  size {bb[2]-bb[0]+1}x{bb[3]-bb[1]+1}")
print(f"  total diff pixels: {n}")

print()
print("=== color mapping at differing pixels ===")
r = REF.load(); c = CLONE.load()
mapping = Counter()
for y in range(bb[1], bb[3]+1):
    for x in range(bb[0], bb[2]+1):
        if r[x,y] != c[x,y]:
            mapping[(r[x,y], c[x,y])] += 1
print(f"  distinct (ref_rgb -> clone_rgb) mappings: {len(mapping)}")
for (ref_rgb, clone_rgb), cnt in mapping.most_common(20):
    print(f"    ref {ref_rgb} -> clone {clone_rgb}  x{cnt}")

print()
print("=== ref unique colors in bbox ===")
ref_colors = Counter()
for y in range(bb[1], bb[3]+1):
    for x in range(bb[0], bb[2]+1):
        ref_colors[r[x,y]] += 1
for col, cnt in ref_colors.most_common(16):
    print(f"    ref {col}: {cnt}")

print()
print("=== clone unique colors in bbox ===")
clone_colors = Counter()
for y in range(bb[1], bb[3]+1):
    for x in range(bb[0], bb[2]+1):
        clone_colors[c[x,y]] += 1
for col, cnt in clone_colors.most_common(16):
    print(f"    clone {col}: {cnt}")
