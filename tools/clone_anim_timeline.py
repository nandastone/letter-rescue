#!/usr/bin/env python3
"""Same diff-vs-previous walk over the CLONE output frames to see whether the
clone is static or already ticking animations during frames 0..20."""
from PIL import Image
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "testing/output/smoke/frames"

REGIONS = {
    "gruzzle": (8, 60, 24, 24),
    "girl":    (36, 100, 24, 40),
    "qblock1": (88, 80, 24, 24),
    "qblock2": (176, 80, 24, 24),
}

frames = sorted(TEST.glob("*.png"))
print(f"{len(frames)} clone frames")
prev = None
prev_subs = {k: None for k in REGIONS}
print(f"{'idx':>4} {'total':>6} " + " ".join(f"{k:>8}" for k in REGIONS))
for i in range(0, min(30, len(frames))):
    img = np.array(Image.open(frames[i]).convert("RGB"))
    total = -1
    if prev is not None:
        total = int((img != prev).any(axis=-1).sum())
    parts = []
    subs = {}
    for k, (x, y, w, h) in REGIONS.items():
        sub = img[y:y+h, x:x+w]
        subs[k] = sub
        if prev_subs[k] is not None:
            d = int((sub != prev_subs[k]).any(axis=-1).sum())
        else:
            d = -1
        parts.append(f"{d:>8}")
    print(f"{i:>4} {total:>6} " + " ".join(parts))
    prev = img
    prev_subs = subs
