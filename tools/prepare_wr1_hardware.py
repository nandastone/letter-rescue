"""Preserve independent OPL entry/return experiments with native hardware state."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from wr1_hardware_reference import event_names

FIELDS = ('pit','pic_queue','vga_timing','pic_ticks','cycle_left','cycles_remaining','pending_cycles')


def prepare(capture,trace,link_map,start_call=561):
    source = json.loads(capture.read_text())
    raw = trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched native trace')
    names = event_names(link_map.read_text())
    result = {k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    result.update(link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),event_names=names,
                  scope='Independent OPL calls, each initialized from its own native entry. No future events or return state supplied to the model.',cases=[])
    initial = None
    for line in raw.splitlines():
        row = json.loads(line)
        if row['event']!='opl' or row['launch_call']<start_call:
            continue
        if row['ip']==0x579e:
            if initial is not None or row['pending_cycles']!=0:
                raise ValueError('Invalid OPL entry boundary')
            initial = row
        elif row['ip']==0x57c3:
            if initial is None or initial['ax']!=row['ax']:
                raise ValueError('Missing or inconsistent OPL entry')
            for event in initial['pic_queue']:
                if event['id'] not in names:
                    raise ValueError('Link map lacks a queued hardware event')
            result['cases'].append(dict(initial={k:initial[k] for k in FIELDS},
                                        expected={k:row[k] for k in FIELDS},
                                        start_pic_ms=initial['pic_ms'],end_pic_ms=row['pic_ms'],
                                        launch_call=initial['launch_call'],register=initial['ax']&255,value=initial['ax']>>8,
                                        cycles=round((row['pic_ms']-initial['pic_ms'])*27000)))
            initial = None
    if initial is not None or not result['cases']:
        raise ValueError('Incomplete OPL experiment set')
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    fixture = prepare(args.capture,args.trace,args.link_map)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} independent OPL calls")
