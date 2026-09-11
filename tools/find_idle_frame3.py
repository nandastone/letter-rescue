#!/usr/bin/env python3
"""Score CHARS girl frames against the ref with alignment sweep.

For each CHARS 24x32 candidate, find the best placement within the sentinel
girl region by sweeping dx, dy. This handles the fact that I don't know the
exact player sprite top-left in the sentinel.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = ROOT / "testing/sentinels/smoke_start.png"
CHARS = ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png"
OUT_DIR = ROOT / "testing/output"

def is_pink(px):
    return abs(px[0]-255) < 8 and abs(px[1]-85) < 8 and abs(px[2]-255) < 8

def main():
    sent = Image.open(SENTINEL).convert("RGB")
    chars = Image.open(CHARS).convert("RGB")

    # Search window in ref (bigger than player region to allow sweep)
    # Ref image is 320x200. Girl is visible near left side in doorway.
    SEARCH_X0, SEARCH_Y0 = 40, 96
    SEARCH_W, SEARCH_H = 40, 48  # 40x48 window to sweep 24x32 inside

    search = sent.crop((SEARCH_X0, SEARCH_Y0,
                        SEARCH_X0 + SEARCH_W, SEARCH_Y0 + SEARCH_H))
    search.save(OUT_DIR / "_ref_search_window.png")

    # For each CHARS candidate and each (dx, dy), count matching non-pink pixels
    results = []
    for y in range(0, chars.size[1] - 32 + 1, 32):
        for x in range(0, chars.size[0] - 24 + 1, 24):
            tile = chars.crop((x, y, x + 24, y + 32))
            tp = list(tile.getdata())
            non_pink_count = sum(1 for p in tp if not is_pink(p))
            if non_pink_count < 200:
                continue
            best_for_tile = None
            for dx in range(0, SEARCH_W - 24 + 1):
                for dy in range(0, SEARCH_H - 32 + 1):
                    ref_crop = search.crop((dx, dy, dx + 24, dy + 32))
                    rp = list(ref_crop.getdata())
                    matched = 0
                    considered = 0
                    for cp, r in zip(tp, rp):
                        if is_pink(cp):
                            continue
                        considered += 1
                        if cp == r:
                            matched += 1
                    score = matched / considered if considered > 0 else 0
                    if best_for_tile is None or score > best_for_tile[0]:
                        best_for_tile = (score, matched, considered, dx, dy)
            if best_for_tile:
                s, m, c, dx, dy = best_for_tile
                results.append((s, m, c, x, y, dx, dy))

    results.sort(reverse=True)
    print(f"{'rank':>4} {'score':>6} {'m':>4}/{'of':<4} {'cx':>4} {'cy':>4} {'dx':>3} {'dy':>3}")
    for i, (s, m, c, x, y, dx, dy) in enumerate(results[:20]):
        abs_x = SEARCH_X0 + dx
        abs_y = SEARCH_Y0 + dy
        print(f"{i+1:>4} {s:>6.3f} {m:>4}/{c:<4} {x:>4} {y:>4} {abs_x:>3} {abs_y:>3}")

    # Build top-10 grid: side by side tile + corresponding ref crop at best alignment
    top = results[:10]
    cell_w, cell_h = 24, 32
    pad = 3
    row_h = cell_h * 2 + pad * 3 + 12
    grid = Image.new("RGB", ((cell_w + pad) * len(top) + pad, row_h + 20), (30,30,30))
    from PIL import ImageDraw
    d = ImageDraw.Draw(grid)
    for i, (s, m, c, x, y, dx, dy) in enumerate(top):
        tile = chars.crop((x, y, x + 24, y + 32))
        ref_crop = search.crop((dx, dy, dx + 24, dy + 32))
        px = pad + i * (cell_w + pad)
        grid.paste(tile, (px, 20))
        grid.paste(ref_crop, (px, 20 + cell_h + pad))
        d.text((px, 4), f"{int(s*100)}%", fill=(200,200,200))
    grid.save(OUT_DIR / "_idle_top10_sweep.png")
    print(f"\nWrote {OUT_DIR / '_idle_top10_sweep.png'}")

if __name__ == "__main__":
    main()
