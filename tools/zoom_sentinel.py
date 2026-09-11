#!/usr/bin/env python3
"""Zoom into the doorway/girl area of the sentinel."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
s = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
# doorway region: around (32-80, 80-140)
crop = s.crop((32, 80, 88, 144))
up = crop.resize((crop.size[0]*8, crop.size[1]*8), Image.NEAREST)
up.save(ROOT / "testing/output/_sentinel_doorway_8x.png")
print("Wrote _sentinel_doorway_8x.png", up.size)
