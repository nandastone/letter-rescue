#!/usr/bin/env python3
"""Dump full ref frame 329 structure around the doorway. We want to know:
- Is the bg pattern uniform inside the doorway?
- Where does the doorway frame end and where does the girl sprite begin?
Scan strips at fixed x positions and fixed y positions."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# A vertical strip at x=43 (girl's left edge) from y=40..150: shows doorway+girl+ground
print(f"{'y':>3} {'ref(43)':<16} {'clone(43)':<16}  {'ref(50)':<16}")
for y in range(40, 145):
    rpx = REF.getpixel((43, y))
    cpx = CLONE.getpixel((43, y))
    rpx50 = REF.getpixel((50, y))
    diff = "!=" if rpx != cpx else "=="
    print(f"{y:>3} {str(rpx):<16} {str(cpx):<16} {diff} {str(rpx50):<16}")

# Render a LARGER zoom of the doorway region in ref and clone side-by-side,
# with y ruler. Output < 1500 px wide.
DX, DY, DW, DH = 36, 40, 40, 110   # whole doorway column incl. above + below
Z = 8
label_h = 16
ruler_w = 30
# 2 columns of DW*Z=320 + ruler + pad
W = ruler_w + 2 * (DW * Z) + 12
H = DH * Z + label_h
out = Image.new("RGB", (W, H), (30, 30, 30))
d = ImageDraw.Draw(out)
# Ruler
for y in range(0, DH, 8):
    d.text((2, label_h + y * Z), str(DY + y), fill=(150, 150, 150))
# Ref crop
ref_crop = REF.crop((DX, DY, DX+DW, DY+DH)).resize((DW*Z, DH*Z), Image.NEAREST)
out.paste(ref_crop, (ruler_w, label_h))
d.text((ruler_w, 0), f"REF ({DX},{DY})-({DX+DW},{DY+DH})", fill=(255,255,255))
# Clone crop
x2 = ruler_w + DW * Z + 8
clone_crop = CLONE.crop((DX, DY, DX+DW, DY+DH)).resize((DW*Z, DH*Z), Image.NEAREST)
out.paste(clone_crop, (x2, label_h))
d.text((x2, 0), "CLONE", fill=(255,255,255))

out_path = ROOT / "testing/output/_doorway_anatomy.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
