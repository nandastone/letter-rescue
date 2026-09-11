#!/usr/bin/env python3
"""For every differing pixel in the player region, categorize as:
  (a) Clone has a sprite pixel, ref has doorway → clone's sprite extends too far
  (b) Ref has a sprite pixel, clone has doorway → ref's sprite extends further
  (c) Both have sprite pixels but different colors → color/pose inside sprite
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Doorway interior pattern: checker of (255,85,85) and (170,0,0)... Actually the
# doorway interior shows a pink-checker pattern of (255,85,85) alt (170,0,0)?
# Let me look at known doorway pixels.
# From the zoom: doorway interior is alternating (255,85,85) (light red/salmon)
# and (170,0,0) (dark red) in a checker. Let's verify.
from collections import Counter
# Sample the doorway interior where NO player is — above player (y=80..95, x=40..60)
sample = Counter()
for y in range(80, 95):
    for x in range(38, 62):
        sample[REF.getpixel((x,y))] += 1
print("Doorway interior colors (ref y=80..95):")
for c, n in sample.most_common(6):
    print(f"  {c}: {n}")

# So doorway colors are those. Use them as "not sprite".
doorway_colors = set(c for c, _ in sample.most_common(4))
print(f"treating as doorway: {doorway_colors}")

# Now categorize diffs
ca, cb, cc = 0, 0, 0
for y in range(95, 140):
    for x in range(30, 75):
        r = REF.getpixel((x,y)); c = CLONE.getpixel((x,y))
        if r == c: continue
        r_is_doorway = r in doorway_colors
        c_is_doorway = c in doorway_colors
        if c_is_doorway and not r_is_doorway:
            cb += 1  # ref extends, clone doesn't
        elif r_is_doorway and not c_is_doorway:
            ca += 1  # clone extends, ref doesn't
        else:
            cc += 1  # both have sprite pixels with different colors

print(f"\ncategorized {ca+cb+cc} diff pixels:")
print(f"  (a) clone sprite extends where ref has doorway: {ca}")
print(f"  (b) ref sprite extends where clone has doorway: {cb}")
print(f"  (c) both are sprite but different colors (pose):  {cc}")

# Visualize: paint each category differently
vis = REF.copy()
for y in range(95, 140):
    for x in range(30, 75):
        r = REF.getpixel((x,y)); c = CLONE.getpixel((x,y))
        if r == c:
            # darken
            vis.putpixel((x,y), tuple(v//3 for v in r))
            continue
        r_is_doorway = r in doorway_colors
        c_is_doorway = c in doorway_colors
        if c_is_doorway and not r_is_doorway:
            vis.putpixel((x,y), (255, 255, 0))  # yellow: ref-only sprite pixel
        elif r_is_doorway and not c_is_doorway:
            vis.putpixel((x,y), (0, 255, 255))  # cyan: clone-only sprite pixel
        else:
            vis.putpixel((x,y), (255, 0, 255))  # magenta: color diff

# Zoom 12x
Z = 12
big = vis.crop((25, 90, 80, 140)).resize((55*Z, 50*Z), Image.NEAREST)
big.save(ROOT / "testing/output/_diff_categorized.png")
print(f"wrote _diff_categorized.png {big.size}")
print("yellow = REF-only sprite pixel  (ref extends here, we don't)")
print("cyan   = CLONE-only sprite pixel (we extend here, ref doesn't)")
print("magenta= color diff (both have sprite, different colors)")
