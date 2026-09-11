#!/usr/bin/env python3
"""Find the bounding box of all differing pixels between ref frame 329 and
clone frame 10, broken down by region count."""
from PIL import Image
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = np.array(Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB"))
CLONE = np.array(Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB"))

diff = (REF != CLONE).any(axis=-1)
ys, xs = np.where(diff)
print(f"total diff pixels: {diff.sum()}")
print(f"bbox: x={xs.min()}..{xs.max()}  y={ys.min()}..{ys.max()}")

# Histogram rows
from collections import Counter
row_counts = Counter(ys.tolist())
col_counts = Counter(xs.tolist())
print("\ndiff rows (y with most diffs):")
for y, n in sorted(row_counts.items())[:40]:
    print(f"  y={y}: {n}")
print("\ndiff cols (x with most diffs):")
for x, n in sorted(col_counts.items())[:40]:
    print(f"  x={x}: {n}")

# Cluster: for each 4x4 block, count diffs
print("\nper-region heatmap (16x16 blocks):")
H, W = diff.shape
blocks = {}
for y, x in zip(ys, xs):
    by, bx = y // 16, x // 16
    blocks[(by, bx)] = blocks.get((by, bx), 0) + 1
# Grid print
max_by = max(b for b,_ in blocks)
max_bx = max(b for _,b in blocks)
min_by = min(b for b,_ in blocks)
min_bx = min(b for _,b in blocks)
print(f"blocks range: by={min_by}..{max_by} bx={min_bx}..{max_bx}")
for by in range(min_by, max_by+1):
    row = []
    for bx in range(min_bx, max_bx+1):
        n = blocks.get((by, bx), 0)
        row.append(f"{n:4d}" if n else "   .")
    yrange = f"y={by*16:3}-{by*16+15:3}"
    xrange = f"[{min_bx*16:3}-{max_bx*16+15:3}]"
    print(f"  {yrange}: " + " ".join(row))
print(f"  x blocks: " + " ".join(f"{bx*16:4}" for bx in range(min_bx, max_bx+1)))
