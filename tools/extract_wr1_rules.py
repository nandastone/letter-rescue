"""Extract original-rule maps and exact player atlases from the researched WR1 data.

Usage: python tools/extract_wr1_rules.py "D:/path/to/WORD"
Requires Pillow. Uses the existing decoded CHARS/STATIC sheets; never changes legacy sprites/maps.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image
from convert_levels import parse_level

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", type=Path)
    args = parser.parse_args()
    exe = (args.game_dir / "WR1.EXE").read_bytes()
    digest = hashlib.sha256(exe).hexdigest()
    if digest != "b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f":
        parser.error("Sprite table offsets require the researched WR1.EXE version")
    output = ROOT / "data/wr1"
    output.mkdir(parents=True, exist_ok=True)
    for index in range(15):
        source = args.game_dir / f"WR1.S{index}"
        level = parse_level(source.read_bytes())
        result = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "attributes": level["attributes"],
                  "background_tiles": level["original_background_tiles"],
                  "books": [[v // 16 for v in position] for position in level["books_px"]],
                  "start": [v // 8 for v in level["player_start_px"]],
                  "slots": [{"slot": b["index"], "grid": [v // 8 for v in b["pos_px"]]}
                            for b in level["question_blocks"]]}
        (output / f"level_{index + 1:02}.json").write_text(json.dumps(result), encoding="utf-8")
    sheets = {2: Image.open(ROOT / "assets/extracted/wr1_1_png/CHARS.WR.png").convert("RGBA"),
              5: Image.open(ROOT / "assets/extracted/wr1_1_png/STATIC.WR.png").convert("RGBA")}
    records = []
    for gender, name in enumerate(("boy", "girl")):
        atlas = Image.new("RGBA", (26 * 24, 32))
        for frame in range(26):
            values = struct.unpack_from("<11H", exe, 0x24F50 + 0x884 + gender * 572 + frame * 22)
            width, height, x1, y1, x2, y2, page = values[4:]
            assert (width, height, x2 - x1 + 1, y2 - y1 + 1) == (24, 32, 24, 32)
            sprite = sheets[page].crop((x1, y1, x2 + 1, y2 + 1))
            pixels = sprite.load()
            for y in range(32):
                for x in range(24):
                    if pixels[x, y][:3] == (255, 85, 255):
                        pixels[x, y] = (0, 0, 0, 0)
                    elif pixels[x, y][:3] == (170, 170, 0):
                        pixels[x, y] = (170, 85, 0, 255)
            atlas.paste(sprite, (frame * 24, 0))
            records.append({"gender": name, "frame": frame, "page": page,
                            "rect": [x1, y1, width, height]})
        atlas.save(ROOT / f"assets/sprites/wr1_{name}.png")
    (output / "player_frames.json").write_text(json.dumps({"exe_sha256": digest, "frames": records}, indent=2), encoding="utf-8")
    print("Extracted 15 raw attribute maps and 26 exact frames for each character")


if __name__ == "__main__":
    main()
