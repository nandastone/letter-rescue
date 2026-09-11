#!/usr/bin/env python3
"""Measure exact screen positions of:
  - Doorway left edge (first brown-red frame pixel, color (170, 85, 0))
  - Doorway right edge
  - Player silhouette (use UNIQUE player colors: bright grey hair (85,85,85)
    which doesn't appear in the doorway)

Compare ref vs clone for each.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Doorway frame color (dark red / brown-red outline)
DOOR_FRAME = {(170, 0, 0), (170, 85, 0)}
# Dark green (0,170,0) is a dress color — let's use it to find player bbox IN the doorway
DRESS_DARK = (0, 170, 0)
# Also use the HAIR - grey (85,85,85) is the girl's hair; it only appears on the player
HAIR = (85, 85, 85)
# Dark red color 170,0,0 also appears on sprite shoes

def find_bbox(img, colors, box):
    x0, y0, x1, y1 = box
    pxs = img.load()
    bb = [x1, y1, -1, -1]
    cnt = 0
    if isinstance(colors, tuple):
        colors = {colors}
    for y in range(y0, y1):
        for x in range(x0, x1):
            if pxs[x,y] in colors:
                bb[0] = min(bb[0], x); bb[1] = min(bb[1], y)
                bb[2] = max(bb[2], x); bb[3] = max(bb[3], y)
                cnt += 1
    return bb, cnt

# Doorway is roughly in x=20..70, y=80..145
DOOR_BOX = (20, 60, 80, 145)
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    bb, cnt = find_bbox(img, DOOR_FRAME, DOOR_BOX)
    print(f"{name} door_frame: bbox={bb} count={cnt}")

# Player sprite: find DRESS DARK GREEN (0,170,0) — dress shadow
PLAY_BOX = (20, 90, 80, 140)
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    bb, cnt = find_bbox(img, DRESS_DARK, PLAY_BOX)
    print(f"{name} dress_dark (0,170,0): bbox={bb} count={cnt}")

# Player hair — grey
for name, img in [("REF", REF), ("CLONE", CLONE)]:
    bb, cnt = find_bbox(img, HAIR, PLAY_BOX)
    print(f"{name} hair (85,85,85): bbox={bb} count={cnt}")

# Save the hair bbox visually
from PIL import ImageDraw
for name, img in [("ref", REF), ("clone", CLONE)]:
    bb, _ = find_bbox(img, HAIR, PLAY_BOX)
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle([bb[0], bb[1], bb[2], bb[3]], outline=(255,255,0))
    # also hair bbox left-x in caption
    cropped = out.crop((20, 50, 80, 150)).resize((300, 500), Image.NEAREST)
    cropped.save(ROOT / f"testing/output/_hair_bbox_{name}.png")
    print(f"wrote _hair_bbox_{name}.png, hair left={bb[0]}, right={bb[2]}")
