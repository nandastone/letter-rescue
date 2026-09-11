#!/usr/bin/env python3
"""Extract the REF player sprite from frame 329.

Strategy: the doorway has a pink-checker bg (alternating (255,85,85) and
(255,85,255)). Anywhere in the player region where the ref pixel is NOT
one of the doorway's expected colors, we can attribute that to the sprite.

Also, clone-player region shows our current idle. We can use:
  sprite_pixel_candidate[y][x] = ref[x,y] if clone[x,y] is pink-checker
                                            but ref[x,y] is not.

This isolates pixels that belong to the ref's sprite but NOT ours.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")

# Pink-checker colors that are "definitely doorway":
DOORWAY_BG = {(255, 85, 85), (255, 85, 255), (170, 0, 0), (170, 85, 0)}
# (170, 85, 0) is brown-red doorway frame

# Player bounding box: (32, 95) - (72, 137)
BX, BY, BW, BH = 30, 90, 48, 50

# Build "ref sprite" = ref px where clone px is doorway_bg AND ref px isn't
#                   OR ref px is NOT doorway_bg AND ref differs from clone
spr = Image.new("RGBA", (BW, BH), (0,0,0,0))
for y in range(BY, BY+BH):
    for x in range(BX, BX+BW):
        r = REF.getpixel((x,y)); c = CLONE.getpixel((x,y))
        if r == c: continue
        if r in DOORWAY_BG:
            # ref shows doorway here -> clone has an extra sprite pixel
            continue
        # ref has sprite-ish content, clone has something else
        spr.putpixel((x-BX, y-BY), (*r, 255))

# and clone sprite where ref has doorway:
spr_clone_extra = Image.new("RGBA", (BW, BH), (0,0,0,0))
for y in range(BY, BY+BH):
    for x in range(BX, BX+BW):
        r = REF.getpixel((x,y)); c = CLONE.getpixel((x,y))
        if r == c: continue
        if c in DOORWAY_BG:
            continue
        spr_clone_extra.putpixel((x-BX, y-BY), (*c, 255))

Z = 14
def zoom(img): return img.resize((img.size[0]*Z, img.size[1]*Z), Image.NEAREST)

from PIL import ImageDraw
pad = 12; th = 22
ref_crop = REF.crop((BX, BY, BX+BW, BY+BH))
clone_crop = CLONE.crop((BX, BY, BX+BW, BY+BH))

out = Image.new("RGB", (BW*Z*4 + pad*5, BH*Z + th + pad*2), (25,25,25))
d = ImageDraw.Draw(out)

out.paste(zoom(ref_crop), (pad, th))
out.paste(zoom(clone_crop), (pad*2 + BW*Z, th))

# Composite ref-sprite on black
s1 = Image.new("RGB", spr.size, (40,40,40))
s1.paste(spr, (0,0), spr)
out.paste(zoom(s1), (pad*3 + BW*Z*2, th))

s2 = Image.new("RGB", spr_clone_extra.size, (40,40,40))
s2.paste(spr_clone_extra, (0,0), spr_clone_extra)
out.paste(zoom(s2), (pad*4 + BW*Z*3, th))

d.text((pad, 4), "REF frame 329", fill=(255,255,255))
d.text((pad*2 + BW*Z, 4), "CLONE frame 10", fill=(255,255,255))
d.text((pad*3 + BW*Z*2, 4), "REF-only (sprite ref has, we don't)", fill=(255,255,255))
d.text((pad*4 + BW*Z*3, 4), "CLONE-only (sprite we have, ref doesn't)", fill=(255,255,255))

out.save(ROOT / "testing/output/_ref_sprite_isolated.png")
print(f"wrote _ref_sprite_isolated.png {out.size}")
