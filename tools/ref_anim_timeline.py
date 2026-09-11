#!/usr/bin/env python3
"""Walk ref frames 318..500 and log per-frame diff-vs-previous to reveal the
animation cadence at game start. We also crop to just the gruzzle region and
the girl region and report per-region change to separate the two clocks.
"""
from PIL import Image
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "testing/reference/smoke"

# Regions (top-left x, y, w, h) — eyeballed from the side-by-side
# Gruzzle on left ledge, girl in doorway center-left.
REGIONS = {
    "gruzzle": (8, 60, 24, 24),
    "girl":    (36, 100, 24, 40),
    "qblock1": (88, 80, 24, 24),   # should not animate at rest
    "qblock2": (176, 80, 24, 24),
}

frames = sorted(REF.glob("frame_*.png"))
START = 318
END = 500

prev = None
prev_subs = {k: None for k in REGIONS}
print(f"{'idx':>4} {'fname':<28} {'total':>6} " + " ".join(f"{k:>8}" for k in REGIONS))
changes = []
for i in range(START, min(END, len(frames))):
    p = frames[i]
    img = np.array(Image.open(p).convert("RGB"))
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
    if total > 0:
        changes.append((i, total, parts))
    if total > 0 or i < START + 20:
        print(f"{i:>4} {p.name:<28} {total:>6} " + " ".join(parts))
    prev = img
    prev_subs = subs

print(f"\nframes with any change between idx {START}..{END}: {len(changes)}")
