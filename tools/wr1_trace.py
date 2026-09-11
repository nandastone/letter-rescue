"""Read WR1 state from a paused DOSBox Pure instance via RetroArch UDP commands.

Research tool: see testing/wr1_runtime_research.md. Never writes game memory.
--advance explicitly requests one frontend frame between samples, not one game tick.
Only use against a task-owned instance with network commands enabled.
"""

import argparse
import json
from pathlib import Path
import socket
import struct
import time

FIELDS = {
    "demo_mode": (0x146, "H"),
    "score": (0x186, "I"), "up": (0x190, "H"), "down": (0x192, "H"),
    "left": (0x194, "H"), "right": (0x196, "H"),
    "phase": (0x1C1, "H"), "sprite": (0x1C3, "H"),
    "books_collected": (0x15C, "H"), "book_count": (0x180, "H"),
    "source_x": (0x26F, "h"), "source_y": (0x271, "h"),
    "active_word": (0x32D, "B"), "active_index": (0x32E, "B"),
    "matched_count": (0x32F, "B"), "mistakes": (0x334, "H"),
    "background_frame": (0x41BE, "H"),
    "render_page": (0x807C, "H"), "display_page": (0x4879, "H"),
    "gruzzle_count": (0x237, "H"), "entity_timer": (0xF54, "H"),
    "timer": (0xF2E, "H"), "rng": (0x6378, "I"),
    "x": (0x662E, "h"), "y": (0x6630, "h"), "picture_offset": (0x6634, "h"),
    "gx": (0x83F6, "h"), "gy": (0x83F8, "h"),
    "camera_x": (0x8480, "h"), "camera_y": (0x8482, "h"),
    "threshold": (0x8E8F, "H"), "facing": (0x9E82, "h"),
    "word_offset": (0xA984, "h"),
    "entrance_timer": (0xC3DD, "h"),
}
REGIONS = [(0x146, 0x148), (0x15C, 0x1C5), (0x237, 0x239), (0x26F, 0x273), (0x32D, 0x336), (0xF2E, 0xF56), (0x41BE, 0x41C0), (0x4879, 0x487B), (0x6378, 0x664A), (0x807C, 0x807E),
           (0x83F6, 0x8484), (0x8E8F, 0x8E91), (0x9E82, 0x9E84), (0xA984, 0xA986)]
GRUZZLE_ARRAYS = {"gx": 0x977A, "gy": 0x9794, "type": 0x6636, "state": 0xC3C9,
                  "animation_index": 0x982C, "jump_phase": 0xAB0A, "move_timer": 0xF40}
REGIONS += [(start, start + 20) for start in GRUZZLE_ARRAYS.values()
            if not any(lo <= start and start + 20 <= hi for lo, hi in REGIONS)]
REGIONS.append((0xC3DD, 0xC3DF))


