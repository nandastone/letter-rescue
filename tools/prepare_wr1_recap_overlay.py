"""Separate scene and Benny drawing from the remaining recap overlay work.

This profile contains primitive workload estimates, never replay timestamps,
waits, admissions, frame numbers, or per-level corrections.
"""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path


def prepare(trace):
    regions = {'helper': [], 'panel': [], 'dissolve': []}
    active = None
    digest = hashlib.sha256()
    for line in trace.open('rb'):
        digest.update(line)
        if not line.startswith((b'{"event":"graphics"', b'{"event":"lifecycle"', b'{"event":"irq"')):
            continue
        # Only decode the fields needed outside active recap work regions.
        if active is None and not (b'"kind":"renderer"' in line and b'"entry":false' in line):
            continue
        row = json.loads(line)
        if row.get('kind') == 'renderer' and not row['entry']:
            active = {'start': row['pic_ms'], 'sprites': [], 'irqs': []}
        elif active is not None:
            if row.get('kind') == 'masked_sprite':
                active['sprites'].append(row['pic_ms'])
            if row['event'] == 'irq' and row['ip'] in (0x232, 0x2d7):
                active['irqs'].append((row['ip'], row['pic_ms']))
            if row['event'] == 'lifecycle' and row['ip'] in (0x1a82, 0x18b0):
                times = active['sprites']
                if len(times) != 4:
                    raise ValueError('Expected exactly two Benny blits after world rendering')
                if active['irqs']:
                    # Keep IRQ-free primitive measurements; service is modeled separately.
                    active = None
                    continue
                sprite_ms = times[1]-times[0] + times[3]-times[2]
                kind = 'dissolve' if row['ip'] == 0x18b0 else 'panel' if row['stack_args'][3] else 'helper'
                regions[kind].append((row['pic_ms']-active['start']-sprite_ms)/1000)
                active = None
    if any(not values for values in regions.values()):
        raise ValueError('Missing recap overlay measurements')
    return {'source_trace_sha256':digest.hexdigest(), 'cycles_per_ms':27000,
            'scope':'IRQ-free workload after world rendering, excluding two Benny blits. One common estimate per operation, independent of level and demo. Dissolve pixel writes and outlined panel drawing are estimates; world, text and Benny work come from recovered routines.',
            'work':{k:{'seconds':statistics.median(v),'minimum':min(v),'maximum':max(v),'samples':len(v)} for k,v in regions.items()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(prepare(args.trace),indent=2)+'\n')
