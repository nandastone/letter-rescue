#!/usr/bin/env python3
"""Render a filmstrip of ref frames 1-400 (select key frames) showing the
player region, so we can see what animation the game plays during spawn.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "testing/reference/smoke"

# Select frames that represent distinct state transitions
KEY_FRAMES = [1, 2, 3, 10, 30, 46, 74, 82, 91, 120, 141, 181, 206, 218, 245, 267, 276, 308, 319, 349, 400]

BX, BY, BW, BH = 28, 85, 50, 60  # player-area crop
Z = 6
pad = 6
cell_w = BW * Z
cell_h = BH * Z
label_h = 18
rows = 3
cols = (len(KEY_FRAMES) + rows - 1) // rows
W = cols * (cell_w + pad) + pad
H = rows * (cell_h + label_h + pad) + pad
out = Image.new("RGB", (W, H), (25, 25, 25))
d = ImageDraw.Draw(out)

for i, fn in enumerate(KEY_FRAMES):
    row = i // cols
    col = i % cols
    path = R / f"frame_{fn:08d}.png"
    img = Image.open(path).convert("RGB")
    crop = img.crop((BX, BY, BX+BW, BY+BH))
    big = crop.resize((cell_w, cell_h), Image.NEAREST)
    x = pad + col * (cell_w + pad)
    y = pad + row * (cell_h + label_h + pad)
    out.paste(big, (x, y))
    d.text((x, y + cell_h + 2), f"frame {fn}", fill=(220,220,220))

out.save(ROOT / "testing/output/_spawn_animation.png")
print(f"wrote _spawn_animation.png {out.size}")
