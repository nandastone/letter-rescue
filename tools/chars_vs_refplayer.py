#!/usr/bin/env python3
"""Compare every CHARS 24x32 cell to the ref-player crop at (36, 104) - (60, 136).
The ref has DOORWAY behind. For a correct score, compare only pixels where the
CHARS cell has a NON-PINK color, AND ignore ref pixels that match the doorway
pattern (pink-checker / red-outline).

Easier approach: score = count of (cell_non_pink == ref) MINUS penalty for
(cell_non_pink and they differ). And for the doorway pattern, we can tolerate
pink-checker (255,85,85) backgrounds that shouldn't exist in the sprite.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")

def is_pink(p): return abs(p[0]-255)<8 and abs(p[1]-85)<8 and abs(p[2]-255)<8

# Ref player bbox: (36, 104) - (60, 136)
REF_X, REF_Y = 36, 104
ref_crop = REF.crop((REF_X, REF_Y, REF_X+24, REF_Y+32))

# Colors in the doorway that bleed through sprite-transparent pixels:
# - pink checker (255,85,85) - light red
# - grey checker (85,85,85) or (170,170,170) as checker
# - red-brown doorway frame
# If a CHARS cell is pink (transparent) at a position AND ref shows doorway color,
# we can't tell. So best to compare only "cell is non-pink" positions.

best = []
for cy in range(0, CHARS.size[1]-32+1, 32):
    for cx in range(0, CHARS.size[0]-24+1, 24):
        cell = CHARS.crop((cx, cy, cx+24, cy+32))
        cpx = list(cell.getdata()); rpx = list(ref_crop.getdata())
        match = 0; total = 0
        for cp, rp in zip(cpx, rpx):
            if is_pink(cp): continue
            total += 1
            if cp == rp: match += 1
        if total == 0: continue
        best.append((match/total, match, total, cx, cy))

best.sort(reverse=True)
print(f"Comparing CHARS cells to ref-player at ({REF_X},{REF_Y})..(+24,+32)")
print(f"{'rank':>4} {'score':>6} {'m/of':>10} {'cx':>4} {'cy':>4}")
for i, (s, m, t, cx, cy) in enumerate(best[:15]):
    print(f"{i+1:>4} {s*100:>5.1f}% {m:>4}/{t:<4} {cx:>4} {cy:>4}")

# Render the top 5 side-by-side with ref for visual check
from PIL import ImageDraw
Z = 10
top = best[:10]
pad = 6
th = 22
out = Image.new("RGB", (24*Z*(len(top)+1) + pad*(len(top)+2), 32*Z + th + 20), (25,25,25))
d = ImageDraw.Draw(out)
d.text((pad, 4), "REF", fill=(255,255,255))
out.paste(ref_crop.resize((24*Z, 32*Z), Image.NEAREST), (pad, th))
for i, (s, m, t, cx, cy) in enumerate(top):
    cell = CHARS.crop((cx, cy, cx+24, cy+32))
    px = pad + (i+1)*(24*Z+pad)
    d.text((px, 4), f"({cx},{cy}) {s*100:.0f}%", fill=(255,255,255))
    out.paste(cell.resize((24*Z, 32*Z), Image.NEAREST), (px, th))
out.save(ROOT / "testing/output/_ref_vs_chars_top10.png")
print(f"\nwrote _ref_vs_chars_top10.png {out.size}")
