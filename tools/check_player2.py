#!/usr/bin/env python3
"""Check pixel colors in doorway region where player should be."""
from PIL import Image
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
clone = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# crop just the doorway interior
crop = clone.crop((40, 100, 75, 140))
up = crop.resize((crop.size[0]*16, crop.size[1]*16), Image.NEAREST)
up.save(ROOT / "testing/output/_clone_doorway_interior_16x.png")

# check sprite colors - cyan (85, 255, 255), red shirt (255, 85, 85), green skirt
found_cyan = 0
found_red = 0
for y in range(100, 140):
    for x in range(40, 75):
        r, g, b = clone.getpixel((x, y))
        if abs(r-85) < 15 and abs(g-255) < 15 and abs(b-255) < 15:
            found_cyan += 1
        if abs(r-255) < 15 and abs(g-85) < 15 and abs(b-85) < 15:
            found_red += 1
print(f"In doorway box: cyan={found_cyan}, red={found_red}")
