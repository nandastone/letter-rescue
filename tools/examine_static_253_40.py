#!/usr/bin/env python3
"""Extract STATIC(253, 40, 24, 32) and analyze:
- Is pink the only 'transparent' color, or are there doorway-checker bits baked in?
- Show it at 12x so we can eyeball.
- Also walk the whole row of STATIC around y=40 to see if there's a strip of
  girl-in-doorway animation frames (the spawn sequence)."""
from PIL import Image, ImageDraw
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
STATIC = Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")

# Raw sprite
raw = STATIC.crop((253, 40, 253+24, 40+32))
print("color histogram of STATIC(253,40,24,32):")
c = Counter()
for y in range(32):
    for x in range(24):
        c[raw.getpixel((x, y))[:3]] += 1
for col, n in c.most_common():
    print(f"  {col}: {n}")

# Save standalone
raw.save(ROOT / "testing/output/_static_253_40.png")
print(f"wrote _static_253_40.png")

# Walk the x range at y=40 to find if there's a sprite strip
# Save a zoom of STATIC y=38..74 at x=0..320, 3x
strip = STATIC.crop((0, 32, 320, 80))
big = strip.convert("RGB").resize((320*4, 48*4), Image.NEAREST)
# Add a ruler showing x=0, 24, 48... at top
out = Image.new("RGB", (big.size[0], big.size[1] + 20), (30, 30, 30))
out.paste(big, (0, 20))
d = ImageDraw.Draw(out)
for x in range(0, 321, 24):
    d.text((x*4, 2), str(x), fill=(255, 255, 0))
out_path = ROOT / "testing/output/_static_row_40.png"
out.save(out_path)
print(f"wrote {out_path} {out.size}")

# Zoom the specific girl cell for a clean view
girl_zoom = raw.convert("RGB").resize((24*12, 32*12), Image.NEAREST)
girl_zoom.save(ROOT / "testing/output/_static_girl_zoom.png")
print(f"wrote _static_girl_zoom.png ({24*12}x{32*12})")
