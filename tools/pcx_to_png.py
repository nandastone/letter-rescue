#!/usr/bin/env python3
"""Convert all PCX files in a directory to PNG (paletted).

Word Rescue's archives store PCX files with non-.pcx extensions like `.WR` or
`.WR1`. Pillow can read them regardless of extension. We preserve the embedded
EGA palette so downstream tools can recover it via PIL's .getpalette() or the
PNG's tRNS/PLTE chunks.

Usage:
    py pcx_to_png.py <src_dir> [<dst_dir>]

If dst_dir is omitted, PNGs are written next to the PCX files.
"""

import json
import sys
from pathlib import Path

from PIL import Image


def convert_dir(src: Path, dst: Path) -> list[tuple[Path, int, int]]:
    dst.mkdir(parents=True, exist_ok=True)
    results = []
    for p in sorted(src.iterdir()):
        if not p.is_file():
            continue
        # Filename cleanup: strip trailing spaces (GX Library 8.3 padding).
        clean_name = p.name.replace(" ", "") + ".png"
        out_path = dst / clean_name
        try:
            img = Image.open(p)
            # Force a load so PIL sniffs the format (won't rely on .pcx ext).
            img.load()
        except Exception as e:
            print(f"  SKIP {p.name}: {e}")
            continue
        # Preserve the palette if the image is indexed; otherwise convert to RGB.
        if img.mode == "P":
            img.save(out_path)
        else:
            img.convert("RGB").save(out_path)
        results.append((out_path, img.width, img.height))
        print(f"  {p.name:20s} -> {out_path.name:24s} ({img.width}x{img.height}, {img.mode})")
    return results


def dump_palette(png_path: Path, out_json: Path) -> None:
    """Read a paletted PNG and write its 16-entry EGA palette as JSON."""
    img = Image.open(png_path)
    img.load()
    if img.mode != "P":
        print(f"  (warning: {png_path.name} is not paletted; cannot dump palette)")
        return
    pal = img.getpalette()[:48]  # 16 entries x 3 channels = 48
    entries = [[pal[i], pal[i + 1], pal[i + 2]] for i in range(0, 48, 3)]
    out_json.write_text(json.dumps({"entries": entries}, indent=2))
    print(f"\nEGA palette (from {png_path.name}, 16 entries):")
    for i, (r, g, b) in enumerate(entries):
        print(f"  {i:2d}: RGB({r:3d}, {g:3d}, {b:3d})  #{r:02X}{g:02X}{b:02X}")
    print(f"Saved to {out_json}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) >= 3 else src
    convert_dir(src, dst)

    # Dump palette from the first paletted PNG in the output directory.
    for p in sorted(dst.iterdir()):
        if p.suffix.lower() == ".png" and p.name != "palette.json":
            try:
                if Image.open(p).mode == "P":
                    dump_palette(p, dst / "palette.json")
                    break
            except Exception:
                continue


if __name__ == "__main__":
    main()
