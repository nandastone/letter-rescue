#!/usr/bin/env python3
"""Compare ref's gruzzle region (y=61..71, x=48..58 diff bbox extended to
full gruzzle sprite area) against all four gruzzle_walk frames + slimed.
Report best match. Render side-by-side."""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Gruzzle bbox from scene: AnimatedSprite2D at (0, -12), centered anchor.
# Gruzzle sprite is 24x24 (let's verify by opening a walk sprite).
g0 = Image.open(ROOT / "assets/sprites/gruzzle_walk_0.png").convert("RGBA")
print(f"gruzzle_walk_0 size: {g0.size}")
GW, GH = g0.size

# Ref diff cluster was y=61..71, x=48..58. Gruzzle world-pos in level_01:
# Let me find it in level data.
import json
lev = json.loads((ROOT / "data/levels/level_01.json").read_text())
print(f"gruzzles in level: {lev.get('gruzzles')}")

# Take a larger box around the diff cluster: y=55..80, x=42..66.
# Actually, find the gruzzle's on-screen bbox by looking at where ref has
# non-background colors differently from the ledge rock.
# Simpler: use (48-GW+8, 60, GW, GH) — guesstimate.
# Given GW/GH, position is probably (center-GW/2, base-GH) for some center/base.
# Look at the ref crop at a few candidate positions.

def score_region(rx, ry):
    """Score each gruzzle frame at (rx,ry) against ref. Pink -> wildcard."""
    ref_crop = REF.crop((rx, ry, rx+GW, ry+GH))
    results = []
    for i, name in enumerate(["walk_0", "walk_1", "walk_2", "walk_3"]):
        g = Image.open(ROOT / f"assets/sprites/gruzzle_{name}.png").convert("RGBA")
        # composite: use CLONE's bg as background (pink -> CLONE pixel)
        clone_crop = CLONE.crop((rx, ry, rx+GW, ry+GH))
        composed = clone_crop.copy()
        px = g.load()
        for y in range(GH):
            for x in range(GW):
                r, gg, b, a = px[x, y]
                if a > 0 and not (r == 255 and gg == 85 and b == 255):
                    composed.putpixel((x, y), (r, gg, b))
        match = sum(1 for y in range(GH) for x in range(GW)
                    if composed.getpixel((x, y)) == ref_crop.getpixel((x, y)))
        results.append((name, match, composed))
    return results, ref_crop

# Try multiple candidate anchor positions to find where gruzzle renders
print("\ntrying candidate gruzzle positions:")
best_overall = (0, None, None, None)
for ry in range(48, 80):
    for rx in range(36, 72):
        results, ref_crop = score_region(rx, ry)
        top = max(results, key=lambda r: r[1])
        if top[1] > best_overall[0]:
            best_overall = (top[1], rx, ry, top[0])
print(f"best match: {best_overall[3]} at ({best_overall[1]},{best_overall[2]}) {best_overall[0]}/{GW*GH}")

# Show all 4 scores at that position
rx, ry = best_overall[1], best_overall[2]
results, ref_crop = score_region(rx, ry)
print(f"\nall scores at ({rx},{ry}):")
for name, score, _ in results:
    print(f"  {name}: {score}/{GW*GH} ({100*score/(GW*GH):.1f}%)")

# Render grid: REF | CLONE | composed_walk_0 | ..._1 | ..._2 | ..._3
Z = 10
cw, ch = GW*Z, GH*Z
pad = 4
items = [("REF", ref_crop), ("CLONE", CLONE.crop((rx,ry,rx+GW,ry+GH)))]
for name, score, composed in results:
    items.append((f"{name}\n{score}/{GW*GH}", composed))

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
out_path = ROOT / "testing/output/_gruzzle_which_frame.png"
out.save(out_path)
print(f"\nwrote {out_path} {out.size}")
