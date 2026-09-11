"""Measure drawing work between native routine boundaries, independent of waits."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def prepare(raw):
    rows = [json.loads(line) for line in raw.splitlines()]
    rows = [r for r in rows if r.get('event') == 'lifecycle']
    start = next(i for i,r in enumerate(rows) if r['ip'] == 0x151c)
    end = next(i for i in range(start,len(rows)) if rows[i]['ip'] == 0x194f)
    rows = rows[start:end+1]
    if any(r['cycles_max'] != 27000 or r['cycles_auto'] for r in rows):
        raise ValueError('Expected fixed27000 DOSBox cycles/ms')
    samples = {key:[] for key in ('helper','panel','transfer','dissolve')}
    pairs = {'helper':(0x197d,0x1a82), 'transfer':(0x1697,0x1789), 'dissolve':(0x17dd,0x18b0)}
    observations = []
    for kind,(entry,leave) in pairs.items():
        active = None
        for row in rows:
            if row['ip'] == entry:
                if active is not None:
                    raise ValueError('Nested work region')
                active = row
            elif row['ip'] == leave and active is not None:
                name = 'panel' if kind == 'helper' and active['stack_args'][3] else kind
                duration = (row['pic_ms']-active['pic_ms']) / 1000
                samples[name].append(duration)
                observations.append({'kind':name,'entry_ip':entry,'return_ip':leave,
                    'begin_ms':active['pic_ms'],'end_ms':row['pic_ms'],'seconds':duration})
                active = None
        if active is not None:
            raise ValueError('Incomplete work region')
    if {k:len(v) for k,v in samples.items()} != {'helper':33,'panel':7,'transfer':7,'dissolve':140}:
        raise ValueError('Expected complete seven-word recap')
    return {'source_trace_sha256':hashlib.sha256(raw).hexdigest(),
        'cycles_per_ms':27000,
        'scope':'Median drawing-work estimate for this DOSBox configuration; no input frames or future update schedule.',
        'work':{k:{'seconds':statistics.median(v),'minimum':min(v),'maximum':max(v),'samples':len(v)} for k,v in samples.items()},
        'observations':observations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('profile',type=Path)
    parser.add_argument('evidence',type=Path)
    args = parser.parse_args()
    result = prepare(args.trace.read_bytes())
    args.evidence.write_text(json.dumps(result,indent=2)+'\n')
    result.pop('observations')
    args.profile.write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
