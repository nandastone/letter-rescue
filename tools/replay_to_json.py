#!/usr/bin/env python3
"""replay_to_json.py — Convert a RetroArch v2 replay file to Godot input JSON.

Parses keyboard events and joypad input from a RetroArch .replay file and
outputs a Godot-compatible replay JSON that input_replay.gd can consume.

Usage:
    python tools/replay_to_json.py <replay_file> [--output out.json] [--level 1] [--difficulty 0]

The parser handles the BSV v2 format (magic 0x42535632 / "BSV2"):
  [40-byte header]
  [2-byte compression+encoding]
  [initial checkpoint: state_size bytes]
  [per-frame data...]

Per-frame structure:
  [backref: uint32]
  [key_event_count: uint8]
  [key_events: count * 10 bytes]  — bsv_key_data_t
  [input_event_count: uint16 LE]
  [input_events: count * 8 bytes] — bsv_input_data_t
  [frame_token: uint8]            — 'f', 'C', or 'c'
  [checkpoint data if token != 'f']

Dependencies: None (stdlib only).
"""

import argparse
import json
import struct
import sys
from pathlib import Path


# RetroArch RETROK_* keycodes → Godot action names.
# Based on Word Rescue controls: arrows + space.
RETROK_TO_ACTION = {
    276: "move_left",     # RETROK_LEFT
    275: "move_right",    # RETROK_RIGHT
    273: "jump",          # RETROK_UP
    274: "move_down",     # RETROK_DOWN
    32:  "use_slime",     # RETROK_SPACE
    13:  "use_slime",     # RETROK_RETURN (alternate)
}

# DOSBox Pure "Generic Keyboard Bindings" — retropad button ID → action.
# Used when the user plays with a gamepad.
JOYPAD_TO_ACTION = {
    4: "jump",        # RETRO_DEVICE_ID_JOYPAD_UP
    5: "move_down",   # RETRO_DEVICE_ID_JOYPAD_DOWN
    6: "move_left",   # RETRO_DEVICE_ID_JOYPAD_LEFT
    7: "move_right",  # RETRO_DEVICE_ID_JOYPAD_RIGHT
    9: "use_slime",   # RETRO_DEVICE_ID_JOYPAD_X (Space)
    3: "use_slime",   # RETRO_DEVICE_ID_JOYPAD_START (Enter)
}

REPLAY_MAGIC = 0x42535632  # "BSV2"
HEADER_SIZE = 40


def parse_header(data: bytes) -> dict:
    """Parse the 40-byte replay header."""
    if len(data) < HEADER_SIZE:
        raise ValueError(f"File too small for header ({len(data)} bytes)")

    fields = struct.unpack_from("<IIIIQIII", data, 0)
    magic = fields[0]
    version = fields[1]
    crc = fields[2]
    state_size = fields[3]
    identifier = fields[4]
    frame_count = fields[5]
    block_size = fields[6]
    superblock_size = fields[7]

    if magic != REPLAY_MAGIC:
        raise ValueError(f"Bad magic: 0x{magic:08X} (expected 0x{REPLAY_MAGIC:08X})")

    return {
        "magic": magic,
        "version": version,
        "crc": crc,
        "state_size": state_size,
        "identifier": identifier,
        "frame_count": frame_count,
        "block_size": block_size,
        "superblock_size": superblock_size,
    }


def parse_key_event(data: bytes, offset: int) -> tuple[dict, int]:
    """Parse one bsv_key_data_t (10 bytes).

    Layout: [down:u8] [pad:u8] [mod:u16] [code:u32] [character:u16]
    """
    down = data[offset]
    code = struct.unpack_from("<I", data, offset + 4)[0]
    return {"down": bool(down), "code": code}, offset + 10


def parse_input_event(data: bytes, offset: int) -> tuple[dict, int]:
    """Parse one bsv_input_data_t (8 bytes)."""
    port, device, idx, _pad, btn_id, value = struct.unpack_from("<BBBBHh", data, offset)
    return {
        "port": port,
        "device": device,
        "idx": idx,
        "id": btn_id,
        "value": value,
    }, offset + 8


def skip_checkpoint(data: bytes, offset: int, header: dict, token: int) -> int:
    """Skip past checkpoint data embedded in a frame.

    This is a best-effort parser. Checkpoint format depends on the
    block_size / superblock_size config. For simple (non-incremental)
    checkpoints, it's just state_size bytes.
    """
    if token == ord('c'):
        # Old-style checkpoint: raw state data.
        return offset + header["state_size"]
    elif token == ord('C'):
        # New-style checkpoint2. Format:
        #   [compression: 1 byte] [encoding: 1 byte] [data: state_size bytes]
        return offset + 2 + header["state_size"]
    return offset


