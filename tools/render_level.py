#!/usr/bin/env python3
"""Render a level as a full image with collision overlay.

This is our 'test' - we render the level, overlay the collision map,
and compare against DOSBox screenshots to find mismatches.

Usage:
    python3 render_level.py <level_json> <tileset_png> <output_png>
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip3 install Pillow")
    sys.exit(1)


def render_level(level_path: str, tileset_path: str, output_path: str):
    level = json.load(open(level_path))
    tileset = Image.open(tileset_path).convert("RGBA")

    map_w = level["width"]
    map_h = level["height"]
    tile_size = 16

    # Create output image.
    img = Image.new("RGBA", (map_w * tile_size, map_h * tile_size), (0, 0, 0, 255))

    # Render background tiles.
    bg_tiles = level.get("background_tiles", [])
    tileset_cols = tileset.width // tile_size  # 320/16 = 20.

    for y, row in enumerate(bg_tiles):
        for x, tile_idx in enumerate(row):
            if tile_idx == 255 or tile_idx == 0xFF:
                continue  # Transparent.
            src_x = (tile_idx % tileset_cols) * tile_size
            src_y = (tile_idx // tileset_cols) * tile_size
            if src_x + tile_size <= tileset.width and src_y + tile_size <= tileset.height:
                tile_img = tileset.crop((src_x, src_y, src_x + tile_size, src_y + tile_size))
                img.paste(tile_img, (x * tile_size, y * tile_size))

    # Overlay collision map (8x8 resolution).
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    col_size = 8  # Collision is at 8x8 resolution.
    collision = level.get("collision", [])
    for y, row in enumerate(collision):
        for x, val in enumerate(row):
            px = x * col_size
            py = y * col_size
            if val == 1:
                draw.rectangle([px, py, px + col_size - 1, py + col_size - 1],
                              fill=(255, 0, 0, 80), outline=(255, 0, 0, 100))
            elif val == 2:
                draw.rectangle([px, py, px + col_size - 1, py + col_size - 1],
                              fill=(0, 0, 255, 80), outline=(0, 0, 255, 100))

    img = Image.alpha_composite(img, overlay)

    # Mark entities.
    draw2 = ImageDraw.Draw(img)

    # Player start: green circle.
    ps = level.get("player_start", [0, 0])
    px, py = int(ps[0] * tile_size), int(ps[1] * tile_size)
    draw2.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(0, 255, 0, 200), outline=(0, 200, 0))

    # Exit door: yellow square.
    ed = level.get("exit_door", [0, 0])
    px, py = int(ed[0] * tile_size), int(ed[1] * tile_size)
    draw2.rectangle([px - 5, py - 5, px + 5, py + 5], fill=(255, 255, 0, 200), outline=(200, 200, 0))

    # Question blocks: orange.
    for qb in level.get("question_blocks", []):
        px, py = int(qb[0] * tile_size), int(qb[1] * tile_size)
        draw2.rectangle([px - 4, py - 4, px + 4, py + 4], fill=(255, 165, 0, 200))

    # Gruzzles: magenta.
    for g in level.get("gruzzles", []):
        px, py = int(g[0] * tile_size), int(g[1] * tile_size)
        draw2.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 0, 255, 200))

    img.save(output_path)
    print(f"Rendered {map_w}x{map_h} tiles ({img.width}x{img.height} px) -> {output_path}")


def dump_attribute_values(level_path: str):
    """Debug: show unique attribute values in the raw collision data."""
    level = json.load(open(level_path))
    collision = level.get("collision", [])
    counts = {}
    for row in collision:
        for val in row:
            counts[val] = counts.get(val, 0) + 1
    print("Collision value counts:")
    for val, count in sorted(counts.items()):
        label = {0: "empty", 1: "solid", 2: "platform"}.get(val, "unknown")
        print(f"  {val}: {count} ({label})")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 render_level.py <level.json> <tileset.png> <output.png>")
        sys.exit(1)

    render_level(sys.argv[1], sys.argv[2], sys.argv[3])
    dump_attribute_values(sys.argv[1])
