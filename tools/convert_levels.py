#!/usr/bin/env python3
"""
Convert Word Rescue .S* level files to Letter Rescue JSON format.

Level format documented at:
https://moddingwiki.shikadi.net/wiki/Word_Rescue_Level_Format

Usage:
    python3 convert_levels.py /path/to/game/files /path/to/output/dir

Expects WR1.S0, WR1.S1, ..., WR1.S14 (Episode 1 has 15 levels).
Also reads WR1.3 for the word list.
"""

import struct
import json
import sys
import os
from pathlib import Path


def read_uint16(data: bytes, offset: int) -> tuple[int, int]:
    """Read a UINT16LE and return (value, new_offset)."""
    val = struct.unpack_from("<H", data, offset)[0]
    return val, offset + 2


def read_coord8(data: bytes, offset: int) -> tuple[tuple[int, int], int]:
    """Read a WR_COORD8 (x, y in 8x8 pixel units). Returns pixel coords."""
    x, offset = read_uint16(data, offset)
    y, offset = read_uint16(data, offset)
    return (x * 8, y * 8), offset


def read_coord16(data: bytes, offset: int) -> tuple[tuple[int, int], int]:
    """Read a WR_COORD16 (x, y in 16x16 pixel units). Returns pixel coords."""
    x, offset = read_uint16(data, offset)
    y, offset = read_uint16(data, offset)
    return (x * 16, y * 16), offset


def read_drip_coord(data: bytes, offset: int) -> tuple[dict, int]:
    """Read a DRIP_COORD (WR_COORD8 origin + UINT16LE max_y)."""
    (px, py), offset = read_coord8(data, offset)
    max_y, offset = read_uint16(data, offset)
    return {"pos_px": [px, py], "max_y_8": max_y}, offset


def decode_rle_layer(data: bytes, offset: int, total_cells: int) -> tuple[list[int], int]:
    """Decode RLE compressed layer data. Returns flat list of tile values."""
    tiles = []
    while len(tiles) < total_cells and offset < len(data):
        count = data[offset]
        offset += 1
        if offset >= len(data):
            break
        value = data[offset]
        offset += 1
        tiles.extend([value] * count)
    return tiles, offset