def parse_frames(data: bytes, start_offset: int, header: dict) -> list[dict]:
    """Parse all frames from the replay data."""
    offset = start_offset
    frames = []
    frame_num = 0

    while offset < len(data):
        frame = {"frame": frame_num, "key_events": [], "input_events": []}

        # backref (uint32)
        if offset + 4 > len(data):
            break
        offset += 4  # skip backref

        # key_event_count (uint8)
        if offset + 1 > len(data):
            break
        key_count = data[offset]
        offset += 1

        # key_events
        for _ in range(key_count):
            if offset + 10 > len(data):
                break
            kev, offset = parse_key_event(data, offset)
            frame["key_events"].append(kev)

        # input_event_count (uint16 LE)
        if offset + 2 > len(data):
            break
        input_count = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        # input_events
        for _ in range(input_count):
            if offset + 8 > len(data):
                break
            iev, offset = parse_input_event(data, offset)
            frame["input_events"].append(iev)

        # frame_token (uint8)
        if offset + 1 > len(data):
            break
        token = data[offset]
        offset += 1

        # Skip checkpoint data if present.
        if token in (ord('C'), ord('c')):
            try:
                offset = skip_checkpoint(data, offset, header, token)
            except Exception:
                print(f"Warning: failed to skip checkpoint at frame {frame_num}, "
                      f"offset {offset}. Stopping parse.", file=sys.stderr)
                break

        frames.append(frame)
        frame_num += 1

    return frames


def frames_to_godot_json(frames: list[dict], level: int, difficulty: int) -> dict:
    """Convert parsed frames to Godot input_replay.gd JSON format."""
    events = []
    # Track action state to emit only changes (press/release).
    action_state: dict[str, bool] = {}

    for frame in frames:
        frame_num = frame["frame"]

        # Process keyboard events.
        for kev in frame["key_events"]:
            action = RETROK_TO_ACTION.get(kev["code"])
            if action:
                pressed = kev["down"]
                if action_state.get(action) != pressed:
                    action_state[action] = pressed
                    events.append({
                        "frame": frame_num,
                        "action": action,
                        "pressed": pressed,
                    })

        # Process joypad events (port 0, device 1 = JOYPAD).
        for iev in frame["input_events"]:
            if iev["port"] == 0 and iev["device"] == 1:
                action = JOYPAD_TO_ACTION.get(iev["id"])
                if action:
                    pressed = iev["value"] != 0
                    if action_state.get(action) != pressed:
                        action_state[action] = pressed
                        events.append({
                            "frame": frame_num,
                            "action": action,
                            "pressed": pressed,
                        })

    return {
        "fps": 70,  # DOSBox native VGA refresh rate.
        "level": level,
        "difficulty": difficulty,
        "total_frames": len(frames),
        "events": events,
    }


def convert(replay_path: Path, output_path: Path | None = None,
            level: int = 1, difficulty: int = 0) -> Path:
    """Parse a RetroArch .replay file, emit Godot JSON. Returns output path."""
    replay_path = Path(replay_path)
    output_path = Path(output_path) if output_path else replay_path.with_suffix(".json")

    data = replay_path.read_bytes()
    print(f"Replay file: {replay_path} ({len(data)} bytes)")

    header = parse_header(data)
    print(f"Format version: {header['version']}")
    print(f"State size: {header['state_size']}")
    print(f"Frame count (header): {header['frame_count']}")

    offset = HEADER_SIZE
    if header["state_size"] > 0:
        offset += 2 + header["state_size"]
    else:
        offset += 2

    print(f"Frame data starts at offset: {offset}")

    frames = parse_frames(data, offset, header)
    print(f"Parsed {len(frames)} frames")

    key_frames = sum(1 for f in frames if f["key_events"])
    input_frames = sum(1 for f in frames if f["input_events"])
    print(f"Frames with keyboard events: {key_frames}")
    print(f"Frames with joypad events: {input_frames}")

    godot_json = frames_to_godot_json(frames, level, difficulty)
    print(f"Godot events: {len(godot_json['events'])}")

    with open(output_path, "w") as f:
        json.dump(godot_json, f, indent="\t")

    print(f"Written to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert RetroArch replay to Godot input JSON.")
    parser.add_argument("replay_file", type=Path)
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--difficulty", type=int, default=0)
    args = parser.parse_args()
    convert(args.replay_file, args.output, args.level, args.difficulty)


if __name__ == "__main__":
    main()
