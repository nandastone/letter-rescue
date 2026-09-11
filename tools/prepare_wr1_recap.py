"""Preserve complete Benny lifecycle observations as a render-state reference."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(trace):
    rows = [json.loads(line) for line in trace.splitlines()]
    lifecycle = [r for r in rows if r['event'] == 'lifecycle']
    starts = [i for i, r in enumerate(lifecycle) if r['ip'] == 0x151c]
    if len(starts) != 1:
        raise ValueError('Expected exactly one recap entry')
    sequence = lifecycle[starts[0]:]
    end = next((i for i, r in enumerate(sequence) if r['ip'] == 0x194f), None)
    if end is None:
        raise ValueError('Recap has no return observation')
    sequence = sequence[:end + 1]
    renders = []
    order = []
    for row in sequence:
        if row['ip'] == 0x1a79:
            x, y, frame, panel, word = row['stack_args']
            if panel:
                order.append(word)
            draw = {'kind': 'helper', 'position': [x, y], 'frame': frame,
                    'order': len(order) - 1 if panel else -1, 'word_index': word if panel else -1}
        elif row['ip'] == 0x18b0:
            local = row['stack_locals']
            draw = {'kind': 'dissolve', 'position': [local[6], local[5]],
                    'frame': 6 + local[3], 'order': local[7], 'word_index': local[0]}
        else:
            continue
        renders.append({'draw': draw, 'state': row})
    if sorted(order) != list(range(7)) or sum(r['draw']['kind'] == 'dissolve' for r in renders) != 140:
        raise ValueError('Expected a complete unskipped seven-word recap')
    return {'source_trace_sha256': hashlib.sha256(trace).hexdigest(),
            'boundary': 'Benny helper and dissolution draws, before/after display call as identified by IP',
            'begin': sequence[0], 'completion_order': [order.index(i) for i in range(7)],
            'renders': renders, 'end': sequence[-1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(prepare(args.trace.read_bytes()), indent=2) + '\n')


if __name__ == '__main__':
    main()
