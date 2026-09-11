#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
# Just the girl body rectangle
crop = s.crop((42, 102, 76, 140))
up = crop.resize((crop.size[0]*20, crop.size[1]*20), Image.NEAREST)
up.save(ROOT / "testing/output/_ref_girl_20x.png")
print("Wrote", up.size)
