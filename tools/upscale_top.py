#!/usr/bin/env python3
"""Upscale _idle_top10_sweep.png 6x so I can see the poses clearly."""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = Image.open(ROOT / "testing/output/_idle_top10_sweep.png")
dst = src.resize((src.size[0]*6, src.size[1]*6), Image.NEAREST)
dst.save(ROOT / "testing/output/_idle_top10_sweep_6x.png")
print("Wrote _idle_top10_sweep_6x.png", dst.size)
