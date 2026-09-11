"""Open Run demo through WR1's menu, then release all frontend controls."""
import argparse
from pathlib import Path
import struct

from bsv_replay import frame_start, read_replay

DEMO_ORDER = (4, 1, 10, 12, 14, 15, 2, 5, 8, 11, 9, 3, 6, 13, 7)


def build(data, count=11000, level=4):
    header, frames = read_replay(data)
    if len(frames) != 770 or count <= 500:
        raise ValueError('Require the controlled 770-frame source and room to launch the demo')
    if level not in DEMO_ORDER:
        raise ValueError('Demo level must be 1..15')
    selector = DEMO_ORDER.index(level) + 1
    result = bytearray(data[:frame_start(data, header)])
    for index in range(count):
        source = frames[min(index, len(frames) - 1)]
        keys = source['key_events'] if index < 350 else []
        inputs = [dict(e) for e in source['input_events']]
        if index >= 350:
            # Escape: menu. From Play, two Up presses select Run demo; Enter.
            buttons = {2: 400 <= index < 404, 4: 420 <= index < 424 or 430 <= index < 434,
                       3: 450 <= index < 454}
            for entry in inputs:
                entry['value'] = int(buttons.get(entry['id'], False)) if entry['port'] == 0 and entry['device'] == 1 else 0
            if level != 4:
                # Z+L opens the game's level selector. Run demo permutes the
                # selected gameplay index through its fixed DS:00A0 table.
                for entry in inputs:
                    entry['value'] = 0
                buttons = {2:550 <= index < 554, 4:570 <= index < 574 or 580 <= index < 584,
                           3:450 <= index < 454 or 600 <= index < 604}
                for digit in set(str(selector)):
                    pressed = any(char == digit and 430 + 6*i <= index < 433 + 6*i
                                  for i, char in enumerate(str(selector)))
                    if digit in '1234':
                        buttons[9 + int(digit)] = pressed
                    else:
                        # DOSBox checks polled physical-key state to release
                        # stale callback keys. Supply both halves of a held key.
                        inputs.append({'port':0,'device':3,'idx':0,'id':ord(digit),'value':int(pressed)})
                        for i, char in enumerate(str(selector)):
                            if char == digit and index in (430 + 6*i, 433 + 6*i):
                                keys.append({'down':index == 430 + 6*i,'mod':0,'code':ord(digit),'character':0})
                for entry in inputs:
                    if entry['port'] == 0 and entry['device'] == 1:
                        entry['value'] = int(buttons.get(entry['id'], False))
                inputs += [{'port':2,'device':1,'idx':0,'id':6,'value':int(410 <= index < 416)},
                           {'port':2,'device':5,'idx':1,'id':0,'value':32767 if 410 <= index < 416 else 0}]
        result += struct.pack('<IB', 0, len(keys))
        for e in keys:
            result += struct.pack('<BBHII', e['down'], 0, e['mod'], e['code'], e['character'])
        result += struct.pack('<H', len(inputs))
        for e in inputs:
            result += struct.pack('<BBBBHh', e['port'], e['device'], e['idx'], 0, e['id'], e['value'])
        result += b'f'
    struct.pack_into('<I', result, 24, count)
    read_replay(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--frames', type=int, default=11000)
    parser.add_argument('--level', type=int, default=4)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build(args.source.read_bytes(), args.frames, args.level))