def parse_level(data: bytes) -> dict:
    """Parse a Word Rescue level file into a structured dict."""
    offset = 0

    # Header.
    map_width, offset = read_uint16(data, offset)    # In 16x16 tiles.
    map_height, offset = read_uint16(data, offset)   # In 16x16 tiles.
    bg_colour, offset = read_uint16(data, offset)    # EGA palette index.
    tileset_idx, offset = read_uint16(data, offset)
    backdrop_idx, offset = read_uint16(data, offset)

    # Player start (WR_COORD8, bottom-middle of door image).
    player_start, offset = read_coord8(data, offset)

    # Exit door (WR_COORD8, top-left of door image, door is 32x40px).
    exit_door, offset = read_coord8(data, offset)

    # Gruzzles.
    gruzzle_count, offset = read_uint16(data, offset)
    gruzzles = []
    for _ in range(gruzzle_count):
        coord, offset = read_coord8(data, offset)
        gruzzles.append(list(coord))

    # Drips.
    drip_count, offset = read_uint16(data, offset)
    drips = []
    for _ in range(drip_count):
        drip, offset = read_drip_coord(data, offset)
        drips.append(drip)

    # Slime buckets (WR_COORD16).
    slime_count, offset = read_uint16(data, offset)
    slime_buckets = []
    for _ in range(slime_count):
        coord, offset = read_coord16(data, offset)
        slime_buckets.append(list(coord))

    # Books (WR_COORD16).
    book_count, offset = read_uint16(data, offset)
    books = []
    for _ in range(book_count):
        coord, offset = read_coord16(data, offset)
        books.append(list(coord))

    # Mystery word letters: always exactly 7, NO count prefix.
    mystery_letters = []
    for _ in range(7):
        coord, offset = read_coord16(data, offset)
        mystery_letters.append(list(coord))

    # Animations (WR_COORD16).
    anim_count, offset = read_uint16(data, offset)
    animations = []
    for _ in range(anim_count):
        coord, offset = read_coord16(data, offset)
        animations.append(list(coord))

    # Foreground tiles (WR_COORD16).
    fg_count, offset = read_uint16(data, offset)
    fg_tiles = []
    for _ in range(fg_count):
        coord, offset = read_coord16(data, offset)
        fg_tiles.append(list(coord))

    # Background layer (RLE compressed, 16x16 tile indices).
    bg_total = map_width * map_height
    bg_tiles, offset = decode_rle_layer(data, offset, bg_total)

    # Book BG-stamp (wr1.exe §1b): level loader writes tile idx 239 (atlas
    # col 19, row 11 — verified to be the pink "book" image in BACK3.WR)
    # at each book position. The sprite-entity book is invisible; BG stamp
    # is the only visible book. Tile data on disk has 0xFF at these cells.
    for (px, py) in books:
        tx, ty = px // 16, py // 16
        if 0 <= ty < map_height and 0 <= tx < map_width:
            bg_tiles[ty * map_width + tx] = 239
    # Letters (tile 238) NOT stamped: atlas cell (18, 11) is a slime bucket,
    # not a letter character. The disassembly's letter→238 claim is suspect
    # until we can verify what the engine actually renders at letter slots.

    # Attribute layer (RLE compressed, 8x8 tile indices). The ModdingWiki
    # claim "(mapWidth - 1) × mapHeight × 4 bytes, positioned from X=1" is
    # wrong for this format: empirical decoding (verified against DOSBox
    # q-block positions in level 1) shows the disk attr layer is full
    # mapWidth × mapHeight × 4 bytes, row-major over the 8x8 grid, with no
    # column-0 shift. Q-block markers (attr vals 0..6) land at the correct
    # pixel positions only with this full-width decode.
    attr_width = map_width * 2  # 8x8 cells per row
    attr_height = map_height * 2
    attr_total = attr_width * attr_height
    attr_tiles, offset = decode_rle_layer(data, offset, attr_total)

    # Reshape into 2D arrays.
    bg_grid = []
    for y in range(map_height):
        row = bg_tiles[y * map_width:(y + 1) * map_width]
        bg_grid.append(row)

    attr_grid = []
    for y in range(attr_height):
        row = attr_tiles[y * attr_width:(y + 1) * attr_width]
        attr_grid.append(row)

    # Extract question block positions from attribute layer.
    # Values 0x00-0x06 are the 7 question mark blocks.
    question_blocks = []
    for y in range(attr_height):
        for x in range(attr_width):
            if y * attr_width + x < len(attr_tiles):
                val = attr_tiles[y * attr_width + x]
                if 0x00 <= val <= 0x06:
                    # Convert 8x8 grid position to pixel coords.
                    question_blocks.append({
                        "index": val,
                        "pos_px": [x * 8, y * 8],
                    })

    # Sort question blocks by index.
    question_blocks.sort(key=lambda b: b["index"])

    # Build collision map from attribute layer.
    # 0x73 = solid, 0x74 = platform (stand on top).
    collision_8x8 = []
    for y in range(attr_height):
        row = []
        for x in range(attr_width):
            idx = y * attr_width + x
            if idx < len(attr_tiles):
                val = attr_tiles[idx]
                if val == 0x73:
                    row.append(1)  # Solid.
                elif val == 0x74:
                    row.append(2)  # One-way platform.
                else:
                    row.append(0)  # Empty.
            else:
                row.append(0)
        collision_8x8.append(row)

    return {
        "map_width_16": map_width,
        "map_height_16": map_height,
        "bg_colour_ega": bg_colour,
        "tileset_index": tileset_idx,
        "backdrop_index": backdrop_idx,
        "player_start_px": list(player_start),
        "exit_door_px": list(exit_door),
        "gruzzles_px": gruzzles,
        "drips": drips,
        "slime_buckets_px": slime_buckets,
        "books_px": books,
        "mystery_letters_px": mystery_letters,
        "animations_px": animations,
        "fg_tiles_px": fg_tiles,
        "question_blocks": [
            {"index": b["index"], "pos_px": b["pos_px"]}
            for b in question_blocks
        ],
        "background_tiles": bg_grid,
        "collision_8x8": collision_8x8,
    }


def load_word_list(path: str) -> list[str]:
    """Load word list from WR?.3 file (space-separated words on one line)."""
    with open(path, "r", encoding="ascii", errors="replace") as f:
        content = f.read().strip()
    return content.split()


