"""Compare complete capture timelines; reject missing evidence and verify PNGs.

This compares two original runs or a future clone trace using the same schema.
Matching originals establishes repeatability, not clone parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def load_capture(folder: Path) -> tuple[dict, list[dict]]:
    report = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    if not report["complete"]:
        raise ValueError(f"Incomplete capture: {folder}")
    raw = (folder / "frames.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != report["timeline_sha256"]:
        raise ValueError(f"Timeline hash differs: {folder}")
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != report["video_callbacks"] or not rows:
        raise ValueError(f"Missing video callbacks: {folder}")
    verified = set()
    for i, row in enumerate(rows):
        if row["callback"] != i:
            raise ValueError(f"Missing/reordered callback: {folder}/{i}")
        if "image" not in row:
            raise ValueError(f"Callback without known image: {folder}/{i}")
        identity = (row["image"], row["width"], row["height"], row["rgb_sha256"])
        if identity not in verified:
            path = (folder / row["image"]).resolve()
            if not path.is_relative_to(folder.resolve()):
                raise ValueError("Image path outside evidence directory")
            with Image.open(path) as image:
                if image.size != (row["width"], row["height"]):
                    raise ValueError(f"Image dimensions differ: {path}")
                if hashlib.sha256(image.convert("RGB").tobytes()).hexdigest() != row["rgb_sha256"]:
                    raise ValueError(f"Image pixels differ from trace: {path}")
            verified.add(identity)
    return report, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path, help="New comparison JSON file")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Comparison evidence already exists")
    ref, expected = load_capture(args.reference)
    new, actual = load_capture(args.candidate)
    provenance = [field for field in ("content_sha256", "core_sha256", "actions", "options", "snapshot_ticks", "capture_boundary_version") if ref.get(field) != new.get(field)]
    keys = ("callback", "run", "width", "height", "rgb_sha256", "original_tick", "snapshot_tick")
    mismatches = [dict(callback=i, differing_fields=[k for k in keys if a.get(k) != b.get(k)])
                  for i, (a, b) in enumerate(zip(expected, actual)) if any(a.get(k) != b.get(k) for k in keys)]
    audio_a = args.reference / "state/audio.wav"
    audio_b = args.candidate / "state/audio.wav"
    if not audio_a.exists() or not audio_b.exists():
        raise ValueError("Missing audio evidence")
    audio_equal = audio_a.read_bytes() == audio_b.read_bytes()
    result = dict(reference=str(args.reference.resolve()), candidate=str(args.candidate.resolve()),
                  reference_frames=len(expected), candidate_frames=len(actual),
                  provenance_differences=provenance, frame_mismatches=mismatches,
                  audio_identical=audio_equal,
                  passed=not provenance and not mismatches and len(expected) == len(actual) and audio_equal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{'PASS' if result['passed'] else 'FAIL'}: {len(expected)}/{len(actual)} callbacks, "
          f"{len(mismatches)} differing frames, identical audio={audio_equal}")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
