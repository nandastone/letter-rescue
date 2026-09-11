#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
# Wider left side crop
crop = clone.crop((0, 60, 120, 160))
up = crop.resize((crop.size[0]*6, crop.size[1]*6), Image.NEAREST)
up.save(ROOT / "testing/output/_clone_left_6x.png")
print("Wrote")
