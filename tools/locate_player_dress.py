#!/usr/bin/env python3
"""Find the player by searching for the unique green-dress color (0,170,0)
in the doorway region. The dress is a stable identifier because the doorway
bg, doorway frame, and grass don't use that color.

Then compare dress centroid between ref and clone.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

DRESS = (0, 170, 0)       # EGA dark green
DRESS_LIGHT = (85, 255, 85)  # dress highlight/hem
HAIR = (85, 85, 85)       # grey hair
BLACK = (0, 0, 0)         # outline

def find_dress_bbox(img, box):
    x0, y0, x1, y1 = box
    px = img.load()
    bbox = [x1, y1, -1, -1]
    count = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y] == DRESS:
                bbox[0] = min(bbox[0], x); bbox[1] = min(bbox[1], y)
                bbox[2] = max(bbox[2], x); bbox[3] = max(bbox[3], y)
                count += 1
    return bbox, count

def find_color_pixels(img, box, color):
    x0, y0, x1, y1 = box
    px = img.load()
    out = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y] == color:
                out.append((x, y))
    return out

# Search the whole left half of frame below HUD
BOX = (0, 40, 160, 200)

for name, img in [("REF", REF), ("CLONE", CLONE)]:
    bb, cnt = find_dress_bbox(img, BOX)
    print(f"{name} dark-green dress: bbox={bb}, count={cnt}")
    if cnt > 0:
        print(f"  bottom-middle of dress: x={ (bb[0]+bb[2])//2 }, y_bottom={bb[3]}")

# Compare pixel-exact positions of black outline (the "y=0 line" of the player sprite)
# The black is at (0,0,0); the top of the player sprite (hair top) is a strong
# black cluster. Find topmost black pixel in the player region.
def topmost_black(img, box):
    x0, y0, x1, y1 = box
    px = img.load()
    for y in range(y0, y1):
        row = [x for x in range(x0, x1) if px[x, y] == BLACK]
        if row:
            return y, row
    return None, []

# Player region (exclude stones/bg above)
PLAYER_BOX = (30, 95, 80, 140)
print()
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    y, xs = topmost_black(img, PLAYER_BOX)
    print(f"{name} topmost black in player box: y={y}, xs={xs}")

# Direct: find all black pixels in player region, compute bbox
print()
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    bp = find_color_pixels(img, PLAYER_BOX, BLACK)
    if bp:
        xs = [p[0] for p in bp]; ys = [p[1] for p in bp]
        print(f"{name} player-region black: count={len(bp)}, bbox=({min(xs)},{min(ys)})..({max(xs)},{max(ys)})")

# Skin (ref) vs clone
print()
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    # Red skin
    sk = find_color_pixels(img, PLAYER_BOX, (255, 85, 85))
    if sk:
        xs = [p[0] for p in sk]; ys = [p[1] for p in sk]
        print(f"{name} skin (255,85,85): count={len(sk)}, bbox=({min(xs)},{min(ys)})..({max(xs)},{max(ys)})")
