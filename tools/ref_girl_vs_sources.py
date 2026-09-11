#!/usr/bin/env python3
"""Extract the ref's girl-in-doorway region at frame 329 (steady state) and
score every candidate source sprite against it. Sources tested:
  - CHARS.WR at every (cx, cy) on a 24x32 grid
  - STATIC.WR at every (sx, sy) (sliding window 24x32)
  - Our player_idle.png (pasted over current spawn_doorway)

Report top matches by pixel-equal count inside the doorway region. Also
render a top-5 side-by-side grid at 6x zoom so we can eyeball the winner.

Output cap: final PNG width kept < 1900px to stay under the many-image
dimension limit.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGBA")
STATIC = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")

# Per summary: sprite top-left screen is (36+7, 104+... well, offset). Use the
# eye glint y=112 anchor. The girl sprite in ref spans approximately
# (36, 104)..(36+24, 104+32)=(60, 136) based on prior measurements (+7 shift).
# We pick the box around the girl — wider than sprite so we include what the
# ref actually renders without pre-judging sprite size.
GX, GY, GW, GH = 36+7, 104, 24, 32   # 43..67, 104..136
ref_box = REF.crop((GX, GY, GX+GW, GY+GH))

def score(src_rgba, sx, sy, sw=GW, sh=GH):
    """Compare src_rgba region at (sx,sy,sw,sh) against ref_box, treating pink
    (255,85,255) as transparent on the source (so it matches whatever is under).
    Returns (matching_px, total_checked). Pink in source is treated as 'matches'
    (wildcard) so the girl-through-transparent-pixel never dings the score.
    """
    match = 0
    total = sw * sh
    for y in range(sh):
        for x in range(sw):
            px = src_rgba.getpixel((sx+x, sy+y))
            r, g, b = px[:3]
            if r == 255 and g == 85 and b == 255:
                match += 1  # transparent: wildcard
                continue
            if (r, g, b) == ref_box.getpixel((x, y)):
                match += 1
    return match, total

TOTAL = GW * GH
print(f"scoring against ref box ({GX},{GY}) {GW}x{GH} ({TOTAL} px)")

best = []  # (score, tag)

# CHARS scan — top-left of each 24x32 cell
for cy in range(0, CHARS.size[1] - GH + 1, 1):
    for cx in range(0, CHARS.size[0] - GW + 1, 1):
        m, _ = score(CHARS, cx, cy)
        if m > TOTAL * 0.80:
            best.append((m, f"CHARS({cx},{cy})", ("chars", cx, cy)))

# STATIC scan
for sy in range(0, STATIC.size[1] - GH + 1, 1):
    for sx in range(0, STATIC.size[0] - GW + 1, 1):
        m, _ = score(STATIC, sx, sy)
        if m > TOTAL * 0.80:
            best.append((m, f"STATIC({sx},{sy})", ("static", sx, sy)))

best.sort(reverse=True)
print(f"\ntop 15 candidates (of {len(best)} above 80%):")
for m, tag, _ in best[:15]:
    print(f"  {m:4d}/{TOTAL} ({100*m/TOTAL:.1f}%)  {tag}")

# Also score our current composition: doorway backdrop (from STATIC at known
# location) + idle.png on top. We approximate this by just checking the CLONE
# frame directly.
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
clone_box = CLONE.crop((GX, GY, GX+GW, GY+GH))
m = sum(1 for y in range(GH) for x in range(GW)
        if clone_box.getpixel((x,y)) == ref_box.getpixel((x,y)))
print(f"\ncurrent clone (doorway + idle.png): {m}/{TOTAL} ({100*m/TOTAL:.1f}%)")

# Render top-5 side-by-side
Z = 6
cols = 6  # ref + 5 candidates
cell_w = GW * Z
cell_h = GH * Z
pad = 4
W = cols * (cell_w + pad) + pad  # = 6*(148) + 4 = 892 — well under 1900
H = cell_h + 30 + pad * 2
out = Image.new("RGB", (W, H), (30, 30, 30))
d = ImageDraw.Draw(out)
# ref
big = ref_box.resize((cell_w, cell_h), Image.NEAREST)
out.paste(big, (pad, pad))
d.text((pad, cell_h + pad + 4), "REF", fill=(255,255,255))

for i, (m, tag, info) in enumerate(best[:5]):
    kind, sx, sy = info
    src = CHARS if kind == "chars" else STATIC
    cand = src.crop((sx, sy, sx+GW, sy+GH)).convert("RGB")
    big = cand.resize((cell_w, cell_h), Image.NEAREST)
    x = pad + (i + 1) * (cell_w + pad)
    out.paste(big, (x, pad))
    d.text((x, cell_h + pad + 4), tag, fill=(255,255,255))
    d.text((x, cell_h + pad + 18), f"{100*m/TOTAL:.1f}%", fill=(200,200,200))

out_path = ROOT / "testing/output/_ref_girl_sources.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
