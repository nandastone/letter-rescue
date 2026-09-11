#!/usr/bin/env python3
"""Find the exact (x, y) top-left of the player 24x32 in BOTH ref and clone,
by sliding the CHARS (0, 64) sprite over each and finding the best-match
position (ignoring pink pixels in the sprite).

If ref_pos != clone_pos, the player is drawn at different coords — a position
bug, not an animation bug.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")

IDLE = CHARS.crop((0, 64, 24, 64+32))

def is_pink(p): return abs(p[0]-255)<8 and abs(p[1]-85)<8 and abs(p[2]-255)<8

def locate(img, sprite, search_box):
    x0, y0, x1, y1 = search_box
    spx = list(sprite.getdata())
    best = (-1, 0, 0, 0, 0)
    for y in range(y0, y1-32+1):
        for x in range(x0, x1-24+1):
            crop = img.crop((x, y, x+24, y+32))
            rpx = list(crop.getdata())
            matched = 0; considered = 0
            for cp, rp in zip(spx, rpx):
                if is_pink(cp): continue
                considered += 1
                if cp == rp: matched += 1
            score = matched / considered if considered else 0
            if score > best[0]:
                best = (score, matched, considered, x, y)
    return best

# search only the doorway region (x=20..80, y=80..140)
BOX = (20, 80, 90, 140)

rs, rm, rc, rx, ry = locate(REF, IDLE, BOX)
cs, cm, cc, cx, cy = locate(CLONE, IDLE, BOX)

print(f"REF best match:   top-left=({rx}, {ry})  {rs*100:.1f}%  {rm}/{rc}")
print(f"CLONE best match: top-left=({cx}, {cy})  {cs*100:.1f}%  {cm}/{cc}")
print(f"delta: ({cx-rx:+d}, {cy-ry:+d})")

# Also: is ref pose actually (0, 64)? Try every CHARS cell at ref_best_pos
print("\nAll CHARS cells scored at REF best location:")
if rx >= 0:
    ref_crop = REF.crop((rx, ry, rx+24, ry+32))
    rpx = list(ref_crop.getdata())
    results = []
    for cy_ in range(0, CHARS.size[1]-32+1, 32):
        for cx_ in range(0, CHARS.size[0]-24+1, 24):
            cell = CHARS.crop((cx_, cy_, cx_+24, cy_+32))
            cpx = list(cell.getdata())
            if all(is_pink(p) for p in cpx): continue
            m, c = 0, 0
            for cp, rp in zip(cpx, rpx):
                if is_pink(cp): continue
                c += 1
                if cp == rp: m += 1
            if c == 0: continue
            results.append((m/c, m, c, cx_, cy_))
    results.sort(reverse=True)
    for i, (s, m, c, x, y) in enumerate(results[:10]):
        print(f"  {i+1}. ({x:3},{y:3}) {s*100:5.1f}%  {m}/{c}")
