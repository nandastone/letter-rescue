#!/usr/bin/env python3
"""Render a 50x50 crop of the player area from both ref and clone at 24x zoom
with an x,y pixel grid so we can literally count where each sprite's leftmost
pixel is.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# 50x50 crop centered on player area
X0, Y0, W, H = 30, 90, 50, 50
Z = 24

def zoom_with_grid(img_crop, origin_x, origin_y):
    big = img_crop.resize((W*Z, H*Z), Image.NEAREST)
    d = ImageDraw.Draw(big)
    # vertical gridlines with x labels every pixel
    for xi in range(W):
        d.line([(xi*Z, 0), (xi*Z, H*Z)], fill=(255, 255, 0, 60), width=1)
    for yi in range(H):
        d.line([(0, yi*Z), (W*Z, yi*Z)], fill=(255, 255, 0, 60), width=1)
    # Every 5th col: stronger line with x number
    for xi in range(0, W, 2):
        d.line([(xi*Z, 0), (xi*Z, H*Z)], fill=(0, 255, 255), width=2)
        d.text((xi*Z+2, 2), str(origin_x + xi), fill=(0, 255, 255))
    for yi in range(0, H, 2):
        d.line([(0, yi*Z), (W*Z, yi*Z)], fill=(0, 255, 255), width=2)
        d.text((2, yi*Z+2), str(origin_y + yi), fill=(0, 255, 255))
    return big

ref_c = REF.crop((X0, Y0, X0+W, Y0+H))
clone_c = CLONE.crop((X0, Y0, X0+W, Y0+H))

pad = 10
th = 22
out = Image.new("RGB", (W*Z*2 + pad*3, H*Z + th + pad), (25,25,25))
d = ImageDraw.Draw(out)
out.paste(zoom_with_grid(ref_c, X0, Y0), (pad, th))
out.paste(zoom_with_grid(clone_c, X0, Y0), (pad*2 + W*Z, th))
d.text((pad, 4), "REF (y=90..140, x=30..80)", fill=(255,255,255))
d.text((pad*2 + W*Z, 4), "CLONE", fill=(255,255,255))
out.save(ROOT / "testing/output/_megazoom.png")
print(f"wrote _megazoom.png {out.size}")
