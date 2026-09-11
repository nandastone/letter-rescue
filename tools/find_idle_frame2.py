#!/usr/bin/env python3
"""Score each CHARS girl frame against the doorway's embedded girl.

The doorway sprite (spawn_doorway.png) already contains a clean, pre-rendered
girl in the canonical idle pose — it's the DOSBox-authored doorway graphic.
Matching the player idle to that girl is the cleanest signal: exact pixels,
no overlap ambiguity.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHARS = ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png"
DOORWAY = ROOT / "assets/sprites/spawn_doorway.png"
OUT_DIR = ROOT / "testing/output"

def is_pink(px):
    return abs(px[0]-255) < 8 and abs(px[1]-85) < 8 and abs(px[2]-255) < 8

def main():
    chars = Image.open(CHARS).convert("RGB")
    door = Image.open(DOORWAY).convert("RGBA")

    # doorway is 32x40. The girl sits roughly centered horizontally, offset
    # down within the arch. Try a 24x32 crop at (4, 4) — that's centered
    # horizontally (32-24)/2=4 and leaves the top 4px of arch above.
    # Or (4, 8) — top 8px of arch above.
    best_overall = None
    for ox in range(0, 9):
        for oy in range(0, 9):
            door_crop = door.crop((ox, oy, ox + 24, oy + 32)).convert("RGBA")
            # Treat doorway's own red frame / dark pixels as "not girl" by
            # masking: only keep doorway pixels that are NOT the dark-red
            # arch colour. The arch is the outer frame.
            door_rgb = door_crop.convert("RGB")
            dp = list(door_rgb.getdata())

            for y in range(0, chars.size[1] - 32 + 1, 32):
                for x in range(0, chars.size[0] - 24 + 1, 24):
                    tile = chars.crop((x, y, x + 24, y + 32))
                    tp = list(tile.getdata())
                    non_pink = sum(1 for p in tp if not is_pink(p))
                    if non_pink < 200:
                        continue
                    # Score: non-pink pixels in candidate that match doorway pixel
                    matched = 0
                    considered = 0
                    for cp, drgb in zip(tp, dp):
                        if is_pink(cp):
                            continue
                        considered += 1
                        if cp == drgb:
                            matched += 1
                    score = matched / considered if considered > 0 else 0
                    if best_overall is None or score > best_overall[0]:
                        best_overall = (score, matched, considered, x, y, ox, oy)

    score, m, c, x, y, ox, oy = best_overall
    print(f"Best: CHARS ({x}, {y}) at door offset ({ox}, {oy}) = {score:.3f} ({m}/{c})")

    # Now do a full scan at that best alignment and dump top-20
    door_crop = door.crop((ox, oy, ox + 24, oy + 32)).convert("RGB")
    dp = list(door_crop.getdata())
    results = []
    for yy in range(0, chars.size[1] - 32 + 1, 32):
        for xx in range(0, chars.size[0] - 24 + 1, 24):
            tile = chars.crop((xx, yy, xx + 24, yy + 32))
            tp = list(tile.getdata())
            non_pink = sum(1 for p in tp if not is_pink(p))
            if non_pink < 200:
                continue
            matched = 0
            considered = 0
            for cp, drgb in zip(tp, dp):
                if is_pink(cp):
                    continue
                considered += 1
                if cp == drgb:
                    matched += 1
            score = matched / considered if considered > 0 else 0
            results.append((score, matched, considered, xx, yy))
    results.sort(reverse=True)
    print(f"\nTop 10 at doorway offset ({ox}, {oy}):")
    print(f"{'rank':>4} {'score':>6} {'match':>5}/{'of':<5} {'x':>4} {'y':>4}")
    for i, (s, m2, c2, xx, yy) in enumerate(results[:10]):
        print(f"{i+1:>4} {s:>6.3f} {m2:>5}/{c2:<5} {xx:>4} {yy:>4}")

    # build grid
    grid = Image.new("RGB", (24 * 11 + 20, 32 + 20), (30,30,30))
    grid.paste(door_crop, (5, 10))
    for i, (s, m2, c2, xx, yy) in enumerate(results[:10]):
        tile = chars.crop((xx, yy, xx + 24, yy + 32))
        grid.paste(tile, ((i + 1) * 24 + 10, 10))
    grid.save(OUT_DIR / "_idle_top10_vs_doorway.png")
    print(f"\nWrote {OUT_DIR / '_idle_top10_vs_doorway.png'}")

if __name__ == "__main__":
    main()