def convert_to_game_format(parsed: dict, words: list[str], level_index: int) -> dict:
    """Convert parsed level data to our game's JSON format.

    The original game uses 16x16 tiles. Our game uses 32x32 tiles (2x visual scale)
    but keeps the same tile grid dimensions. All pixel positions from the original
    are divided by 16 to get tile coordinates. The Godot game multiplies tile
    coords by 32 to get screen positions.
    """
    orig_tile = 16  # Original tile size in pixels.

    # Words for this level (8 per level: 7 game words + 1 mystery word).
    level_words = words[level_index * 8:(level_index * 8) + 7]
    mystery_word = words[level_index * 8 + 7] if level_index * 8 + 7 < len(words) else ""

    # Map dimensions stay the same (in tiles).
    map_w = parsed["map_width_16"]
    map_h = parsed["map_height_16"]

    # Question block positions: pixel coords -> tile coords.
    q_blocks = []
    for block in parsed["question_blocks"]:
        px, py = block["pos_px"]
        q_blocks.append([px / orig_tile, py / orig_tile])

    # Build collision grid at original 16x16 tile resolution.
    # Each 16x16 tile covers a 2x2 block of 8x8 attribute cells.
    orig_attr_h = len(parsed["collision_8x8"])
    orig_attr_w = len(parsed["collision_8x8"][0]) if orig_attr_h > 0 else 0

    # Use raw 8x8 collision. The game engine offsets by +2 cells (16px)
    # to account for the attribute layer starting at tile x=1.
    collision = parsed["collision_8x8"]

    def px_to_tiles(px_coord: list) -> list:
        """Convert original pixel coordinates to tile coordinates."""
        return [px_coord[0] / orig_tile, px_coord[1] / orig_tile]

    return {
        "name": "Level %d" % (level_index + 1),
        "width": map_w,
        "height": map_h,
        "tileset": parsed["tileset_index"],
        "backdrop": parsed["backdrop_index"],
        "bg_colour_ega": parsed["bg_colour_ega"],
        "player_start": px_to_tiles(parsed["player_start_px"]),
        "exit_door": px_to_tiles(parsed["exit_door_px"]),
        "question_blocks": q_blocks,
        "words": level_words,
        "gruzzles": [px_to_tiles(g) for g in parsed["gruzzles_px"]],
        "drips": [
            {"pos": px_to_tiles(d["pos_px"]), "max_y": d["max_y_8"]}
            for d in parsed["drips"]
        ],
        "slime_buckets": [px_to_tiles(s) for s in parsed["slime_buckets_px"]],
        "books": [px_to_tiles(b) for b in parsed["books_px"]],
        "mystery_word": mystery_word,
        "mystery_letters": [px_to_tiles(l) for l in parsed["mystery_letters_px"]],
        "animations": [px_to_tiles(a) for a in parsed["animations_px"]],
        "fg_tiles": [px_to_tiles(f) for f in parsed["fg_tiles_px"]],
        "collision": collision,
        "background_tiles": parsed["background_tiles"],
        "_raw": {
            "map_width_16": parsed["map_width_16"],
            "map_height_16": parsed["map_height_16"],
            "player_start_px": parsed["player_start_px"],
            "exit_door_px": parsed["exit_door_px"],
            "gruzzle_count": len(parsed["gruzzles_px"]),
        },
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 convert_levels.py <game_files_dir> <output_dir>")
        print()
        print("Expects the game directory to contain:")
        print("  WR1.S0 through WR1.S14  (level files)")
        print("  WR1.3                    (word list)")
        sys.exit(1)

    game_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine episode (look for WR1, WR2, or WR3 files).
    episode = None
    for ep in [1, 2, 3]:
        if (game_dir / f"WR{ep}.S0").exists():
            episode = ep
            break
        # Try lowercase.
        if (game_dir / f"wr{ep}.s0").exists():
            episode = ep
            break

    if episode is None:
        # Try to find any .S0 file.
        for f in game_dir.iterdir():
            if f.name.upper().endswith(".S0"):
                prefix = f.name[:-3]
                episode = int(prefix[-1]) if prefix[-1].isdigit() else 1
                break

    if episode is None:
        print("Error: Could not find WR?.S0 level files in %s" % game_dir)
        print("Files found:")
        for f in sorted(game_dir.iterdir()):
            print("  %s" % f.name)
        sys.exit(1)

    print("Found Episode %d files." % episode)

    # Load word list.
    word_file = None
    for name in [f"WR{episode}.3", f"wr{episode}.3"]:
        p = game_dir / name
        if p.exists():
            word_file = p
            break

    words = []
    if word_file:
        words = load_word_list(str(word_file))
        print("Loaded %d words from %s" % (len(words), word_file.name))
    else:
        print("Warning: No word list found (WR%d.3). Using placeholder words." % episode)
        words = ["cat", "dog", "hat", "sun", "cup", "bed", "pen"] * 15

    # Convert each level.
    converted = 0
    for level_idx in range(15):
        level_file = None
        for name in [f"WR{episode}.S{level_idx}", f"wr{episode}.s{level_idx}"]:
            p = game_dir / name
            if p.exists():
                level_file = p
                break

        if level_file is None:
            print("  Level %d: file not found, skipping." % (level_idx + 1))
            continue

        data = level_file.read_bytes()
        print("  Level %d: %s (%d bytes)" % (level_idx + 1, level_file.name, len(data)))

        try:
            parsed = parse_level(data)
            level_json = convert_to_game_format(parsed, words, level_idx)

            out_path = output_dir / ("level_%02d.json" % (level_idx + 1))
            with open(out_path, "w") as f:
                json.dump(level_json, f, indent=2)

            print("    -> %s (%dx%d tiles, %d gruzzles, %d words)" % (
                out_path.name,
                level_json["width"],
                level_json["height"],
                len(level_json["gruzzles"]),
                len(level_json["words"]),
            ))
            converted += 1
        except Exception as e:
            print("    ERROR: %s" % e)
            import traceback
            traceback.print_exc()

    print()
    print("Converted %d/%d levels." % (converted, 15))
    print("Output: %s" % output_dir)


if __name__ == "__main__":
    main()
