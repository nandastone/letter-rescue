#!/usr/bin/env python3
"""Pull out the top candidates individually and upscale for inspection."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png")

# candidates to inspect
spots = [(168, 96), (120, 160), (240, 64), (0, 64), (192, 96), (48, 96),
         (0, 128), (24, 128), (48, 128)]
cell_w, cell_h = 24, 32
pad = 4
grid = Image.new("RGB", ((cell_w + pad) * len(spots) + pad, cell_h + 20 + pad), (20,20,20))
from PIL import ImageDraw
d = ImageDraw.Draw(grid)
for i, (x, y) in enumerate(spots):
    tile = chars.crop((x, y, x + cell_w, y + cell_h))
    grid.paste(tile, (pad + i * (cell_w + pad), 16))
    d.text((pad + i * (cell_w + pad) + 2, 2), f"{x},{y}", fill=(220,220,220))
up = grid.resize((grid.size[0]*8, grid.size[1]*8), Image.NEAREST)
up.save(ROOT / "testing/output/_chars_candidates_8x.png")
print("Wrote _chars_candidates_8x.png", up.size)