class Reader:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(("127.0.0.1", port))
        self.socket.settimeout(2)

    def command(self, text, reply=True):
        self.socket.send(text.encode("ascii"))
        if reply:
            return self.socket.recv(65507).decode("ascii").strip()

    def read(self, address, count):
        response = self.command(f"READ_CORE_MEMORY {address:X} {count}")
        parts = response.split()
        if len(parts) < 3 or parts[0] != "READ_CORE_MEMORY" or parts[2] == "-1":
            raise RuntimeError(response)
        if int(parts[1], 16) != address:
            raise RuntimeError("Response address differs from request")
        result = bytes.fromhex(" ".join(parts[2:]))
        if len(result) != count:
            raise RuntimeError(f"Short memory response: {len(result)} != {count}")
        return result

    def require_paused(self):
        status = self.command("GET_STATUS")
        if not status.startswith("GET_STATUS PAUSED "):
            raise RuntimeError(f"Pause the task-owned original first: {status}")

    def music_prefix(self, ds_base):
        """Read immutable loaded CMF bytes, independently of future playback."""
        # The core exposes OS memory at 0x100000 and moves game RAM to zero.
        # Relate the live INT 63h segment to the independently located EXE image.
        _offset, segment = struct.unpack('<HH', self.read(0x100000 + 0x63 * 4, 4))
        driver = ds_base - 0x22550 + (0x19580 - 0x2a00)
        physical_bias = (segment << 4) - driver
        if self.read(driver + 0x4a80, 2) != b'\xda\x60':
            return None
        segment, offset = struct.unpack('<HH', self.read(driver + 0x85c, 4))
        prefix = self.read((segment << 4) + offset - physical_bias, 64)
        return list(prefix) if prefix.startswith(b'CTMF') else None

    def find_ds(self, executable):
        # These three code blocks have no relocatable operands in their prefixes.
        ram = b"".join(self.read(i, 4096) for i in range(0, 512 * 1024, 4096))
        bases = []
        for offset in (0x3C14, 0x37C5, 0xAC27):
            signature = executable[offset:offset + 32]
            if len(signature) != 32:
                raise RuntimeError("Executable is too short")
            match = ram.find(signature)
            if match < 0 or ram.find(signature, match + 1) >= 0:
                raise RuntimeError(f"Nonunique/missing executable signature at {offset:#x}")
            bases.append(match - (offset - 0x2A00))
        if len(set(bases)) != 1:
            raise RuntimeError(f"Inconsistent executable mapping: {bases}")
        return bases[0] + 0x22550

    def snapshot(self, base):
        self.require_paused()
        previous = None
        for attempt in range(6):
            chunks = [self.read(base + start, end - start) for start, end in REGIONS]
            if chunks == previous:
                break
            previous = chunks
            time.sleep(.03)
        else:
            raise RuntimeError("Memory did not stabilize across consecutive paused reads")
        row = {}
        for name, (offset, fmt) in FIELDS.items():
            index = next(i for i, (start, end) in enumerate(REGIONS)
                         if start <= offset and offset + struct.calcsize(fmt) <= end)
            row[name] = struct.unpack_from("<" + fmt, chunks[index], offset - REGIONS[index][0])[0]
        row["world_x"] = row["x"] + 8 * row["camera_x"]
        row["world_y"] = row["y"] + 8 * row["camera_y"]
        actors = {}
        for name, offset in GRUZZLE_ARRAYS.items():
            index = next(i for i, (lo, hi) in enumerate(REGIONS) if lo <= offset and offset + 20 <= hi)
            actors[name] = struct.unpack_from('<10h', chunks[index], offset - REGIONS[index][0])
        row["gruzzles"] = [{name: values[i] for name, values in actors.items()}
                            for i in range(min(row["gruzzle_count"], 10))]
        row["read_passes"] = attempt + 1
        replay = self.command("GET_CONFIG_PARAM active_replay").split()
        if len(replay) == 5 and replay[:2] == ["GET_CONFIG_PARAM", "active_replay"]:
            row["replay_id"] = int(replay[2])
            row["replay_flags"] = int(replay[3])
            row["replay_frame"] = int(replay[4])
        return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=55445)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--advance", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.samples <= 10000 or not 1 <= args.port <= 65535:
        parser.error("Samples must be 1..10000 and port 1..65535")
    exe = args.exe.read_bytes()
    import hashlib
    digest = hashlib.sha256(exe).hexdigest()
    if digest != "b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f":
        parser.error("This address map only supports the researched WR1.EXE hash")
    reader = Reader(args.port)
    try:
        reader.require_paused()
        version = reader.command("VERSION")
        base = reader.find_ds(exe)
        rows = []
        for i in range(args.samples):
            if args.advance:
                reader.command("FRAMEADVANCE", reply=False)
                time.sleep(.05)
            row = reader.snapshot(base)
            if args.advance and rows and "replay_frame" in row and "replay_frame" in rows[-1]:
                if row["replay_id"] != rows[-1]["replay_id"] or row["replay_frame"] != rows[-1]["replay_frame"] + 1:
                    raise RuntimeError("Replay did not advance by exactly one recorded frame")
            row["sample"] = i
            rows.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"retroarch": version, "exe_sha256": digest,
            "mapped_ds_base": base, "advance_per_sample": args.advance,
            "samples": rows}, indent=2), encoding="utf-8")
        print(f"Saved {len(rows)} stable snapshots; mapped DS base {base:#x}; {args.output}")
    finally:
        reader.socket.close()


if __name__ == "__main__":
    main()
