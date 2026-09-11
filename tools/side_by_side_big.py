#!/usr/bin/env python3
"""Full-frame side by side."""
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ref = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
pad = 10
out = Image.new("RGB", (ref.size[0]*3 + pad*3, ref.size[1]*3 + pad*2), (20,20,20))
out.paste(ref.resize((ref.size[0]*3, ref.size[1]*3), Image.NEAREST), (pad, pad))
out.paste(clone.resize((clone.size[0]*3, clone.size[1]*3), Image.NEAREST), (ref.size[0]*3 + pad*2, pad))
out.save(ROOT / "testing/output/_full_compare_3x.png")
print("Wrote _full_compare_3x.png", out.size)
