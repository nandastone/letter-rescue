#!/usr/bin/env python3
"""Find the girl sprite ref is using. Method:
1. Start from the CLONE (which has the correct backdrop/doorway composed).
2. For each candidate 24x32 source sprite S, build a test image:
       test = CLONE with idle.png ERASED (replaced by CLONE's doorway-only bg)
            + S pasted at the same place as idle.png
3. Score test vs REF pixel-by-pixel inside the girl bbox. Best score wins.

We reconstruct the "doorway-only background at girl position" by looking at the
clone at that position where idle.png is transparent — those pixels are bg.
Where idle.png is opaque, we need to infer bg. For the checker pattern inside
the doorway, we can reliably derive it from the parity of (x, y) plus the
doorway's known color pair.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
IDLE = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGBA")

# Infer sprite top-left of idle.png in the clone. From game.gd comments:
# "sprite top-left screen = player.global_position.x + 4" with player at
# start[0]*16 + 7 = 32+7 = 39, so sprite x = 43. Sprite y top-left = spawn_y - 16
# where spawn_y = ceil(10.5)*16 = 176. Position with offset (0,-16) centered
# 24x32: top-left y = 176 - 16 - 16 = 144 - 16 = ... Let's just find it by
# searching for known eye pixels. Eyes are at sprite (11,7),(12,7),(16,7),(17,7).
# In ref we see WW pairs at screen x=54-55 and x=59-60 on y=111.
# So sprite_tl_x = 54 - 11 = 43, sprite_tl_y = 111 - 7 = 104. Same as before.
SX, SY, SW, SH = 43, 104, 24, 32

# Doorway checker pattern: salmon (255,85,85) at (x+y) even, grey (85,85,85) at odd.
# Verify by sampling a known pure-doorway area above the girl — we already know
# x=44, y=104..106 is pure doorway in both ref and clone.
for y in range(104, 110):
    for x in range(44, 50):
        c = CLONE.getpixel((x, y))
        parity = (x + y) % 2
        # Expected colors
        salmon = (255, 85, 85)
        grey = (85, 85, 85)
        expected = salmon if parity == 0 else grey
        if c != expected:
            print(f"  parity mismatch at ({x},{y}): got {c}, expected {expected}")

def doorway_bg_pixel(x, y):
    if (x + y) % 2 == 0:
        return (255, 85, 85)
    return (85, 85, 85)

# Build bg-only image at the girl region
bg = Image.new("RGB", (SW, SH))
for yy in range(SH):
    for xx in range(SW):
        bg.putpixel((xx, yy), doorway_bg_pixel(SX + xx, SY + yy))

# Verify: where idle.png is transparent, CLONE should equal bg
idle_px = IDLE.load()
mismatch_bg = 0
for yy in range(SH):
    for xx in range(SW):
        _, _, _, a = idle_px[xx, yy]
        if a == 0:
            if CLONE.getpixel((SX+xx, SY+yy)) != bg.getpixel((xx, yy)):
                mismatch_bg += 1
print(f"bg-vs-clone (idle transparent pixels) mismatch: {mismatch_bg}")

# Ref box
ref_box = REF.crop((SX, SY, SX+SW, SY+SH))

def score_sprite(src_rgba, sx, sy):
    """Compose src_rgba[sx..sx+SW, sy..sy+SH] (pink -> alpha) over bg,
    compare to ref_box."""
    composed = bg.copy().convert("RGBA")
    cell = src_rgba.crop((sx, sy, sx+SW, sy+SH)).convert("RGBA")
    px = cell.load()
    for y in range(SH):
        for x in range(SW):
            r, g, b, a = px[x, y]
            if r == 255 and g == 85 and b == 255:
                px[x, y] = (0, 0, 0, 0)
    composed.alpha_composite(cell)
    composed_rgb = composed.convert("RGB")
    match = sum(1 for y in range(SH) for x in range(SW)
                if composed_rgb.getpixel((x, y)) == ref_box.getpixel((x, y)))
    return match, composed_rgb

# Score current idle.png
m_idle, _ = score_sprite(IDLE.convert("RGBA"), 0, 0)
print(f"\nidle.png: {m_idle}/{SW*SH} ({100*m_idle/(SW*SH):.1f}%)")

# Scan CHARS at every possible (sx, sy)
TOTAL = SW * SH
results = []
for sy in range(0, CHARS.size[1] - SH + 1):
    for sx in range(0, CHARS.size[0] - SW + 1):
        m, _ = score_sprite(CHARS, sx, sy)
        if m >= m_idle:
            results.append((m, sx, sy))
results.sort(reverse=True)
print(f"\ntop 15 CHARS (x,y) candidates scoring >= idle.png ({m_idle}):")
for m, sx, sy in results[:15]:
    print(f"  CHARS({sx:3},{sy:3}): {m:4d}/{TOTAL} ({100*m/TOTAL:.1f}%)")

# Also scan STATIC.WR
STATIC = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")
s_results = []
for sy in range(0, STATIC.size[1] - SH + 1):
    for sx in range(0, STATIC.size[0] - SW + 1):
        m, _ = score_sprite(STATIC, sx, sy)
        if m > m_idle:
            s_results.append((m, sx, sy))
s_results.sort(reverse=True)
print(f"\ntop 10 STATIC (x,y) candidates scoring > idle.png:")
for m, sx, sy in s_results[:10]:
    print(f"  STATIC({sx:3},{sy:3}): {m:4d}/{TOTAL} ({100*m/TOTAL:.1f}%)")

# Render top 6 candidates side-by-side (ref + idle + top 4 CHARS + top 1 STATIC)
Z = 6
cw, ch = SW*Z, SH*Z
pad = 4
items = [("REF", ref_box), (f"idle.png\n{m_idle}/{TOTAL}", IDLE.convert("RGB"))]
for m, sx, sy in results[:4]:
    items.append((f"CHARS({sx},{sy})\n{m}/{TOTAL}",
                  CHARS.crop((sx, sy, sx+SW, sy+SH)).convert("RGB")))
if s_results:
    m, sx, sy = s_results[0]
    items.append((f"STATIC({sx},{sy})\n{m}/{TOTAL}",
                  STATIC.crop((sx, sy, sx+SW, sy+SH)).convert("RGB")))

W = min(1800, len(items) * (cw + pad) + pad)
H = ch + 40 + pad * 2
out = Image.new("RGB", (W, H), (30, 30, 30))
d = ImageDraw.Draw(out)
for i, (label, im) in enumerate(items):
    big = im.resize((cw, ch), Image.NEAREST)
    x = pad + i * (cw + pad)
    if x + cw > W: break
    out.paste(big, (x, pad))
    for j, line in enumerate(label.split("\n")):
        d.text((x, ch + pad + 2 + j*14), line, fill=(240,240,240))
out_path = ROOT / "testing/output/_find_girl_sprite.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
