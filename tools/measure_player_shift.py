#!/usr/bin/env python3
"""Find the exact horizontal shift between ref player and clone player by
aligning the current idle.png to both images and comparing the best-fit x.

The idle.png is a reliable 24x32 template. The pink (255,85,255) pixels are
transparent. Score = count of non-pink idle pixels that match the image.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
IDLE = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGB")

# idle.png transparency: is it pink or black?
from collections import Counter
idle_colors = Counter(IDLE.getdata())
print("idle.png colors (top 6):", idle_colors.most_common(6))

# Probably pink (255,85,255) since extracted from CHARS.WR.png.
TRANSPARENT = (255, 85, 255)

def best_match(img, sprite, box):
    x0, y0, x1, y1 = box
    spx = list(sprite.getdata())
    results = []
    for y in range(y0, y1-32+1):
        for x in range(x0, x1-24+1):
            crop = img.crop((x, y, x+24, y+32))
            rpx = list(crop.getdata())
            match = 0; total = 0
            for sp, rp in zip(spx, rpx):
                if sp == TRANSPARENT: continue
                total += 1
                if sp == rp: match += 1
            score = match/total if total else 0
            results.append((score, match, total, x, y))
    results.sort(reverse=True)
    return results

SEARCH = (30, 90, 80, 140)
ref_best = best_match(REF, IDLE, SEARCH)
clone_best = best_match(CLONE, IDLE, SEARCH)

print("\nTop 5 idle.png fits against REF:")
for s, m, t, x, y in ref_best[:5]:
    print(f"  ({x},{y}): {s*100:5.1f}% {m}/{t}")
print("\nTop 5 idle.png fits against CLONE:")
for s, m, t, x, y in clone_best[:5]:
    print(f"  ({x},{y}): {s*100:5.1f}% {m}/{t}")

# If idle.png is the CORRECT sprite, best-match against CLONE should be 100%
# and best-match against REF gives us ref player position.
# If idle.png is NOT the correct sprite, neither will be 100%.

# Also: explicitly try idle.png pasted into an empty doorway in both ref/clone
# at various positions, then compare the doorway rendering to understand the
# baseline. Or simpler: find where the 100% match position for CLONE is (proves
# it's the right sprite) and then where REF best matches.
