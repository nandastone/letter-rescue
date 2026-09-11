#!/usr/bin/env python3
"""Two hypotheses to test:
  H1: Same sprite, shifted by +dx. Paste idle.png at (36+dx, 104) into a clone-like
      doorway image and compare to ref.
  H2: Different sprite at same position. Try each CHARS (x, 64) cell.

Use a synthesized image where we replace the clone's player area with a test sprite.
Actually simpler: we have the clone (known to be idle.png at (36,104)). Compute
  diff(ref, synth) where synth = clone with player-area replaced by test_sprite
  pasted at (36+dx, 104).
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
CHARS = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGBA")
IDLE = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")

# First: we need a "no-player" doorway-only image. Approximate by taking the
# clone and COVERING the 24x32 player region with the doorway's pink-checker pattern.
# Better: use the ref at y=80..95 (above player, only doorway visible) to see the
# pattern, and copy it over the player region.
#
# Easiest: just use the clone but set the player region to be the same as CLONE.
# Then for H1, shift the idle sprite drawing by dx.

def get_sprite_from_chars(cx, cy):
    """Extract 24x32 sprite at (cx,cy) of CHARS, pink→transparent."""
    cell = CHARS.crop((cx, cy, cx+24, cy+32))
    # make pink transparent
    data = cell.load()
    for y in range(32):
        for x in range(24):
            r, g, b, a = data[x, y]
            if abs(r-255) < 8 and abs(g-85) < 8 and abs(b-255) < 8:
                data[x, y] = (0, 0, 0, 0)
    return cell

def paste_sprite_over(base, sprite, x, y):
    """Paste sprite (RGBA) on base (RGB), returns new RGB image."""
    out = base.convert("RGBA").copy()
    out.alpha_composite(sprite, (x, y))
    return out.convert("RGB")

# We need a "doorway without player" baseline. Generate it by:
#   take clone, paste a doorway-only sprite at player pos. We don't have a clean
#   baseline, but we can approximate: use the clone's pixels at the player region
#   EXCEPT where idle.png is opaque, replace with the pink-checker pattern.
def strip_player(clone, idle, px, py):
    out = clone.convert("RGB").copy()
    idle_rgba = idle.convert("RGBA")
    for y in range(idle.size[1]):
        for x in range(idle.size[0]):
            r, g, b, a = idle_rgba.getpixel((x, y))
            if a > 0:
                # approximate doorway bg at this position by using sibling pixels
                # just use the corresponding pixel from an empty doorway region
                # (we'll sample from a y-shift where the sprite doesn't exist)
                # Use (px+x, 60+y) as a guess: y=60-90 is above player, just doorway pattern
                src_y = 60 + (y % 30)
                out.putpixel((px + x, py + y), clone.getpixel((px + x, src_y)))
    return out

# Build stripped clone (doorway-only approximation)
stripped = strip_player(CLONE, IDLE, 36, 104)
stripped.save(ROOT / "testing/output/_stripped_clone.png")

# H1: try pasting idle.png at (36+dx, 104) for dx in -10..+10
print("H1: same sprite (idle.png) shifted by dx:")
for dx in range(-2, 15):
    test = stripped.convert("RGBA").copy()
    test.alpha_composite(IDLE, (36+dx, 104))
    test_rgb = test.convert("RGB")
    # diff only in player-affected region
    diffs = 0
    for y in range(90, 140):
        for x in range(30, 75):
            if REF.getpixel((x,y)) != test_rgb.getpixel((x,y)):
                diffs += 1
    print(f"  dx={dx:+d}: {diffs} diffs  sprite top-left screen = {36+dx}")

print()
print("H2: different CHARS cells at (36, 104):")
results = []
for cy in [64, 96]:
    for cx in range(0, 312, 24):
        sprite = get_sprite_from_chars(cx, cy)
        test = stripped.convert("RGBA").copy()
        test.alpha_composite(sprite, (36, 104))
        test_rgb = test.convert("RGB")
        diffs = 0
        for y in range(90, 140):
            for x in range(30, 75):
                if REF.getpixel((x,y)) != test_rgb.getpixel((x,y)):
                    diffs += 1
        results.append((diffs, cx, cy))
results.sort()
for diffs, cx, cy in results[:15]:
    print(f"  CHARS ({cx:3}, {cy:2}): {diffs} diffs")
