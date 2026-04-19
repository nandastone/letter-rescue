#!/usr/bin/env python3
"""compare_frames.py — Compare reference frames against test frames.

Produces a per-frame report with pixel-exact diff counts and SSIM scores,
plus diff images highlighting every mismatched pixel.

Usage:
    python tools/compare_frames.py <reference_dir> <test_dir> [--output diff_dir] [--report report.json]

Examples:
    python tools/compare_frames.py testing/reference/frames testing/output/test_frames
    python tools/compare_frames.py ref/ test/ --output diffs/ --report results.json

Dependencies:
    pip install pillow numpy scikit-image
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from skimage.metrics import structural_similarity as ssim
    HAS_SSIM = True
except ImportError:
    HAS_SSIM = False
    print("Warning: scikit-image not installed. SSIM scores will be unavailable.", file=sys.stderr)
    print("Install with: pip install scikit-image", file=sys.stderr)


def load_frame(path: Path) -> np.ndarray:
    """Load an image as a numpy RGB array."""
    img = Image.open(path).convert("RGB")
    return np.array(img)


def compute_diff(ref: np.ndarray, test: np.ndarray) -> dict:
    """Compare two frames. Returns metrics and a diff image (RGB).

    Shape mismatch is a caller-side bug — main() must pre-validate.
    """
    assert ref.shape == test.shape, (
        f"Shape mismatch: reference {ref.shape} vs test {test.shape}"
    )

    # Pixel-exact absolute error: count of pixels that differ at all.
    pixel_diff = np.any(ref != test, axis=2)  # H x W bool mask
    diff_count = int(np.sum(pixel_diff))
    total_pixels = ref.shape[0] * ref.shape[1]

    # Build a diff visualization: identical pixels dimmed, different pixels in red.
    diff_image = (ref.astype(np.float32) * 0.3).astype(np.uint8)
    diff_image[pixel_diff] = [255, 0, 0]

    result = {
        "diff_pixels": diff_count,
        "total_pixels": total_pixels,
        "match_pct": round((1.0 - diff_count / total_pixels) * 100, 4),
    }

    # SSIM (structural similarity).
    if HAS_SSIM:
        score = ssim(ref, test, channel_axis=2)
        result["ssim"] = round(float(score), 6)

    return result, diff_image


def find_frames(directory: Path) -> list[Path]:
    """Find all PNG frames in a directory, sorted by name."""
    frames = sorted(directory.glob("*.png"))
    if not frames:
        # Try common naming patterns.
        frames = sorted(directory.glob("*.PNG"))
    return frames


def align_frame_lists(ref_frames: list[Path], test_frames: list[Path], offset: int = 0):
    """Pair up frames by index, applying an optional offset to test frames.

    Returns list of (ref_path, test_path, frame_number) tuples.
    """
    pairs = []
    for i, ref_path in enumerate(ref_frames):
        test_idx = i + offset
        if 0 <= test_idx < len(test_frames):
            pairs.append((ref_path, test_frames[test_idx], i))
    return pairs


def find_sync_frame(frames: list[Path], sentinel: np.ndarray) -> int:
    """Scan `frames` for the first index that pixel-exact matches `sentinel`.

    Returns -1 if no match is found. Shape mismatches are treated as non-matches
    (rather than errors) so the scan is robust against leading frames of a
    different size (e.g. a splash screen before the game resizes its viewport).
    """
    for i, path in enumerate(frames):
        img = load_frame(path)
        if img.shape != sentinel.shape:
            continue
        if np.array_equal(img, sentinel):
            return i
    return -1


def run(ref_dir: Path, test_dir: Path,
        diff_dir: Path | None = None, report_path: Path | None = None,
        offset: int = 0, sync_frame: Path | None = None,
        sample: int = 0, fail_threshold: int = 0) -> int:
    """Execute a comparison. Returns exit-code-style int (0=ok, 1=error)."""
    ref_dir = Path(ref_dir)
    test_dir = Path(test_dir)
    diff_dir = Path(diff_dir) if diff_dir else (test_dir.parent / "diffs")
    report_path = Path(report_path) if report_path else (diff_dir / "report.json")

    diff_dir.mkdir(parents=True, exist_ok=True)

    ref_frames = find_frames(ref_dir)
    test_frames = find_frames(test_dir)

    if not ref_frames:
        print(f"Error: No PNG frames found in {ref_dir}", file=sys.stderr)
        return 1
    if not test_frames:
        print(f"Error: No PNG frames found in {test_dir}", file=sys.stderr)
        return 1

    print(f"Reference: {len(ref_frames)} frames in {ref_dir}")
    print(f"Test:      {len(test_frames)} frames in {test_dir}")
    print(f"Diffs:     {diff_dir}")
    print(f"Offset:    {offset}")

    if sync_frame:
        sync_frame = Path(sync_frame)
        if not sync_frame.exists():
            print(f"Error: sync-frame file not found: {sync_frame}", file=sys.stderr)
            return 1
        sentinel = load_frame(sync_frame)
        ref_start = find_sync_frame(ref_frames, sentinel)
        if ref_start < 0:
            print(f"Error: sync frame not found anywhere in {ref_dir}", file=sys.stderr)
            return 1
        test_start = find_sync_frame(test_frames, sentinel)
        ref_frames = ref_frames[ref_start:]
        if test_start >= 0:
            test_frames = test_frames[test_start:]
            print(f"Sync:      ref trimmed from frame {ref_start}, test trimmed from {test_start}")
        else:
            # Clone doesn't yet render anything pixel-identical to the sentinel,
            # which is expected until the rendering pipeline matches the original.
            # Keep test frames unchanged; they already start at gameplay (Godot
            # jumps directly into game.tscn via input_replay.gd).
            print(f"Sync:      ref trimmed from frame {ref_start}; test unchanged "
                  "(no pixel-exact match on test side - expected until render matches)")
    print()

    pairs = align_frame_lists(ref_frames, test_frames, offset)

    if sample > 0:
        pairs = [p for i, p in enumerate(pairs) if i % sample == 0]

    results = []
    perfect_count = 0
    worst_frame = None
    worst_diff = 0

    for ref_path, test_path, frame_num in pairs:
        ref_img = load_frame(ref_path)
        test_img = load_frame(test_path)

        if ref_img.shape != test_img.shape:
            print(
                f"Error: shape mismatch at frame {frame_num}: "
                f"ref {ref_path.name}={ref_img.shape} vs "
                f"test {test_path.name}={test_img.shape}. "
                f"Both must be identical (expected 200x320x3).",
                file=sys.stderr,
            )
            return 1

        metrics, diff_img = compute_diff(ref_img, test_img)
        metrics["frame"] = frame_num
        metrics["ref_file"] = ref_path.name
        metrics["test_file"] = test_path.name

        if metrics["diff_pixels"] == 0:
            perfect_count += 1
        else:
            diff_path = diff_dir / f"diff_{frame_num:08d}.png"
            Image.fromarray(diff_img).save(diff_path)
            metrics["diff_file"] = str(diff_path)

        if metrics["diff_pixels"] > worst_diff:
            worst_diff = metrics["diff_pixels"]
            worst_frame = frame_num

        results.append(metrics)

    total = len(results)
    avg_match = sum(r["match_pct"] for r in results) / total if total else 0
    avg_ssim = (sum(r.get("ssim", 0) for r in results) / total) if (total and HAS_SSIM) else None

    summary = {
        "total_frames_compared": total,
        "perfect_frames": perfect_count,
        "imperfect_frames": total - perfect_count,
        "avg_match_pct": round(avg_match, 4),
        "worst_frame": worst_frame,
        "worst_diff_pixels": worst_diff,
    }
    if avg_ssim is not None:
        summary["avg_ssim"] = round(avg_ssim, 6)

    report = {"summary": summary, "frames": results}

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 60)
    print(f"  Frames compared:  {total}")
    print(f"  Perfect (0 diff): {perfect_count} / {total}")
    print(f"  Avg match:        {avg_match:.2f}%")
    if avg_ssim is not None:
        print(f"  Avg SSIM:         {avg_ssim:.4f}")
    if worst_frame is not None:
        print(f"  Worst frame:      #{worst_frame} ({worst_diff} pixels)")
    print(f"  Report:           {report_path}")
    print("=" * 60)

    if fail_threshold > 0 and worst_diff > fail_threshold:
        print(f"\nFAIL: worst frame exceeds threshold ({worst_diff} > {fail_threshold})")
        return 1

    if perfect_count == total:
        print("\nPERFECT MATCH across all frames!")
    else:
        print(f"\n{total - perfect_count} frame(s) differ. Check diff images in {diff_dir}/")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Compare reference vs test frames.")
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("test_dir", type=Path)
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--report", "-r", type=Path, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--sync-frame", type=Path, default=None)
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--fail-threshold", type=int, default=0)
    args = parser.parse_args()
    sys.exit(run(
        ref_dir=args.reference_dir,
        test_dir=args.test_dir,
        diff_dir=args.output,
        report_path=args.report,
        offset=args.offset,
        sync_frame=args.sync_frame,
        sample=args.sample,
        fail_threshold=args.fail_threshold,
    ))


if __name__ == "__main__":
    main()
