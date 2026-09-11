"""Preserve whole MIDI-call experiments and executable-derived instruction work."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_driver_cpu import DriverCPU
from wr1_hardware_reference import event_names


def prepare(capture,trace,link_map,executable,music):
    source = json.loads(capture.read_text())
    raw = trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched capture')
    rows = [json.loads(line) for line in raw.splitlines()]
    origin = next(i for i,r in enumerate(rows) if r['event']=='frontend' and r['call']==561)
    initial_opl = rows[origin]['music_driver']['opl_state']
    cpu = DriverCPU(executable.read_bytes(),music.read_bytes(),initial_opl)
    result = {k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    result.update(link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),event_names=event_names(link_map.read_text()),
                  initial_opl=initial_opl,music_file=music.as_posix(),music_sha256=hashlib.sha256(music.read_bytes()).hexdigest(),
                  scope='Per-MIDI native hardware initialization; one initial voice state. Work is derived from executable instructions, not recorded elapsed time.',cases=[])
    start = None
    for row in rows[origin+1:]:
        if row['event']=='driver_event' and row['ip']==0x58f1:
            if start is not None or row['pending_cycles']:
                raise ValueError('Invalid MIDI entry')
            start = row
            midi = dict(status=row['ax']&255,data=[row['bx']>>8,row['bx']&255])
            writes,count = cpu.event(midi)
            native_writes = []
        elif row['event']=='opl' and row['ip']==0x579e:
            if start is None:
                raise ValueError('OPL write outside a MIDI call')
            native_writes.append([row['ax']&255,row['ax']>>8])
        elif row['event']=='driver_event' and row['ip']==0x599f:
            if start is None or writes!=native_writes:
                raise ValueError('Missing MIDI call or incorrect executable-derived register output')
            result['cases'].append(dict(midi=midi,work=cpu.timeline,writes=native_writes,instructions=count,
                                        initial={k:start[k] for k in FIELDS},expected={k:row[k] for k in FIELDS},
                                        start_cycle=round(start['pic_ms']*27000),end_cycle=round(row['pic_ms']*27000)))
            start = None
    if start is not None or not result['cases']:
        raise ValueError('Incomplete MIDI experiments')
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','executable','music','output'):
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    fixture = prepare(args.capture,args.trace,args.link_map,args.executable,args.music)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} whole MIDI-call experiments")
