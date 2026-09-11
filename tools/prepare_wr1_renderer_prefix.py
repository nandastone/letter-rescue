"""Preserve the renderer opening from entry through drawing-page selection.

Future calls and endpoint state are expected results only. The intended model
must generate the calls from initial picture/camera state.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from prepare_wr1_graphics import DETAILS
from wr1_hardware_reference import event_names


def prepare(capture,trace,link_map,start_call=561):
    source=json.loads(capture.read_text())
    raw=trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched renderer capture')
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names=event_names(link_map.read_text())
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  scope='Independent renderer openings. One entry checkpoint; later graphics calls and camera/picture/device state are expected results, not model inputs.',cases=[])
    fields=FIELDS+('pic_interrupts',)
    begin=child=None
    configuration_seen=False
    for line in raw.splitlines():
        row=json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event'] in ('irq','music') and row['ip']==0x232:
            if row['cycles_max']!=27000 or row['cycles_auto']:raise ValueError('Unsupported CPU configuration')
            configuration_seen=True
        if row['event']=='graphics' and row['kind']=='renderer' and row['entry']:
            if begin is not None:raise ValueError('Unfinished renderer opening')
            begin=row
            calls=[]
        elif begin is not None and row['event']=='graphics' and row['kind']!='renderer':
            if row['entry']:
                if child is not None:raise ValueError('Unexpected nested primitive in opening')
                child=row
            else:
                if child is None or child['kind']!=row['kind']:raise ValueError('Unpaired opening graphics call')
                calls.append({'kind':child['kind'],'args':child['args'],'entry_cycle':round(child['pic_ms']*27000),
                              'return_cycle':round(row['pic_ms']*27000),'initial':{k:child[k] for k in fields},
                              'expected':{k:row[k] for k in fields}})
                child=None
        elif begin is not None and row['event']=='graphics_stage' and row['kind']=='renderer' and row['ip']==0x1a5:
            if child is not None:raise ValueError('Opening ends inside a primitive')
            if any(e['id'] not in names for e in begin['pic_queue']):raise ValueError('Unmapped callback')
            result['cases'].append({'initial':{k:begin[k] for k in fields},'expected':{k:row[k] for k in fields},
                                   'initial_prefix':begin['renderer_prefix'],'prefix':row['renderer_prefix'],
                                   'graphics':{k:begin[k] for k in DETAILS+('graphics_flags',)},
                                   'expected_graphics_state':row['graphics_state'],'calls':calls,
                                   'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                   'launch_call':begin['launch_call']})
            begin=None
    if begin is not None or child is not None or not result['cases'] or not configuration_seen:
        raise ValueError('Incomplete renderer-opening evidence')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} renderer openings")
