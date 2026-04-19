#!/usr/bin/env python3
"""letter-rescue CLI — cross-platform test pipeline.

Subcommands:
    record <test_name>               Record BSV2+video in one pass via RetroArch,
                                     extract reference PNGs, convert BSV2 to JSON.
    regtest <test_name>              Run the Godot clone against an existing
                                     recording and pixel-diff vs. reference.
    godot-capture <replay.json> ...  Run Godot with a replay, emit PNG frames.
    extract-frames <video> [dir]     ffmpeg: video -> PNGs at 70fps, 320x200.
    compare <ref_dir> <test_dir>     Pixel-diff two frame directories.

All tool paths can be overridden via env vars:
    GODOT, RETROARCH, DOSBOX_CORE, GAME_DIR

Invoke with `py tools/lr.py <cmd> ...` on Windows, `python3 tools/lr.py ...` elsewhere.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent

# Make sibling modules importable.
sys.path.insert(0, str(TOOLS_DIR))
import compare_frames  # noqa: E402
import replay_to_json  # noqa: E402

DEFAULT_GODOT = os.environ.get(
    "GODOT",
    r"C:\Users\nitch\AppData\Local\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.6.1-stable_win64_console.exe",
)
DEFAULT_RETROARCH = os.environ.get("RETROARCH", r"C:\RetroArch-Win64\retroarch.exe")
DEFAULT_DOSBOX_CORE = os.environ.get(
    "DOSBOX_CORE", r"C:\RetroArch-Win64\cores\dosbox_pure_libretro.dll"
)
DEFAULT_GAME_DIR = os.environ.get(
    "GAME_DIR", r"D:\Downloads\Word Rescue (1992)(Apogee Software Ltd)\WORD"
)

RETROARCH_CFG = TOOLS_DIR / "retroarch.cfg"


def count_pngs(d: Path) -> int:
    return len(list(d.glob("*.png"))) if d.exists() else 0


def clear_pngs(d: Path) -> None:
    for p in d.glob("*.png"):
        p.unlink()


def _tail_log(log_path: Path, n: int) -> None:
    """Print the last N lines of a log file to stderr. Surfaces silent errors."""
    if not log_path.is_file():
        return
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        print(f"  (could not read log: {e})", file=sys.stderr)
        return
    print(f"\n--- Last {n} lines of {log_path.name} ---", file=sys.stderr)
    for line in lines[-n:]:
        print(line, file=sys.stderr)
    print("--- end log ---", file=sys.stderr)


def _snapshot_dir(d: Path) -> set:
    """Return the set of files currently in `d` (non-recursive)."""
    if not d.is_dir():
        return set()
    return {p for p in d.iterdir() if p.is_file()}


def _find_new_recording(retroarch_path: Path, before: set) -> Path | None:
    """Locate whatever new file RetroArch dropped in its recordings dir.

    RetroArch (at least the Win64 build we're using) ignores `-r <path>` and
    writes to `<retroarch_dir>/recordings/` with a timestamped filename that
    often has a misleading `.png` extension despite being an FLV H.264 video.
    Grab the largest newly-created file (which is always the video, not any
    thumbnail sibling) so we can route it to the expected test path.
    """
    recordings_dir = retroarch_path.parent / "recordings"
    if not recordings_dir.is_dir():
        return None
    new_files = _snapshot_dir(recordings_dir) - before
    if not new_files:
        return None
    return max(new_files, key=lambda p: p.stat().st_size)


def cmd_record(args) -> int:
    """Record BSV2 inputs AND video simultaneously, then auto-extract frames + JSON.

    Single pass: user plays through, RetroArch writes both .replay and .mkv.
    On exit, we extract reference PNGs from the video and convert BSV2 to
    Godot JSON. This replaces the old record->capture pipeline, whose
    replay-to-video step was not deterministic under DOSBox Pure when the
    session wrote to the virtual disk.
    """
    test_name = args.test_name
    retroarch = Path(args.retroarch)
    core = Path(args.core)
    game_dir = Path(args.game_dir)

    replay_file = PROJECT_DIR / "testing" / "replays" / f"{test_name}.replay"
    video_file = PROJECT_DIR / "testing" / "output" / f"{test_name}_dosbox.mkv"
    ref_dir = PROJECT_DIR / "testing" / "reference" / test_name
    godot_json = PROJECT_DIR / "testing" / "replays" / f"{test_name}.json"
    log_file = PROJECT_DIR / "testing" / "output" / f"{test_name}_retroarch.log"

    for label, path in [("RetroArch", retroarch), ("DOSBox core", core)]:
        if not path.is_file():
            print(f"Error: {label} not found at {path}", file=sys.stderr)
            return 1
    if not game_dir.is_dir():
        print(f"Error: game directory not found: {game_dir}", file=sys.stderr)
        return 1

    replay_file.parent.mkdir(parents=True, exist_ok=True)
    video_file.parent.mkdir(parents=True, exist_ok=True)

    for p in (replay_file, video_file, log_file):
        if p.exists():
            p.unlink()

    print(f"=== Recording {test_name} ===")
    print(f"Game dir:   {game_dir}")
    print(f"BSV2 out:   {replay_file}")
    print(f"Video out:  {video_file}")
    print(f"Log out:    {log_file}")
    print()
    print("Play the scenario to test, then close RetroArch to save.")
    print()

    # Snapshot RetroArch's recordings dir so we can detect what it actually
    # writes (it ignores `-r` and uses its own timestamped filenames).
    before_recordings = _snapshot_dir(retroarch.parent / "recordings")

    # Capture RetroArch's verbose output to a log file so a silent recording
    # failure can be diagnosed after the fact.
    with open(log_file, "w", encoding="utf-8", errors="replace") as log:
        result = subprocess.run(
            [
                str(retroarch),
                "--verbose",
                "--appendconfig", str(RETROARCH_CFG),
                "-L", str(core),
                str(game_dir),
                "-R", str(replay_file),
                "-r", str(video_file),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    if not replay_file.is_file():
        print("\nError: BSV2 replay file not produced.", file=sys.stderr)
        _tail_log(log_file, 30)
        return result.returncode or 1
    print(f"\nBSV2 saved:  {replay_file} ({replay_file.stat().st_size} bytes)")

    # Prefer the `-r` output if RetroArch honored it (may change across builds);
    # otherwise grab whatever RetroArch dropped in its default recordings dir.
    if not video_file.is_file() or video_file.stat().st_size < 4096:
        if video_file.is_file():
            video_file.unlink()  # clear the empty container stub
        found = _find_new_recording(retroarch, before_recordings)
        if found is None:
            print(
                "\nError: no usable video produced.\n"
                f"  `-r` target was empty: {video_file}\n"
                f"  RetroArch's default recordings dir had no new files either.\n"
                f"  Full RetroArch log: {log_file}",
                file=sys.stderr,
            )
            _tail_log(log_file, 40)
            return 1
        print(f"  (RetroArch wrote to {found.name} instead of the -r target; relocating)")
        shutil.copy(found, video_file)
    print(f"Video saved: {video_file} ({video_file.stat().st_size} bytes)")

    print("\n=== Extracting reference frames ===")
    ef_args = argparse.Namespace(video_file=str(video_file), output_dir=str(ref_dir), fps=70)
    if cmd_extract_frames(ef_args) != 0:
        return 1

    print("\n=== Converting BSV2 -> Godot JSON ===")
    replay_to_json.convert(replay_file, godot_json, level=1, difficulty=0)

    print("\n=== Done ===")
    print(f"  BSV2:             {replay_file}")
    print(f"  Video:            {video_file}")
    print(f"  Reference frames: {ref_dir} ({count_pngs(ref_dir)} PNGs)")
    print(f"  Godot replay:     {godot_json}")
    return 0


def cmd_extract_frames(args) -> int:
    video = Path(args.video_file)
    out_dir = (
        Path(args.output_dir) if args.output_dir
        else PROJECT_DIR / "testing" / "reference" / "frames"
    )
    fps = args.fps

    if not video.is_file():
        print(f"Error: video file not found: {video}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    clear_pngs(out_dir)

    print(f"[extract] Input:  {video}")
    print(f"[extract] Output: {out_dir}")
    print(f"[extract] FPS:    {fps}")

    r = subprocess.run(
        [
            "ffmpeg", "-i", str(video),
            "-vf", f"fps={fps},scale=320:200:flags=neighbor",
            "-vsync", "0",
            str(out_dir / "frame_%08d.png"),
        ]
    )
    if r.returncode != 0:
        return r.returncode
    print(f"\n[extract] {count_pngs(out_dir)} frames extracted.")
    return 0


def cmd_godot_capture(args) -> int:
    replay = Path(args.replay_file).resolve()
    out_dir = (
        Path(args.output_dir) if args.output_dir
        else PROJECT_DIR / "testing" / "output" / "test_frames"
    )
    godot = Path(args.godot)
    max_frames = getattr(args, "max_frames", 0)

    if not replay.is_file():
        print(f"Error: replay JSON not found: {replay}", file=sys.stderr)
        return 1
    if not godot.is_file():
        print(f"Error: Godot binary not found: {godot}", file=sys.stderr)
        return 1

    data = json.loads(replay.read_text())
    total = int(data.get("total_frames", 3000)) + 100
    if max_frames > 0:
        total = min(total, max_frames)

    out_dir.mkdir(parents=True, exist_ok=True)
    clear_pngs(out_dir)

    print(f"[godot-capture] Replay: {replay}")
    print(f"[godot-capture] Output: {out_dir}")
    print(f"[godot-capture] Frames: {total}")

    user_args = ["--replay", str(replay)]
    if max_frames > 0:
        user_args += ["--max-frame", str(max_frames)]

    r = subprocess.run(
        [
            str(godot),
            "--path", str(PROJECT_DIR),
            "--fixed-fps", "70",
            "--write-movie", str(out_dir / "frame.png"),
            "--quit-after", str(total),
            "--",
            *user_args,
        ],
        cwd=PROJECT_DIR,
    )
    if r.returncode != 0:
        return r.returncode
    print(f"\n[godot-capture] {count_pngs(out_dir)} frames written.")
    return 0


def cmd_compare(args) -> int:
    return compare_frames.run(
        ref_dir=Path(args.reference_dir),
        test_dir=Path(args.test_dir),
        diff_dir=Path(args.output) if args.output else None,
        report_path=Path(args.report) if args.report else None,
        offset=args.offset,
        sync_frame=Path(args.sync_frame) if args.sync_frame else None,
        sample=args.sample,
        fail_threshold=args.fail_threshold,
    )


def cmd_regtest(args) -> int:
    """Run the Godot clone against an existing recording and diff the frames."""
    test_name = args.test_name
    sync_frame = args.sync_frame

    replay_json = PROJECT_DIR / "testing" / "replays" / f"{test_name}.json"
    ref_dir = PROJECT_DIR / "testing" / "reference" / test_name
    out_dir = PROJECT_DIR / "testing" / "output" / test_name
    frames_dir = out_dir / "frames"
    diffs_dir = out_dir / "diffs"

    if not sync_frame:
        default = PROJECT_DIR / "testing" / "sentinels" / f"{test_name}_start.png"
        if default.is_file():
            sync_frame = str(default)
            print(f"Using auto-detected sentinel: {sync_frame}\n")

    print(f"=== Visual Regression Test: {test_name} ===\n")

    if not replay_json.is_file() or count_pngs(ref_dir) == 0:
        print("Error: missing record artifacts.", file=sys.stderr)
        if not replay_json.is_file():
            print(f"  Missing Godot replay JSON: {replay_json}", file=sys.stderr)
        if count_pngs(ref_dir) == 0:
            print(f"  Missing reference frames:  {ref_dir}", file=sys.stderr)
        print(f"  Record first: py tools/lr.py record {test_name}", file=sys.stderr)
        return 1

    max_frames = getattr(args, "frames", 0)
    print("--- Step 1: Capturing Godot frames ---")
    gc_args = argparse.Namespace(
        replay_file=str(replay_json),
        output_dir=str(frames_dir),
        godot=args.godot,
        max_frames=max_frames,
    )
    if cmd_godot_capture(gc_args) != 0:
        return 1
    print()

    print("--- Step 2: Comparing frames ---")
    rc = compare_frames.run(
        ref_dir=ref_dir,
        test_dir=frames_dir,
        diff_dir=diffs_dir,
        report_path=out_dir / "report.json",
        offset=0,
        sync_frame=Path(sync_frame) if sync_frame else None,
        sample=0,
        fail_threshold=0,
    )

    # Copy the last settled frame to a predictable path so the user can always
    # view "the result" of the latest test run at testing/output/<name>/latest.png.
    frames = sorted(frames_dir.glob("*.png")) if frames_dir.exists() else []
    latest_path = None
    if frames:
        latest_path = out_dir / "latest.png"
        shutil.copy(frames[-1], latest_path)

    # Side-by-side comparison at the first gameplay frame (sync). Emitted every
    # regtest so a visual diff is always available without digging through
    # separate frame directories.
    side_by_side_path = _write_side_by_side(
        ref_dir, frames_dir, out_dir, Path(sync_frame) if sync_frame else None
    )

    print()
    print("==========================================")
    print(f"  Test:    {test_name}")
    print(f"  Godot:   {frames_dir}")
    print(f"  Ref:     {ref_dir}")
    print(f"  Diffs:   {diffs_dir}")
    report_file = out_dir / "report.json"
    if report_file.is_file():
        print(f"  Report:  {report_file}")
    if latest_path:
        print(f"  Latest:  {latest_path}   (screenshot of settled frame)")
    if side_by_side_path:
        print(f"  Compare: {side_by_side_path}   (DOS ref | Godot clone, synced)")
    print("==========================================")
    return rc


def _write_side_by_side(ref_dir: Path, test_dir: Path, out_dir: Path,
                        sync_frame: Path | None) -> Path | None:
    """Build a ref|clone composite after the clone has settled into gameplay.

    Godot's level-load does an `await get_tree().process_frame` so the first
    written frame is pre-load (blank playfield). Skip ahead N frames so the
    comparison is at steady state, and use the same N offset on the ref side
    (post-sync) so both show roughly the same game moment. A short label
    strip underneath identifies which side is which.
    """
    try:
        from PIL import Image, ImageDraw
        import numpy as np
    except ImportError:
        return None

    ref_frames = sorted(ref_dir.glob("*.png")) if ref_dir.is_dir() else []
    test_frames = sorted(test_dir.glob("*.png")) if test_dir.is_dir() else []
    if not ref_frames or not test_frames:
        return None

    ref_sync = 0
    if sync_frame and sync_frame.is_file():
        sentinel = np.array(Image.open(sync_frame).convert("RGB"))
        for i, p in enumerate(ref_frames):
            img = np.array(Image.open(p).convert("RGB"))
            if img.shape == sentinel.shape and np.array_equal(img, sentinel):
                ref_sync = i
                break

    # Skip the first frames; level-load await + anim settle. 10 frames ~= 140ms
    # at 70Hz — enough to be post-load but still close to the sync point so the
    # animation cycles are comparable.
    skip = 10
    ref_idx = min(ref_sync + skip, len(ref_frames) - 1)
    test_idx = min(skip, len(test_frames) - 1)

    ref_img = Image.open(ref_frames[ref_idx]).convert("RGB")
    test_img = Image.open(test_frames[test_idx]).convert("RGB")
    if ref_img.size != test_img.size:
        return None
    w, h = ref_img.size
    gutter = 4
    label_h = 14
    composite = Image.new("RGB", (w * 2 + gutter, h + label_h), (40, 40, 40))
    composite.paste(ref_img, (0, label_h))
    composite.paste(test_img, (w + gutter, label_h))
    d = ImageDraw.Draw(composite)
    d.text((4, 2), f"DOSBox ref (frame {ref_idx})", fill=(220, 220, 220))
    d.text((w + gutter + 4, 2), f"Godot clone (frame {test_idx})", fill=(220, 220, 220))
    dest = out_dir / "side_by_side.png"
    composite.save(dest)
    return dest


def main() -> int:
    p = argparse.ArgumentParser(
        description="letter-rescue test pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--retroarch", default=DEFAULT_RETROARCH, help="RetroArch binary")
    p.add_argument("--core", default=DEFAULT_DOSBOX_CORE, help="DOSBox Pure libretro core")
    p.add_argument("--game-dir", default=DEFAULT_GAME_DIR, help="Word Rescue game directory")
    p.add_argument("--godot", default=DEFAULT_GODOT, help="Godot binary")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser(
        "record",
        help="Record BSV2+video in one pass, extract PNGs, convert BSV2 to Godot JSON.",
    )
    sp.add_argument("test_name")
    sp.set_defaults(func=cmd_record)

    sp = sub.add_parser("extract-frames", help="Extract PNG frames from a video file.")
    sp.add_argument("video_file")
    sp.add_argument("output_dir", nargs="?")
    sp.add_argument("--fps", type=int, default=70)
    sp.set_defaults(func=cmd_extract_frames)

    sp = sub.add_parser("godot-capture", help="Run Godot with a replay, emit PNGs.")
    sp.add_argument("replay_file")
    sp.add_argument("output_dir", nargs="?")
    sp.set_defaults(func=cmd_godot_capture)

    sp = sub.add_parser("compare", help="Compare reference vs test frames.")
    sp.add_argument("reference_dir")
    sp.add_argument("test_dir")
    sp.add_argument("--output", "-o")
    sp.add_argument("--report", "-r")
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--sync-frame")
    sp.add_argument("--sample", type=int, default=0)
    sp.add_argument("--fail-threshold", type=int, default=0)
    sp.set_defaults(func=cmd_compare)

    sp = sub.add_parser("regtest", help="Run Godot against an existing recording and diff.")
    sp.add_argument("test_name")
    sp.add_argument("--sync-frame")
    sp.add_argument("--frames", type=int, default=0,
                    help="Cap Godot simulation to N frames (for tight frame-0 "
                         "iteration). 0 = run for the replay's full duration.")
    sp.set_defaults(func=cmd_regtest)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
