#!/usr/bin/env python3
"""Find the exact X shift by auto-correlating ref and clone player-regions.

Normalized cross-correlation of a crop of the player region across small
x-shifts. The minimum diff count at some shift tells the horizontal offset.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Clone's player is drawn at top-left screen = (36, 104) per earlier analysis.
# Take a 24x32 window at that position in clone — that's the clone player drawn on top of doorway.
# Now see which x-offset of that window, when overlaid on ref, minimizes diff
# (considering only pixels where the window is non-transparent-looking... but we can't easily
# tell. Simpler: just count diff pixels at each shift.)

# Actually let's just run diff_count(ref[x0..x0+24, 104..136], clone[x0..x0+24, 104..136]) for x0 range
for x0 in range(25, 60):
    ref_c = REF.crop((x0, 104, x0+24, 136))
    clone_c = CLONE.crop((36, 104, 60, 136))  # fixed clone window at its drawn position
    diffs = 0
    for y in range(32):
        for x in range(24):
            if ref_c.getpixel((x,y)) != clone_c.getpixel((x,y)):
                diffs += 1
    print(f"  ref_x0={x0}: {diffs} diffs vs clone window")

print()
# Similarly shift clone window and keep ref fixed
print("shift clone window, fix ref at (40, 104):")
for x0 in range(20, 60):
    ref_c = REF.crop((40, 104, 64, 136))  # possible ref player position
    clone_c = CLONE.crop((x0, 104, x0+24, 136))
    diffs = 0
    for y in range(32):
        for x in range(24):
            if ref_c.getpixel((x,y)) != clone_c.getpixel((x,y)):
                diffs += 1
    print(f"  clone_x0={x0}: {diffs} diffs")
