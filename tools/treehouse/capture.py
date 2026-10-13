"""Capture every DOSBox Pure video callback with controlled keyboard/mouse input.

Frames are lossless, stored once per unique RGB hash. Every callback, including
duplicates, has a timeline entry. This captures emulator output, not yet a
proof that every hardware VGA presentation has reached the frontend.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import zipfile

from libretro import Native
from executable import unpack


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Recorder(Native):
    def __init__(self, core: Path, content: Path, output: Path):
        self.evidence = output
        self.images = output / "frames"
        self.images.mkdir()
        self.timeline = (output / "frames.jsonl").open("w", encoding="utf-8")
        self.run_index = -1  # Callbacks emitted while loading have no retro_run.
        self.callback_index = 0
        self.unique = set()
        self.mouse = {0: 0, 1: 0, 2: 0, 3: 0}
        with zipfile.ZipFile(content) as archive:
            original, _ = unpack(archive.read("TheTreeh/treehse.exe"))
        self.signatures = [(s, original.index(s)) for s in
                           (b"Version 1.1", b"Treehouse Requires 640K memory.", b"MS Run-Time Library")]
        self.image_base = None
        self.clock_samples = 0
        super().__init__(core, content, output / "state", audio=True)

    def game_ready(self):
        region = next(((ptr + offset, length) for start, ptr, offset, length in self.memory
                       if start == 0 and ptr), None)
        if region is None:
            return False
        pointer, length = region
        if self.image_base is None:
            ram = C.string_at(pointer, length)
            if any(ram.count(signature) != 1 for signature, _ in self.signatures):
                return False
            bases = {ram.index(signature) - offset for signature, offset in self.signatures}
            if len(bases) != 1:
                return False
            base = bases.pop()
            if base < 0 or base + 0x341f2 > length:
                return False
            if struct.unpack_from("<H", ram, base + 0x341e4)[0] != 60:
                return False
            self.image_base = base
        return True

    def video(self, data, width, height, pitch):
        duplicate = not data
        if data == C.c_void_p(-1).value:
            raise ValueError("Hardware framebuffer cannot be captured by this runner")
        super().video(data, width, height, pitch)
        row = dict(callback=self.callback_index, run=self.run_index, duplicate=duplicate)
        row["original_tick"] = None
        if self.capture_boundary_version == 1 and self.game_ready():
            pointer = next(ptr + offset for start, ptr, offset, length in self.memory if start == 0 and ptr)
            row["original_tick"] = int.from_bytes(C.string_at(pointer + self.image_base + 0x341ee, 4), "little")
            self.clock_samples += 1
        if self.frame is not None:
            pixels = self.frame.tobytes()
            sha = hashlib.sha256(pixels).hexdigest()
            key = f"{self.frame.width}x{self.frame.height}-{sha}"
            if key not in self.unique:
                self.frame.save(self.images / f"{key}.png")
                self.unique.add(key)
            row.update(width=self.frame.width, height=self.frame.height, rgb_sha256=sha,
                       image=f"frames/{key}.png")
        self.timeline.write(json.dumps(row) + "\n")
        self.callback_index += 1

    def input(self, port, device, index, button):
        if device == 2 and port == 0:
            return self.mouse.get(button, 0)
        return super().input(port, device, index, button)

    def perform(self, actions: list[dict]) -> None:
        for action in actions:
            unknown = set(action) - {"frames", "keys", "mouse", "capture"}
            if unknown:
                raise ValueError(f"Unknown action fields: {sorted(unknown)}")
            frames = action.get("frames", 1)
            if not isinstance(frames, int) or frames <= 0:
                raise ValueError("Action frame count must be a positive integer")
            keys = action.get("keys", [])
            mouse = action.get("mouse", {})
            if set(mouse) - {"dx", "dy", "left", "right"}:
                raise ValueError("Unknown mouse field")
            dx, dy = mouse.get("dx", 0), mouse.get("dy", 0)
            if not all(isinstance(v, int) and -32768 <= v <= 32767 for v in (dx, dy)):
                raise ValueError("Mouse deltas must be signed 16-bit integers")
            for key in keys:
                self.key(key, True)
            try:
                for i in range(frames):
                    self.run_index += 1
                    self.mouse = {0: dx if i == 0 else 0, 1: dy if i == 0 else 0,
                                  2: int(bool(mouse.get("left"))), 3: int(bool(mouse.get("right")))}
                    self.run(1)
            finally:
                for key in keys:
                    self.key(key, False)
                self.mouse = {0: 0, 1: 0, 2: 0, 3: 0}
            if "capture" in action:
                name = action["capture"]
                if not isinstance(name, str) or not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in name):
                    raise ValueError("Snapshot names must use lowercase letters, digits, '_' or '-'")
                self.save(name, ram=True)

    def close(self):
        try:
            super().close()
        finally:
            self.timeline.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path)
    parser.add_argument("output", type=Path, help="New evidence directory")
    default_core = Path(__file__).resolve().parents[2] / "testing/output/treehouse/capture-core/dosbox_pure_libretro.dll"
    parser.add_argument("--core", type=Path, default=Path(os.environ.get("DOSBOX_CORE", str(default_core))))
    parser.add_argument("--actions", type=Path)
    parser.add_argument("--frames", type=int, default=1800)
    parser.add_argument("--allow-unsynchronized-core", action="store_true",
                        help="Diagnostic use only: stock core input and timer delivery can race")
    args = parser.parse_args()
    actions = json.loads(args.actions.read_text(encoding="utf-8")) if args.actions else [dict(frames=args.frames, capture="end")]
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(schema=1, complete=False, content_sha256=digest(args.content), core_sha256=digest(args.core),
                  actions=actions, tool_sha256=digest(Path(__file__)),
                  adapter_sha256=digest(Path(__file__).with_name("libretro.py")),
                  clock_boundary="Not captured; requires a presentation hook",
                  frame_boundary="DOSBox Pure video callback; hardware presentation coverage unverified")
    report_path = args.output / "run.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    native = None
    try:
        native = Recorder(args.core, args.content, args.output)
        report["capture_boundary_version"] = native.capture_boundary_version
        report["snapshot_boundary_version"] = native.snapshot_boundary_version
        report["snapshot_boundary"] = "Finish pending emulation frame before save or restore"
        if native.capture_boundary_version != 1 and not args.allow_unsynchronized_core:
            raise ValueError("Use the instrumented capture core; see tools/treehouse/README.md")
        if native.capture_boundary_version == 1:
            report["clock_boundary"] = "PIT counter sampled inside video callback while emulation worker is held"
        native.perform(actions)
        report.update(complete=True, runs=native.frame_count, video_callbacks=native.callback_index,
                      unique_images=len(native.unique), fps=native.av.timing.fps,
                      sample_rate=native.av.timing.sample_rate,
                      clock_samples=native.clock_samples, main_image_base=native.image_base,
                      options={k.decode(): v.decode() for k, v in native.values.items()})
    finally:
        if native is not None:
            native.close()
        if (args.output / "frames.jsonl").exists():
            report["timeline_sha256"] = digest(args.output / "frames.jsonl")
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Captured {report['video_callbacks']} callbacks, {report['unique_images']} unique frames")


if __name__ == "__main__":
    main()
