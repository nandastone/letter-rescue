#!/usr/bin/env python3
"""Find the X shift needed to align clone's player region to ref.

Compare ref vs clone at every pixel in the doorway region, with clone shifted
by dx. Report diff count per dx. The minimum is the needed shift.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Player region: confined to 24x32 doorway-interior area. Use (36, 104)-(68, 138).
# But to measure shift, we need to shift clone relative to ref and see diffs IN this region.
# Trick: we want pixels where ref != clone_shifted. But the BG around the sprite is identical
# in both (doorway is at same world position), so shifting the clone shifts everything.
# Thus shifting shows us where the PLAYER-only diff is minimum.

BOX = (30, 95, 75, 140)

def diff_count_shifted(ref, clone, dx, dy, box):
    n = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            cx, cy = x + dx, y + dy
            if not (0 <= cx < clone.size[0] and 0 <= cy < clone.size[1]):
                continue
            if ref.getpixel((x,y)) != clone.getpixel((cx, cy)):
                n += 1
    return n

print(f"Testing x shifts (clone shifted by dx) in player box {BOX}:")
for dx in range(-8, 9):
    n = diff_count_shifted(REF, CLONE, dx, 0, BOX)
    mark = " <-- current" if dx == 0 else ""
    print(f"  dx={dx:+d}: {n} diffs{mark}")
