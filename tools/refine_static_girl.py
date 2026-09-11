#!/usr/bin/env python3
"""Fine-scan STATIC at (251 +- 5, 40 +- 5) and also try slightly different
screen positions (in case clone's sprite anchor is 1px off). Find absolute
best match, visualize top 3."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
STATIC = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")

SW, SH = 24, 32

def doorway_bg(x, y):
    return (255, 85, 85) if (x + y) % 2 == 0 else (85, 85, 85)

def score(src_sx, src_sy, anchor_x, anchor_y):
    bg = Image.new("RGB", (SW, SH))
    for yy in range(SH):
        for xx in range(SW):
            bg.putpixel((xx, yy), doorway_bg(anchor_x + xx, anchor_y + yy))
    ref_box = REF.crop((anchor_x, anchor_y, anchor_x+SW, anchor_y+SH))
    cell = STATIC.crop((src_sx, src_sy, src_sx+SW, src_sy+SH)).convert("RGBA")
    px = cell.load()
    for y in range(SH):
        for x in range(SW):
            r, g, b, a = px[x, y]
            if r == 255 and g == 85 and b == 255:
                px[x, y] = (0, 0, 0, 0)
    composed = bg.convert("RGBA")
    composed.alpha_composite(cell)
    composed = composed.convert("RGB")
    return sum(1 for y in range(SH) for x in range(SW)
               if composed.getpixel((x, y)) == ref_box.getpixel((x, y))), composed

# Fine scan source position (251±5, 40±5) at fixed anchor (43, 104)
print("fine scan of source position at fixed anchor (43, 104):")
best = (0, 0, 0, None)
for sy in range(30, 60):
    for sx in range(240, 280):
        m, _ = score(sx, sy, 43, 104)
        if m > best[0]:
            best = (m, sx, sy, None)
print(f"  best: STATIC({best[1]}, {best[2]}): {best[0]}/768 ({100*best[0]/768:.1f}%)")

# Try different anchors around (43, 104) with source (251, 40)
print("\nanchor scan with source fixed at (251, 40):")
best_anchor = (0, 0, 0)
for ay in range(100, 110):
    for ax in range(38, 50):
        m, _ = score(251, 40, ax, ay)
        if m > best_anchor[0]:
            best_anchor = (m, ax, ay)
print(f"  best: anchor ({best_anchor[1]}, {best_anchor[2]}): {best_anchor[0]}/768 ({100*best_anchor[0]/768:.1f}%)")

# Search both source and anchor jointly
print("\njoint search:")
best_joint = (0, 0, 0, 0, 0)
for sy in range(32, 48):
    for sx in range(245, 265):
        for ay in range(102, 108):
            for ax in range(40, 48):
                m, _ = score(sx, sy, ax, ay)
                if m > best_joint[0]:
                    best_joint = (m, sx, sy, ax, ay)
print(f"  best: STATIC({best_joint[1]},{best_joint[2]}) at anchor ({best_joint[3]},{best_joint[4]}): {best_joint[0]}/768 ({100*best_joint[0]/768:.1f}%)")

# Visualize the best joint result
m, sx, sy, ax, ay = best_joint
_, composed = score(sx, sy, ax, ay)
ref_box = REF.crop((ax, ay, ax+SW, ay+SH))
clone_box = CLONE.crop((ax, ay, ax+SW, ay+SH))
# Direct sprite view
sprite_view = STATIC.crop((sx, sy, sx+SW, sy+SH)).convert("RGB")

Z = 10
cw, ch = SW*Z, SH*Z
pad = 4
items = [
    ("REF", ref_box),
    ("CLONE", clone_box),
    ("COMPOSED", composed),
    (f"STATIC({sx},{sy})\nraw sprite", sprite_view),
]
W = len(items) * (cw + pad) + pad
H = ch + 40 + pad * 2
out = Image.new("RGB", (min(W, 1800), H), (30, 30, 30))
d = ImageDraw.Draw(out)
for i, (label, im) in enumerate(items):
    big = im.resize((cw, ch), Image.NEAREST)
    x = pad + i * (cw + pad)
    if x + cw > 1800: break
    out.paste(big, (x, pad))
    for j, line in enumerate(label.split("\n")):
        d.text((x, ch + pad + 2 + j*14), line, fill=(240,240,240))
out_path = ROOT / "testing/output/_static_girl_refined.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
