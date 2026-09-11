"""Build the fifth-pass slime probes from the existing controlled BSV2 replay.

Forward playback only. Retains the initial savestate and input records, rewrites
backrefs to zero, extends with the last neutral frame, and adds joypad R/Enter.
"""
import argparse
import struct
from pathlib import Path
from bsv_replay import frame_start, read_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--hit',action='store_true')
    args = parser.parse_args()
    data = args.source.read_bytes()
    header,frames = read_replay(data)
    if len(frames) != 770:
        parser.error('Expected the 770-frame exploration_controlled.replay')
    windows = [(620,624),(640,644),(850,854)] if args.hit else [(580,584),(600,604),(850,854)]
    result = bytearray(data[:frame_start(data,header)])
    for index in range(940):
        source = frames[min(index,len(frames)-1)]
        keys = source['key_events']
        inputs = [dict(e) for e in source['input_events']]
        if index >= 350:
            for event in inputs:
                if event['device']==1 and event['id']==9:
                    event['value'] = int(any(a <= index < b for a,b in windows))
        result += struct.pack('<IB',0,len(keys))
        for e in keys:
            result += struct.pack('<BBHII',e['down'],0,e['mod'],e['code'],e['character'])
        result += struct.pack('<H',len(inputs))
        for e in inputs:
            result += struct.pack('<BBBBHh',e['port'],e['device'],e['idx'],0,e['id'],e['value'])
        result += b'f'
    struct.pack_into('<I',result,24,940)
    read_replay(result) # Validate exact EOF and declared frame count before writing.
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result)


if __name__ == '__main__':
    main()
