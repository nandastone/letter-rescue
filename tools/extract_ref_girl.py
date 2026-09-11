#!/usr/bin/env python3
"""Isolate the ref's girl sprite by subtracting doorway background.

Method: in the ref, the doorway interior above the girl (y=70..95) shows pure
background. Clone that 24x25-row pattern downward to cover the girl area
(y=104..136), then any pixel that differs from the tiled background is part of
the girl sprite. Dump that silhouette + raster it next to our current idle.png
so we can compare directly.

Also compare against CHARS cells to find the best pose match.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGBA")
IDLE = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")

# Region that contains the girl. Use the eye-aligned box (x=43..67, y=104..136).
GX, GY, GW, GH = 43, 104, 24, 32
# Background pattern sample: from y=72..96 at the same x range — doorway only.
BG_X, BG_Y = GX, 72
# The doorway pattern is a 2x2 checker; take 24x24 sample.
bg_h = 24
bg = Image.new("RGB", (GW, GH))
# Tile the BG sample downward
for yy in range(GH):
    for xx in range(GW):
        src_y = BG_Y + (yy % bg_h)
        bg.putpixel((xx, yy), REF.getpixel((BG_X + xx, src_y)))

ref_box = REF.crop((GX, GY, GX+GW, GY+GH))

# Build a silhouette: pixels where ref != bg are "sprite"
sil = Image.new("RGBA", (GW, GH), (0, 0, 0, 0))
sprite_px = 0
for y in range(GH):
    for x in range(GW):
        r = ref_box.getpixel((x, y))
        b = bg.getpixel((x, y))
        if r != b:
            sil.putpixel((x, y), r + (255,))
            sprite_px += 1
print(f"ref girl sprite: {sprite_px} non-bg pixels in {GW}x{GH} box")

# Save extracted sprite
extracted_path = ROOT / "testing/output/_ref_girl_extracted.png"
sil.save(extracted_path)
print(f"wrote {extracted_path}")

# Score every CHARS 24x32 cell: overlay on bg, compare to ref_box
def score_chars(cx, cy):
    cell = CHARS.crop((cx, cy, cx+GW, cy+GH)).convert("RGBA")
    composed = bg.copy().convert("RGBA")
    composed.alpha_composite(_pink_to_alpha(cell))
    composed = composed.convert("RGB")
    n = sum(1 for yy in range(GH) for xx in range(GW)
            if composed.getpixel((xx, yy)) == ref_box.getpixel((xx, yy)))
    return n

def _pink_to_alpha(img):
    d = img.copy()
    px = d.load()
    for y in range(d.size[1]):
        for x in range(d.size[0]):
            r, g, b, a = px[x, y]
            if abs(r - 255) < 8 and abs(g - 85) < 8 and abs(b - 255) < 8:
                px[x, y] = (0, 0, 0, 0)
    return d

TOTAL = GW * GH
results = []
for cy in range(0, CHARS.size[1] - GH + 1):
    for cx in range(0, CHARS.size[0] - GW + 1):
        n = score_chars(cx, cy)
        if n > TOTAL * 0.9:
            results.append((n, cx, cy))
results.sort(reverse=True)

print(f"\ntop 15 CHARS 24x32 candidates (composed over doorway bg):")
for n, cx, cy in results[:15]:
    print(f"  CHARS({cx:3},{cy:3}): {n:4d}/{TOTAL} ({100*n/TOTAL:.1f}%)")

# Score current idle.png too
idle_composed = bg.copy().convert("RGBA")
idle_composed.alpha_composite(IDLE)
idle_composed = idle_composed.convert("RGB")
n_idle = sum(1 for yy in range(GH) for xx in range(GW)
             if idle_composed.getpixel((xx, yy)) == ref_box.getpixel((xx, yy)))
print(f"\ncurrent idle.png composed on bg: {n_idle}/{TOTAL} ({100*n_idle/TOTAL:.1f}%)")

# Render grid: ref | extracted | idle | top 5 CHARS candidates
Z = 6
cell_w = GW * Z
cell_h = GH * Z
pad = 4
items = [("REF", ref_box), ("EXTRACTED", sil.convert("RGB")), ("idle.png",
         _pink_to_alpha(IDLE).convert("RGB"))]
for n, cx, cy in results[:5]:
    cand = CHARS.crop((cx, cy, cx+GW, cy+GH)).convert("RGB")
    items.append((f"CHARS({cx},{cy})\n{100*n/TOTAL:.1f}%", cand))
cols = len(items)
W = cols * (cell_w + pad) + pad
H = cell_h + 40 + pad * 2
if W > 1800:
    print(f"WARN capped — would be {W}px wide")
out = Image.new("RGB", (min(W, 1800), H), (30, 30, 30))
d = ImageDraw.Draw(out)
for i, (label, im) in enumerate(items):
    big = im.resize((cell_w, cell_h), Image.NEAREST)
    x = pad + i * (cell_w + pad)
    if x + cell_w > 1800: break
    out.paste(big, (x, pad))
    for j, line in enumerate(label.split("\n")):
        d.text((x, cell_h + pad + 4 + j * 14), line, fill=(240,240,240))
out_path = ROOT / "testing/output/_ref_girl_compare.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
