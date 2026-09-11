"""Extract the embedded AdLib driver's immutable tables from WR1.EXE."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def extract(executable):
    data = Path(executable).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        raise ValueError('Unsupported WR1 executable')
    base = 0x19580
    result = {'exe_sha256': digest, 'driver_file_base': base}
    for name, offset, count in [('modulators',0x762,9),('carriers',0x76b,9),
                                ('bend_steps',0x774,13),('percussion',0x6af,34)]:
        result[name] = list(data[base+offset:base+offset+count])
    result['frequencies'] = list(struct.unpack_from('<12H',data,base+0x74a))
    result['default_instruments'] = [list(data[base+0x12f+11*i:base+0x12f+11*(i+1)]) for i in range(128)]
    result['rhythm_registers'] = []
    cursor = base+0x6d1
    while data[cursor:cursor+2] != b'\xff\xff':
        # LODSW / XCHG AL,AH: the stored pair is value, register.
        result['rhythm_registers'].append(list(reversed(data[cursor:cursor+2])))
        cursor += 2
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--output',type=Path,default=Path('assets/audio/original/driver_tables.json'))
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.executable),indent=2)+'\n')
