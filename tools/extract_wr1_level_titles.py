"""Extract WR1's fifteen level-card string pairs from the EXE pointer table."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXE_SHA256 = 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f'
DATA_OFFSET = 0x24F50
TABLE_OFFSET = DATA_OFFSET + 0xBE


def extract(data):
    if hashlib.sha256(data).hexdigest() != EXE_SHA256:
        raise ValueError('Unsupported WR1.EXE')
    titles = []
    for index in range(15):
        strings = []
        for column in range(2):
            offset, segment = struct.unpack_from('<HH', data, TABLE_OFFSET + index * 8 + column * 4)
            if segment != 0x2255:
                raise ValueError('Unexpected title data segment')
            start = DATA_OFFSET + offset
            strings.append(data[start:data.index(b'\0', start)].decode('ascii'))
        if strings[0] != f'Level {index + 1}':
            raise ValueError('Unexpected level title order')
        titles.append({'heading': strings[0], 'name': strings[1]})
    return {'source_sha256': EXE_SHA256, 'table_file_offset': TABLE_OFFSET,
            'draw_routine_file_offset': 0x8361, 'titles': titles}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.exe.read_bytes()), indent=2) + '\n', encoding='utf-8')
