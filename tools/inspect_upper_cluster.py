#!/usr/bin/env python3
"""Zoom ref and clone over y=55..80, x=40..70 to see what entity is there."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Also dump raw pixel comparison
for y in range(60, 75):
    row = []
    for x in range(45, 70):
        r = REF.getpixel((x, y))
        c = CLONE.getpixel((x, y))
        mark = "!" if r != c else "."
        row.append(mark)
    print(f"y={y}: " + "".join(row))

# Render zoom side-by-side
BX, BY, BW, BH = 40, 52, 30, 30
Z = 14
cw, ch = BW*Z, BH*Z
pad = 4
W = 2 * (cw + pad) + pad
H = ch + 20 + pad
out = Image.new("RGB", (W, H), (30, 30, 30))
d = ImageDraw.Draw(out)
ref_c = REF.crop((BX, BY, BX+BW, BY+BH)).resize((cw, ch), Image.NEAREST)
clo_c = CLONE.crop((BX, BY, BX+BW, BY+BH)).resize((cw, ch), Image.NEAREST)
out.paste(ref_c, (pad, 16))
out.paste(clo_c, (pad*2 + cw, 16))
d.text((pad, 0), f"REF ({BX},{BY})-({BX+BW},{BY+BH})", fill=(255,255,255))
d.text((pad*2 + cw, 0), "CLONE", fill=(255,255,255))
out_path = ROOT / "testing/output/_upper_cluster.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
