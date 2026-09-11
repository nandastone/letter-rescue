#!/usr/bin/env python3
"""For each 24x32 cell in CHARS.WR, measure how many of its non-pink pixels
match the ref frame 329 at the expected player position.

The player's top-left in ref should be around (40, 104). Sweep +-2 around it.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

def is_pink(p): return abs(p[0]-255)<8 and abs(p[1]-85)<8 and abs(p[2]-255)<8

def score_cell(cell, ref, px_center, sweep=3):
    cpx = list(cell.getdata())
    best = (-1, 0, 0, 0)
    for dy in range(-sweep, sweep+1):
        for dx in range(-sweep, sweep+1):
            x0 = px_center[0] + dx; y0 = px_center[1] + dy
            ref_crop = ref.crop((x0, y0, x0+24, y0+32))
            rpx = list(ref_crop.getdata())
            considered = 0; matched = 0
            for cp, rp in zip(cpx, rpx):
                if is_pink(cp): continue
                considered += 1
                if cp == rp: matched += 1
            if considered == 0: continue
            score = matched / considered
            if score > best[0]:
                best = (score, matched, considered, (dx, dy))
    return best

# Also measure current idle.png
idle = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGB")

ref_exp = (40, 104)   # expected top-left; game.gd sets start.x at 52 - 12 = 40
print(f"testing ref anchor sweep around ({ref_exp[0]}, {ref_exp[1]})\n")

# score all CHARS cells
results = []
for y in range(0, CHARS.size[1]-32+1, 32):
    for x in range(0, CHARS.size[0]-24+1, 24):
        cell = CHARS.crop((x, y, x+24, y+32))
        # skip all-pink
        if all(is_pink(p) for p in cell.getdata()): continue
        s, m, c, off = score_cell(cell, REF, ref_exp)
        results.append((s, m, c, x, y, off))

# Current idle.png against ref
s, m, c, off = score_cell(idle, REF, ref_exp)
print(f"CURRENT idle.png vs REF: {s*100:5.1f}%  {m}/{c}  best offset {off}\n")

# Current idle.png against clone (sanity — should be ~100%)
s2, m2, c2, off2 = score_cell(idle, CLONE, ref_exp)
print(f"CURRENT idle.png vs CLONE: {s2*100:5.1f}%  {m2}/{c2}  best offset {off2}\n")

results.sort(reverse=True)
print(f"{'rank':>4} {'score':>6} {'match/of':>11}  {'cx':>4} {'cy':>4}  offset")
for i, (s, m, c, x, y, off) in enumerate(results[:15]):
    print(f"{i+1:>4} {s*100:>5.1f}% {m:>5}/{c:<5}  {x:>4} {y:>4}  {off}")
