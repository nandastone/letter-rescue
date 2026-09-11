#!/usr/bin/env python3
from PIL import Image, ImageDraw
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ref = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Wider crop to catch any shifted player
L, T, R, B = 20, 70, 100, 150
refc = ref.crop((L, T, R, B))
clnc = clone.crop((L, T, R, B))
w, h = refc.size
pad = 8
out = Image.new("RGB", (w*2*6 + pad*3, h*6 + pad*2 + 14), (20,20,20))
out.paste(refc.resize((w*6, h*6), Image.NEAREST), (pad, pad+14))
out.paste(clnc.resize((w*6, h*6), Image.NEAREST), (pad*2 + w*6, pad+14))
d = ImageDraw.Draw(out)
d.text((pad, 2), "REF", fill=(220,220,220))
d.text((pad*2 + w*6, 2), "CLONE (new idle)", fill=(220,220,220))
out.save(ROOT / "testing/output/_girl_compare_wide.png")
print("Wrote", out.size)
