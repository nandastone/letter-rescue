#!/usr/bin/env python3
"""Generate placeholder word picture images for all words in the game.

Creates simple colored images with the word drawn as text.
These are placeholders, to be replaced with proper illustrations.
"""

import subprocess
import os
import json
from pathlib import Path

# Collect all unique words from level data.
def get_all_words():
    words = set()
    levels_dir = Path(__file__).parent.parent / "data" / "levels"

    # Check main levels dir and episode subdirs.
    for search_dir in [levels_dir, levels_dir / "ep2", levels_dir / "ep3"]:
        if not search_dir.exists():
            continue
        for f in search_dir.glob("level_*.json"):
            with open(f) as fp:
                data = json.load(fp)
                for w in data.get("words", []):
                    words.add(w.lower())

    return sorted(words)


# Simple color palette for variety.
COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#82E0AA", "#F0B27A",
    "#85C1E9", "#D7BDE2", "#F1948A", "#73C6B6", "#FAD7A0",
    "#AED6F1", "#D5F5E3", "#FADBD8", "#D6EAF8", "#E8DAEF",
]


def generate_picture(word, output_dir, index):
    """Generate a simple picture for a word using ImageMagick."""
    color = COLORS[index % len(COLORS)]
    output_path = output_dir / f"{word}.png"

    # Determine font size based on word length.
    if len(word) <= 3:
        font_size = 20
    elif len(word) <= 5:
        font_size = 16
    elif len(word) <= 7:
        font_size = 13
    else:
        font_size = 10

    cmd = [
        "magick",
        "-size", "64x64",
        f"xc:{color}",
        "-fill", "white",
        "-stroke", "black",
        "-strokewidth", "1",
        # Draw a rounded rectangle border.
        "-draw", "roundrectangle 2,2 61,61 6,6",
        "-fill", "#333333",
        "-stroke", "none",
        "-gravity", "center",
        "-pointsize", str(font_size),
        "-font", "Helvetica-Bold",
        "-annotate", "+0+0", word.upper(),
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback without specific font.
        cmd_simple = [
            "magick",
            "-size", "64x64",
            f"xc:{color}",
            "-fill", "#333333",
            "-gravity", "center",
            "-pointsize", str(font_size),
            "-annotate", "+0+0", word.upper(),
            str(output_path),
        ]
        subprocess.run(cmd_simple, check=True, capture_output=True)

    return output_path


def main():
    words = get_all_words()
    print(f"Found {len(words)} unique words across all levels.")

    output_dir = Path(__file__).parent.parent / "assets" / "pictures"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, word in enumerate(words):
        path = generate_picture(word, output_dir, i)
        print(f"  {word} -> {path.name}")

    print(f"\nGenerated {len(words)} word pictures in {output_dir}")


if __name__ == "__main__":
    main()
