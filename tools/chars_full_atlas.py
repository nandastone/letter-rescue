#!/usr/bin/env python3
"""Render every 24x32 cell of CHARS.WR at 6x with a label, so we can identify
exactly which cell is the girl's idle/standing pose.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")
W, H = chars.size
Z = 6
CELL_W = 24; CELL_H = 32
cols_per_row = W // CELL_W
rows = H // CELL_H

out_w = cols_per_row * (CELL_W*Z + 4) + 4
out_h = rows * (CELL_H*Z + 20) + 4
out = Image.new("RGB", (out_w, out_h), (25,25,25))
d = ImageDraw.Draw(out)

for ry in range(rows):
    for cx in range(cols_per_row):
        x0 = cx * CELL_W; y0 = ry * CELL_H
        tile = chars.crop((x0, y0, x0+CELL_W, y0+CELL_H))
        # skip if all pink
        px = list(tile.getdata())
        if all(abs(p[0]-255)<8 and abs(p[1]-85)<8 and abs(p[2]-255)<8 for p in px):
            continue
        big = tile.resize((CELL_W*Z, CELL_H*Z), Image.NEAREST)
        ox = 4 + cx * (CELL_W*Z + 4)
        oy = 4 + ry * (CELL_H*Z + 20)
        out.paste(big, (ox, oy))
        d.text((ox, oy + CELL_H*Z + 2), f"({x0},{y0})", fill=(220,220,220))

out.save(ROOT / "testing/output/_chars_full_atlas.png")
print(f"wrote _chars_full_atlas.png {out.size}")
