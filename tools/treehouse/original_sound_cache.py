"""Read prepared resident sounds from an offline initial snapshot only."""
import struct
from memory_catalog import read_catalogs


def prepared_sounds(ram):
    # RAM-0 starts at physical 0x1860 in the pinned reference memory map.
    physical = bytes(0x1860) + ram
    ds = (0x323f0 + 0x1860) // 16
    result = []
    for catalog in read_catalogs(physical, ds):
        if catalog['archive'] not in ['digisnd', 'voices']:
            continue
        for entry in catalog['records']:
            if entry['tag'] != 'SND' or not entry['handle']:
                continue
            state, segment = struct.unpack_from('<HH', physical, ds*16+entry['handle'])
            if state & 0x200:
                raise ValueError('Prepared EMS sounds are outside this snapshot adapter')
            if state & 0x2000 and ((state & 15) or segment):
                result.append(f'{catalog["archive"]}:{entry["id"]}')
    return sorted(result)
