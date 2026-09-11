"""Decode the input bytes consumed by WR1.EXE at file 3727..379C.

One byte per admitted main update. Bit 0x20 ends playback before that update;
bytes after the first terminator are not played. No positions or outcomes.
"""
import argparse
import hashlib
import json
from pathlib import Path

BITS = {'up': 1, 'down': 2, 'right': 4, 'left': 8, 'slime_request': 16}


def decode(data):
    if not data or len(data) > 4000:
        raise ValueError('Demo must fit the native 4000-byte read buffer')
    inputs = []
    for index, value in enumerate(data):
        if value & 0x20:
            return {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                    'updates': index, 'terminator_offset': index,
                    'trailing_bytes': len(data) - index - 1,
                    'inputs': inputs}
        if value & 0xc0:
            raise ValueError(f'Unsupported input bits at byte {index}: {value:#x}')
        inputs.append({key: bool(value & bit) for key, bit in BITS.items()})
    raise ValueError('Demo has no stop marker; native playback would read beyond this file')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = decode(args.source.read_bytes())
    result['source_file'] = args.source.name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}))


if __name__ == '__main__':
    main()
