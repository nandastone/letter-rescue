#!/usr/bin/env python3
"""Extract STATIC.WR(253, 40, 24, 32) → assets/sprites/player_idle.png with
pink (255, 85, 255) converted to transparent. Per joint-search findings, this
sprite at screen anchor (45, 104) matches REF frame 329 at 95.4%.

Also clip any rogue pixels outside the sprite silhouette: colors other than
the girl's known palette are treated as bleed from adjacent sprites and made
transparent. Palette allowlist derived from histogram of STATIC(253,40).
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")

# Girl palette (from histogram): include only colors belonging to the sprite.
# Black outline, red skin, cyan/green clothing, white eyes. Exclude pink (bg)
# and any brown/tan bleed from adjacent sprites.
GIRL_PALETTE = {
    (0, 0, 0),        # outline
    (255, 85, 85),    # skin/face
    (170, 0, 0),      # dark red (shadow, dress boundary)
    (85, 85, 85),     # grey (hair shadow)
    (170, 170, 170),  # light grey
    (255, 255, 255),  # eye white
    (85, 255, 85),    # bright green dress
    (0, 170, 0),      # dark green dress shadow
    (85, 255, 255),   # cyan shirt
    (0, 170, 170),    # dark cyan shirt shadow
}

cell = STATIC.crop((253, 40, 253+24, 40+32)).convert("RGBA")
px = cell.load()
for y in range(32):
    for x in range(24):
        r, g, b, a = px[x, y]
        rgb = (r, g, b)
        if rgb == (255, 85, 255) or rgb not in GIRL_PALETTE:
            px[x, y] = (0, 0, 0, 0)  # transparent

# Save it as the new idle
out = ROOT / "assets/sprites/player_idle.png"
cell.save(out)
print(f"wrote {out}")
# Confirm transparent count
tp = sum(1 for y in range(32) for x in range(24) if px[x, y][3] == 0)
op = 32*24 - tp
print(f"opaque: {op}, transparent: {tp}")
