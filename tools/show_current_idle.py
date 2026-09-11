#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
img = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGBA")
print("player_idle.png size:", img.size)
up = img.resize((img.size[0]*16, img.size[1]*16), Image.NEAREST)
up.save(ROOT / "testing/output/_current_idle_16x.png")
