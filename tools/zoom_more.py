#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
chars = Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGB")
# More spots to inspect - front-facing girl poses
spots = [(264, 64), (288, 64), (216, 64), (192, 96), (216, 96), (144, 96), (96, 96)]
for x, y in spots:
    crop = chars.crop((x - 4, y, x + 24 + 4, y + 32))
    up = crop.resize((crop.size[0]*14, crop.size[1]*14), Image.NEAREST)
    up.save(ROOT / f"testing/output/_chars_{x}_{y}_14x.png")
print("Done")
