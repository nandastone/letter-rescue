"""Preserve native keyboard-handler entry/return pairs with controller state."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_hardware_reference import event_names


def prepare(capture,trace,link_map,start_call=561):
    source=json.loads(capture.read_text())
    raw=trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched native trace')
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names=event_names(link_map.read_text())
    fields=FIELDS+('pic_interrupts','keyboard')
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  scope='Independent IRQ1 bodies from before IN AL,60h through before IRET. Full controller state initialized once per body.',cases=[])
    begin=None
    for line in raw.splitlines():
        row=json.loads(line)
        if row['event']!='keyboard_irq' or row['launch_call']<start_call:continue
        if row['ip']==0x12:
            if begin is not None:raise ValueError('Unpaired keyboard entry')
            begin=row
        elif row['ip']==0x24f:
            if begin is None:raise ValueError('Keyboard return without entry')
            result['cases'].append({'initial':{k:begin[k] for k in fields},'expected':{k:row[k] for k in fields},
                                   'initial_game':begin['keyboard_game'],'game':row['keyboard_game'],
                                   'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                   'launch_call':begin['launch_call']})
            begin=None
    if begin is not None or not result['cases']:raise ValueError('Incomplete keyboard experiment set')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} keyboard interrupt bodies")
