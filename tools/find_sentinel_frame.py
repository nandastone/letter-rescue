#!/usr/bin/env python3
"""Report which ref frame matches the sentinel and look at a few frames around
it to understand what constitutes 'first playable frame' in the ref capture.
"""
from PIL import Image
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "testing/reference/smoke"
SENTINEL = ROOT / "testing/sentinels/smoke_start.png"

sent = np.array(Image.open(SENTINEL).convert("RGB"))
print(f"sentinel shape: {sent.shape}")

# Find matching ref frame
frames = sorted(REF_DIR.glob("frame_*.png"))
matches = []
for i, p in enumerate(frames):
    img = np.array(Image.open(p).convert("RGB"))
    if img.shape == sent.shape and np.array_equal(img, sent):
        matches.append((i, p.name))

print(f"sentinel matches {len(matches)} ref frames: {matches[:5]}{' ...' if len(matches)>5 else ''}")

# Look at the match window: frames around first match
if matches:
    first_idx = matches[0][0]
    print(f"\nfirst match at ref index {first_idx} (file {matches[0][1]})")

    # Compute diff between consecutive frames in [first-3 .. first+5] to see
    # what's changing. Large diff = scene transition; small = just animation.
    start = max(0, first_idx - 3)
    end = min(len(frames), first_idx + 8)
    prev = None
    for i in range(start, end):
        img = np.array(Image.open(frames[i]).convert("RGB"))
        if prev is not None:
            d = int((img != prev).any(axis=-1).sum())
        else:
            d = -1
        mark = "  <-- SENTINEL" if i == first_idx else ""
        print(f"  frame {i:4d} ({frames[i].name}): {d:6d} px diff vs prev{mark}")
        prev = img
