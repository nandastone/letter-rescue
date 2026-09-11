"""Strict forward reader for RetroArch BSV version2, as used by build69a4f0e.

Primary layout: input/bsv/bsvmovie.{c,h} and input/input_driver.h at that commit.
Checkpoint codecs need not be decoded to read inputs; their stored lengths suffice.
"""
import struct

REPLAY_MAGIC = 0x42535632
HEADER_SIZE = 40


def require(data, offset, size, context):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError(f"Truncated {context} at byte {offset}: need {size}, have {max(0, len(data)-offset)}")


def parse_header(data):
    require(data, 0, HEADER_SIZE, "BSV2 header")
    values = struct.unpack_from("<IIIIQIIII", data)
    keys = ("magic", "version", "crc", "state_size", "identifier", "frame_count",
            "block_size", "superblock_size", "checkpoint_config")
    header = dict(zip(keys, values))
    if header["magic"] != REPLAY_MAGIC:
        raise ValueError(f"Bad BSV2 magic: {header['magic']:#x}")
    if header["version"] != 2:
        raise ValueError(f"Unsupported replay version {header['version']}; expected2")
    return header


def skip_checkpoint(data, offset, header=None, token=ord('C')):
    if token == ord('C'):
        require(data, offset, 14, "encoded checkpoint header")
        size = struct.unpack_from("<I", data, offset + 10)[0]
        offset += 14
    elif token == ord('c'):
        require(data, offset, 8, "raw checkpoint header")
        size = struct.unpack_from("<Q", data, offset)[0]
        offset += 8
    else:
        raise ValueError(f"Invalid checkpoint token {token:#x}")
    require(data, offset, size, "checkpoint payload")
    return offset + size


def frame_start(data, header):
    end = skip_checkpoint(data, HEADER_SIZE)
    if end - HEADER_SIZE != header["state_size"]:
        raise ValueError("Initial checkpoint length disagrees with header state_size")
    return end


def parse_key_event(data, offset):
    require(data, offset, 12, "keyboard event")
    down, _padding, mod, code, character = struct.unpack_from("<BBHII", data, offset)
    if down not in (0, 1):
        raise ValueError(f"Invalid keyboard down flag at byte {offset}: {down}")
    return {"down": bool(down), "mod": mod, "code": code, "character": character}, offset + 12


def parse_input_event(data, offset):
    require(data, offset, 8, "input event")
    port, device, idx, _padding, button, value = struct.unpack_from("<BBBBHh", data, offset)
    return {"port": port, "device": device, "idx": idx, "id": button, "value": value}, offset + 8


def parse_frames(data, start_offset, header):
    offset, frames = start_offset, []
    while offset < len(data):
        start = offset
        require(data, offset, 5, f"frame{len(frames)} prefix")
        backref, key_count = struct.unpack_from("<IB", data, offset)
        offset += 5
        keys, inputs = [], []
        for _ in range(key_count):
            event, offset = parse_key_event(data, offset)
            keys.append(event)
        require(data, offset, 2, "input count")
        count = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        for _ in range(count):
            event, offset = parse_input_event(data, offset)
            inputs.append(event)
        require(data, offset, 1, "frame token")
        token = data[offset]
        offset += 1
        if token in (ord('C'), ord('c')):
            offset = skip_checkpoint(data, offset, header, token)
        elif token != ord('f'):
            raise ValueError(f"Invalid frame token {token:#x} at byte {offset-1}, frame{len(frames)}")
        frames.append({"frame": len(frames), "key_events": keys, "input_events": inputs,
                       "backref": backref, "start": start, "end": offset, "token": chr(token)})
    if len(frames) != header["frame_count"]:
        raise ValueError(f"Frame count mismatch: header={header['frame_count']}, parsed={len(frames)}")
    return frames


def read_replay(data):
    header = parse_header(data)
    return header, parse_frames(data, frame_start(data, header), header)
