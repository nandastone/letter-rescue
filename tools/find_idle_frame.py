#!/usr/bin/env python3
"""Find the CHARS.WR girl frame that best matches the ref idle pose.

The ref sentinel shows the girl standing in the doorway at roughly (48, 104).
The doorway sprite is drawn behind the player, so the ref contains both
doorway pixels AND player pixels. We score each CHARS frame by matching
only against the subset of ref pixels that are the girl's body (not
doorway or background).
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = ROOT / "testing/sentinels/smoke_start.png"
CHARS = ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png"
DOORWAY = ROOT / "assets/sprites/spawn_doorway.png"
OUT_DIR = ROOT / "testing/output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# pink sprite mask colour (full magenta) in EGA sheets
PINK = (255, 85, 255)

def is_pink(px):
    return abs(px[0]-255) < 8 and abs(px[1]-85) < 8 and abs(px[2]-255) < 8

def main():
    sent = Image.open(SENTINEL).convert("RGB")
    chars = Image.open(CHARS).convert("RGB")
    door = Image.open(DOORWAY).convert("RGBA")

    # Spawn in ref: player_start attr pos ~ (3.5, 8) tiles -> (56, 128) px?
    # But sentinel crop shows girl at ~(48, 104) based on prior analysis.
    # The doorway sprite is 32x40, drawn at (raw_start.x - 8, raw_start.y - 32).
    # The player sprite (24x32) is drawn at raw_start centered on bottom-middle,
    # so top-left of player sprite = (raw_start.x - 12, raw_start.y - 32).
    #
    # In the sentinel, girl's visible area appears to be ~(48..72, 104..136).
    # Let's take a 24x32 window there as the ref player region.
    REF_X, REF_Y = 48, 104
    REF_W, REF_H = 24, 32
    ref = sent.crop((REF_X, REF_Y, REF_X + REF_W, REF_Y + REF_H)).convert("RGB")

    # Also grab the doorway image at its offset relative to the 24x32 player
    # window: doorway is 32x40 at (raw_start.x-8, raw_start.y-32); player
    # window top-left is (raw_start.x-12, raw_start.y-32). So doorway in
    # player-window coords starts at (-8-(-12), 0) = (4, 0) and extends
    # to (4+32, 0+40) = (36, 40). Clip to 24x32 window.
    door_crop = Image.new("RGBA", (REF_W, REF_H), (0,0,0,0))
    door_crop.paste(door, (4, 0))

    ref.save(OUT_DIR / "_ref_player_region.png")
    door_crop.save(OUT_DIR / "_ref_doorway_underlay.png")

    # Candidate list: every non-pink 24x32 block in CHARS.WR.
    candidates = []
    W, H = chars.size
    for y in range(0, H - 32 + 1, 32):
        for x in range(0, W - 24 + 1, 24):
            tile = chars.crop((x, y, x + 24, y + 32))
            # only consider tiles with enough non-pink pixels to be a sprite
            px = list(tile.getdata())
            non_pink = sum(1 for p in px if not is_pink(p))
            if non_pink < 200:
                continue
            candidates.append((x, y, tile))

    # Score: count pixels where non-pink candidate pixel matches ref pixel exactly.
    # Pink candidate pixels are sprite-transparent; skip them.
    # Also skip ref pixels that are "definitely doorway" — we approximate this
    # by keeping only ref pixels that DIFFER from the doorway underlay.
    door_rgb = door_crop.convert("RGB")
    door_alpha = door_crop.split()[3]

    ref_px = list(ref.getdata())
    door_px = list(door_rgb.getdata())
    door_a_px = list(door_alpha.getdata())

    # "Girl overlay" mask: pixels that are NOT the doorway (or where doorway
    # had transparency or where ref pixel differs from doorway pixel).
    overlay_mask = []
    for rp, dp, da in zip(ref_px, door_px, door_a_px):
        if da < 128:
            overlay_mask.append(True)  # doorway transparent here, so ref = ?
        else:
            overlay_mask.append(rp != dp)  # pixel differs -> player overlay

    results = []
    for x, y, tile in candidates:
        tp = list(tile.getdata())
        matched = 0
        considered = 0
        for i, cp in enumerate(tp):
            if is_pink(cp):
                continue
            considered += 1
            if not overlay_mask[i]:
                # ref pixel is pure doorway here, don't penalise
                continue
            if cp == ref_px[i]:
                matched += 1
        score = matched / considered if considered > 0 else 0
        results.append((score, matched, considered, x, y))

    results.sort(reverse=True)

    print(f"{'rank':>4} {'score':>6} {'match':>5}/{'of':<5} {'x':>4} {'y':>4}")
    for i, (score, m, c, x, y) in enumerate(results[:20]):
        print(f"{i+1:>4} {score:>6.3f} {m:>5}/{c:<5} {x:>4} {y:>4}")

    # Save top-10 as a grid alongside ref
    top = results[:10]
    grid = Image.new("RGB", (REF_W * (len(top) + 1) + 10, REF_H + 20), (30,30,30))
    grid.paste(ref, (0, 10))
    for i, (score, m, c, x, y) in enumerate(top):
        tile = chars.crop((x, y, x + 24, y + 32))
        grid.paste(tile, ((i + 1) * REF_W + 5, 10))
    grid.save(OUT_DIR / "_idle_top10.png")
    print(f"\nWrote {OUT_DIR / '_idle_top10.png'}")

    if results:
        best = results[0]
        print(f"\nBest: CHARS ({best[3]}, {best[4]}) score={best[0]:.3f}")

if __name__ == "__main__":
    main()
