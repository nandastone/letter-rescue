#!/usr/bin/env python3
"""Side-by-side zoom of ref vs clone doorway girl."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ref = Image.open(ROOT / "testing/sentinels/smoke_start.png").convert("RGB")
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# crop the girl/doorway region
L, T, R, B = 32, 80, 88, 144
refc = ref.crop((L, T, R, B))
clnc = clone.crop((L, T, R, B))
w, h = refc.size
pad = 8
out = Image.new("RGB", (w*2*6 + pad*3, h*6 + pad*2 + 14), (20,20,20))
refu = refc.resize((w*6, h*6), Image.NEAREST)
clnu = clnc.resize((w*6, h*6), Image.NEAREST)
out.paste(refu, (pad, pad + 14))
out.paste(clnu, (pad*2 + w*6, pad + 14))
from PIL import ImageDraw
d = ImageDraw.Draw(out)
d.text((pad, 2), "REF (DOSBox)", fill=(220,220,220))
d.text((pad*2 + w*6, 2), "CLONE", fill=(220,220,220))
out.save(ROOT / "testing/output/_girl_ref_vs_clone_6x.png")
print("Wrote", out.size)
