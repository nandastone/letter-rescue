#!/usr/bin/env python3
"""Diff ONLY the 24x32 player-sprite region between ref and clone, at 16x zoom.
Player is at screen top-left (36, 104) based on skin-bbox measurement.

Also: dump the computed ref-player sprite (pixels where ref differs from clone
doorway-only frame) so we see what sprite the ref actually contains.
"""
from PIL import Image, ImageDraw
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
REF = Image.open(ROOT / "testing/reference/smoke/frame_00000329.png").convert("RGB")
CLONE = Image.open(ROOT / "testing/output/smoke/frames/frame00000010.png").convert("RGB")
IDLE = Image.open(ROOT / "assets/sprites/player_idle.png").convert("RGB")

# Tighter player box based on skin bbox (32..68, 95..134) + a little margin
PX, PY, PW, PH = 32, 95, 40, 42
Z = 16

def zoom(img): return img.resize((img.size[0]*Z, img.size[1]*Z), Image.NEAREST)

ref_c = REF.crop((PX, PY, PX+PW, PY+PH))
clone_c = CLONE.crop((PX, PY, PX+PW, PY+PH))

# Diff overlay
diff = Image.new("RGB", (PW, PH), (0,0,0))
for y in range(PH):
    for x in range(PW):
        r = ref_c.getpixel((x,y)); c = clone_c.getpixel((x,y))
        if r != c:
            diff.putpixel((x,y), (255, 0, 0))
        else:
            diff.putpixel((x,y), (40, 40, 40))

# Build image: ref (16x) | clone (16x) | diff (16x)
pad = 10
th = 24
out = Image.new("RGB", (PW*Z*3 + pad*4, PH*Z + th + pad*2), (20,20,20))
d = ImageDraw.Draw(out)
out.paste(zoom(ref_c), (pad, th))
out.paste(zoom(clone_c), (pad*2 + PW*Z, th))
out.paste(zoom(diff), (pad*3 + PW*Z*2, th))
d.text((pad, 6), "REF crop (32,95)-(72,137)", fill=(255,255,255))
d.text((pad*2 + PW*Z, 6), "CLONE crop", fill=(255,255,255))
d.text((pad*3 + PW*Z*2, 6), "DIFF (red)", fill=(255,255,255))
out.save(ROOT / "testing/output/_player_diff_16x.png")
print(f"wrote _player_diff_16x.png {out.size}")

# Histogram per color on differing pixels only
diffs = Counter()
for y in range(PH):
    for x in range(PW):
        r = ref_c.getpixel((x,y)); c = clone_c.getpixel((x,y))
        if r != c:
            diffs[(r, c)] += 1

print("\ntop 30 (ref_rgb -> clone_rgb) at differing pixels:")
for (rc, cc), n in diffs.most_common(30):
    print(f"  {rc} -> {cc}   x{n}")

# Also: extract what the ref shows at each pixel of the expected player bbox (36,104..60,136)
# That's (36-PX, 104-PY) = (4, 9) within the crop, 24x32.
pref = ref_c.crop((4, 9, 4+24, 9+32))
pref.save(ROOT / "testing/output/_ref_player_crop_24x32.png")
pcln = clone_c.crop((4, 9, 4+24, 9+32))
pcln.save(ROOT / "testing/output/_clone_player_crop_24x32.png")

# Compare our idle.png to the ref-player crop, pixel by pixel (ignoring pink in idle)
match = 0; total = 0; mismatch_colors = Counter()
for y in range(32):
    for x in range(24):
        ip = IDLE.getpixel((x,y))
        rp = pref.getpixel((x,y))
        cp = pcln.getpixel((x,y))
        # idle.png transparent is black (0,0,0) since png has no alpha; but maybe
        # it's pink. Check both.
        if ip == (255, 85, 255) or ip == (0, 0, 0):
            continue
        total += 1
        if ip == rp: match += 1
        else: mismatch_colors[(ip, rp)] += 1

print(f"\nidle.png vs ref 24x32 crop: {match}/{total} exact match ({match/total*100 if total else 0:.1f}%)")
print("top 15 mismatches (idle -> ref):")
for (ip, rp), n in mismatch_colors.most_common(15):
    print(f"  idle {ip} vs ref {rp}  x{n}")
