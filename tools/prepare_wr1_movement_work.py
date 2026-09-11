"""Preserve native admission-to-contact movement work and live attributes."""
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
        raise ValueError('Incomplete or mismatched movement capture')
    names=event_names(link_map.read_text())
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  scope='One admission checkpoint and live attribute map predict movement to contact entry. Later state and hardware are expected results only; IRQ/input preemption and modal paths are explicit boundaries.',cases=[])
    fields=FIELDS+('pic_interrupts','keyboard')
    begin=None
    for line in raw.splitlines():
        row=json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event']=='instruction' and row['ip']==0x444:
            if begin is not None:raise ValueError('Unfinished movement interval')
            if row['cycles_max']!=27000 or row['cycles_auto'] or row['cpu_ax']!=0:raise ValueError('Unsupported admission configuration')
            if any(e['id'] not in names for e in row['pic_queue']):raise ValueError('Unmapped callback')
            begin=row
        elif begin is not None and row['event']=='instruction' and row['ip']==0xa1e:
            if begin['cs']!=row['cs'] or begin['bp']!=row['bp']:raise ValueError('Movement stack mismatch')
            result['cases'].append({'initial':{k:begin[k] for k in fields},'expected':{k:row[k] for k in fields},
                                   'movement':begin['movement'],'attributes':begin['movement_attributes'],
                                   'expected_movement':row['movement'],
                                   'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                   'launch_call':begin['launch_call']})
            begin=None
        elif begin is not None and (row['event']=='keyboard_input' or (row['event']=='keyboard_irq' and row['ip']==0x12) or (row['event'] in ('irq','music') and row['ip']==0x232)):
            raise ValueError('IRQ/input preemption inside movement is not supported by this fixture')
    if begin is not None or not result['cases']:raise ValueError('Incomplete movement evidence')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--start-call',type=int,default=561)
    args=parser.parse_args()
    f=prepare(args.capture,args.trace,args.link_map,args.start_call)
    args.output.write_bytes(gzip.compress(json.dumps(f,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(f['cases'])} movement intervals")
