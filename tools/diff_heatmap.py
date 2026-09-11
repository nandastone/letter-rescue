#!/usr/bin/env python3
"""Make a row-by-row diff count to see if diff concentrates on player, doorway, or elsewhere.
Also dumps the ref+clone+diff tall-crop at 12x for direct eyeballing.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
W, H = REF.size

r = REF.load(); c = CLONE.load()
per_row = [0]*H
for y in range(H):
    for x in range(W):
        if r[x,y] != c[x,y]:
            per_row[y] += 1
per_col = [0]*W
for x in range(W):
    for y in range(H):
        if r[x,y] != c[x,y]:
            per_col[x] += 1

print("rows with any diff:")
for y in range(H):
    if per_row[y] > 0:
        print(f"  y={y:3}: {per_row[y]:4} diff px   {'#'*per_row[y]}")
print()
print("cols with any diff:")
for x in range(W):
    if per_col[x] > 0:
        print(f"  x={x:3}: {per_col[x]:4} diff px   {'#'*per_col[x]}")
print()

# Tall crop (player + doorway region) at 12x
CX, CY, CW, CH = 30, 56, 44, 84
Z = 12
def zoom(img): return img.resize((img.size[0]*Z, img.size[1]*Z), Image.NEAREST)
ref_c = REF.crop((CX, CY, CX+CW, CY+CH))
clone_c = CLONE.crop((CX, CY, CX+CW, CY+CH))
diff = Image.new("RGB", (CW, CH), (0,0,0))
dpx = diff.load(); rpx = ref_c.load(); cpx = clone_c.load()
for y in range(CH):
    for x in range(CW):
        if rpx[x,y] != cpx[x,y]:
            dpx[x,y] = (255, 0, 0)
        else:
            dpx[x,y] = (40, 40, 40)

pad = 16
out = Image.new("RGB", (CW*Z*3 + pad*4, CH*Z + 40), (25,25,25))
d = ImageDraw.Draw(out)
out.paste(zoom(ref_c), (pad, 30))
out.paste(zoom(clone_c), (pad*2 + CW*Z, 30))
out.paste(zoom(diff), (pad*3 + CW*Z*2, 30))
d.text((pad, 8), "REF (crop y=56..140)", fill=(255,255,255))
d.text((pad*2 + CW*Z, 8), "CLONE (crop y=56..140)", fill=(255,255,255))
d.text((pad*3 + CW*Z*2, 8), "DIFF", fill=(255,255,255))
out.save(ROOT / "testing/output/_diff_heatmap.png")
print(f"wrote _diff_heatmap.png {out.size}")
