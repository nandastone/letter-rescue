"""Reduce observed native fresh-map loads to a word/RNG regression fixture."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('replay', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.trace.read_text().splitlines()]
    keys = ['launch_call','pic_ms','rng','word_cursor','words','level_index',
            'word_offset','picture_offset','mystery_index']
    compact = lambda row: {key:row[key] for key in keys}
    initial, begin, loads = None, None, []
    for row in rows:
        if row.get('event') != 'lifecycle':
            continue
        if row['ip'] == 0xa3d:
            if begin is not None:
                raise ValueError('Nested reset entry')
            begin = row
        elif row['ip'] == 0xcb5:
            if begin is None:
                raise ValueError('Reset return without entry')
            if initial is None:
                initial = compact(row)
            else:
                if begin['word_cursor'] == row['word_cursor']:
                    raise ValueError('Expected a fresh map, not cached restart')
                loads.append({'begin':compact(begin),'end':compact(row)})
            begin = None
    if begin is not None or initial is None or len(loads) != 16:
        raise ValueError('Expected initial map and sixteen completed loads')
    if not any(load['end']['word_cursor'] < load['begin']['word_cursor'] for load in loads):
        raise ValueError('Probe did not cross EOF')
    args.output.write_text(json.dumps({
        'trace_sha256':hashlib.sha256(args.trace.read_bytes()).hexdigest(),
        'replay_sha256':hashlib.sha256(args.replay.read_bytes()).hexdigest(),
        'input':'Original Z+L selector alternating14 and1, sixteen loads; no guest memory edits.',
        'initial':initial,'loads':loads},indent=2)+'\n')


if __name__ == '__main__':
    main()
