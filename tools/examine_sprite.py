#!/usr/bin/env python3
"""Examine what's actually in the new player_idle.png at 20x."""
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
img = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")
# render on a checkered background so alpha is visible
bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
for y in range(img.size[1]):
    for x in range(img.size[0]):
        if (x // 2 + y // 2) % 2 == 0:
            bg.putpixel((x, y), (200, 200, 200, 255))
bg = Image.alpha_composite(bg, img)
up = bg.resize((bg.size[0]*20, bg.size[1]*20), Image.NEAREST)
up.save(ROOT / "testing/output/_new_idle_20x.png")
print("Wrote _new_idle_20x.png")
