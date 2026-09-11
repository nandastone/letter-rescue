#!/usr/bin/env python3
"""Zoom in on just the player region in ref vs clone, side by side, at 8x.

Also dumps the clone's current player_idle.png and each row-2 CHARS candidate
so we can eyeball whether the pose is right or just the animation tick differs.
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "testing/reference/smoke/frame_00000329.png"
CLONE = ROOT / "testing/output/smoke/frames/frame00000010.png"
CHARS = ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png"
IDLE = ROOT / "assets/sprites/player_idle.png"
OUT = ROOT / "testing/output/_player_zoom.png"

# Player region in 320x200 ref/clone: sprite top-left sits around (36, 104),
# 24x32. Grab 40x40 for a little margin.
PX, PY, PW, PH = 32, 96, 40, 40
ZOOM = 8

def zoom(img, z=ZOOM):
    return img.resize((img.size[0]*z, img.size[1]*z), Image.NEAREST)

def main():
    ref = Image.open(REF).convert("RGB")
    clone = Image.open(CLONE).convert("RGB")

    ref_crop = ref.crop((PX, PY, PX+PW, PY+PH))
    clone_crop = clone.crop((PX, PY, PX+PW, PY+PH))

    ref_big = zoom(ref_crop)
    clone_big = zoom(clone_crop)

    # diff overlay: highlight pixels that differ
    diff = Image.new("RGB", ref_crop.size, (0,0,0))
    rpx = ref_crop.load(); cpx = clone_crop.load(); dpx = diff.load()
    for y in range(PH):
        for x in range(PW):
            if rpx[x,y] != cpx[x,y]:
                dpx[x,y] = (255, 0, 0)
            else:
                dpx[x,y] = (40, 40, 40)
    diff_big = zoom(diff)

    # also pull every 24x32 candidate from CHARS row 0,1,2,3 that could be "idle"
    chars = Image.open(CHARS).convert("RGB")
    idle = Image.open(IDLE).convert("RGB")

    pad = 12
    label_h = 20
    title_h = 28
    row_top_h = title_h + ref_big.size[1] + label_h
    W = ref_big.size[0]*3 + pad*4
    H = title_h + row_top_h + pad + (32*ZOOM + label_h)*4 + pad
    out = Image.new("RGB", (W, H), (20,20,20))
    d = ImageDraw.Draw(out)

    d.text((pad, 6), "DOSBox ref (frame 329)", fill=(255,255,255))
    d.text((pad*2 + ref_big.size[0], 6), "Godot clone (frame 10)", fill=(255,255,255))
    d.text((pad*3 + ref_big.size[0]*2, 6), "Diff (red = differ)", fill=(255,255,255))

    y0 = title_h
    out.paste(ref_big, (pad, y0))
    out.paste(clone_big, (pad*2 + ref_big.size[0], y0))
    out.paste(diff_big, (pad*3 + ref_big.size[0]*2, y0))

    # second section: current player_idle.png (8x) + all CHARS row candidates at 8x
    y1 = title_h + row_top_h
    d.text((pad, y1 - 14), "Current idle sprite vs CHARS candidates (rows 0/32/64/96 @ 8x):", fill=(255,255,255))

    # current idle
    idle_big = zoom(idle)
    out.paste(idle_big, (pad, y1))
    d.text((pad, y1 + idle_big.size[1] + 2), "idle.png", fill=(200,200,200))

    # CHARS rows
    cw = 24*ZOOM
    for row_idx, row_y in enumerate([0, 32, 64, 96]):
        ry = y1 + (32*ZOOM + label_h)*row_idx
        d.text((pad + idle_big.size[0] + pad, ry - 14 if row_idx else ry),
               f"y={row_y}", fill=(200,200,200))
        for col_idx in range(min(10, chars.size[0]//24)):
            cx = col_idx*24
            tile = chars.crop((cx, row_y, cx+24, row_y+32))
            # skip all-pink
            if all(abs(p[0]-255)<8 and abs(p[1]-85)<8 and abs(p[2]-255)<8 for p in tile.getdata()):
                continue
            tile_big = zoom(tile)
            px = pad + idle_big.size[0] + pad + col_idx*(cw + 4)
            py = ry
            if px + cw > W - pad:
                break
            out.paste(tile_big, (px, py))
            d.text((px, py + tile_big.size[1] + 2), f"({cx},{row_y})", fill=(180,180,180))

    out.save(OUT)
    print(f"Wrote {OUT} {out.size}")

if __name__ == "__main__":
    main()
