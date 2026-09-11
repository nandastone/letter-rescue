#!/usr/bin/env python3
"""Convert a validated RetroArch BSV2 replay to frame-boundary Godot inputs.

Uses DOSBox Pure Generic Keyboard Bindings on port0. Keyboard callbacks, polled
keyboard keys and joypad buttons remain independent input sources, combined by OR.
--start-frame trims native menu frames and carries held inputs into new frame0.
"""
import argparse
import hashlib
import json
from pathlib import Path
from bsv_replay import read_replay

RETROK_TO_ACTION = {276: "move_left", 275: "move_right", 273: "jump",
                    274: "move_down", 32: "use_slime", 13: "use_slime"}
JOYPAD_TO_ACTION = {4: "jump", 5: "move_down", 6: "move_left", 7: "move_right",
                    9: "use_slime", 3: "use_slime"}
ACTIONS = ("move_left", "move_right", "jump", "move_down", "use_slime")


def frame_action_states(frames):
    callbacks = {}
    for frame in frames:
        for event in frame["key_events"]:
            if event["code"] in RETROK_TO_ACTION:
                callbacks[event["code"]] = event["down"]
        # Polled values belong to this frame. An unrecorded query returns0 in RA.
        polled = {}
        for event in frame["input_events"]:
            if event["port"] != 0 or event["idx"] != 0:
                continue
            device, button, value = event["device"], event["id"], event["value"]
            if device not in (1, 3):
                continue
            identity = (device, button)
            if identity in polled and polled[identity] != value:
                raise ValueError(f"Conflicting intra-frame input samples at frame{frame['frame']}: {identity}")
            polled[identity] = value
        held = {RETROK_TO_ACTION[key] for key, down in callbacks.items() if down}
        for (device, button), value in polled.items():
            if device == 1 and button == 256:  # RETRO_DEVICE_ID_JOYPAD_MASK
                held.update(action for bit, action in JOYPAD_TO_ACTION.items() if value & (1 << bit))
            elif value:
                action = (JOYPAD_TO_ACTION if device == 1 else RETROK_TO_ACTION).get(button)
                if action:
                    held.add(action)
        yield {"frame": frame["frame"], "held": held}


def frames_to_godot_json(frames, level=1, difficulty=0, start_frame=0, end_frame=None):
    end_frame = len(frames) if end_frame is None else end_frame
    if not 0 <= start_frame < end_frame <= len(frames):
        raise ValueError("Expected0 <= start-frame < end-frame <= replay length")
    previous, events = set(), []
    for sample in frame_action_states(frames):
        frame = sample["frame"]
        if frame >= end_frame:
            break
        if frame < start_frame:
            continue
        held = sample["held"]
        for action in ACTIONS:
            if (action in held) != (action in previous):
                events.append({"frame": frame-start_frame, "action": action, "pressed": action in held})
        previous = held
    return {"fps": 70, "level": level, "difficulty": difficulty,
            "total_frames": end_frame-start_frame, "events": events,
            "source_start_frame": start_frame, "source_end_frame": end_frame,
            "input_mapping": "DOSBox Pure Generic Keyboard Bindings, port0; frame-boundary OR"}


def convert(replay_path, output_path=None, level=1, difficulty=0, start_frame=0, end_frame=None):
    replay_path = Path(replay_path)
    output_path = Path(output_path) if output_path else replay_path.with_suffix(".json")
    data = replay_path.read_bytes()
    header, frames = read_replay(data)
    result = frames_to_godot_json(frames, level, difficulty, start_frame, end_frame)
    result["source_sha256"] = hashlib.sha256(data).hexdigest()
    result["source_frame_count"] = header["frame_count"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(frames)} frames; converted [{start_frame}, {result['source_end_frame']}) "
          f"to {len(result['events'])} changes: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay_file", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--difficulty", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--end-frame", type=int)
    args = parser.parse_args()
    try:
        convert(args.replay_file, args.output, args.level, args.difficulty, args.start_frame, args.end_frame)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Replay conversion failed: {error}\n")


if __name__ == "__main__":
    main()
