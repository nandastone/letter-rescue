"""Preserve continuous idle waits and separately identify external input changes.

Each model experiment receives one initial checkpoint only. Later IRQ entries
and the next gameplay gate are expected results, never simulation inputs.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_hardware_reference import event_names
from wr1_music_reference import FIELDS as MUSIC_FIELDS
from wr1_irq_work import STATE_FIELDS

HARDWARE_FIELDS = FIELDS+('pic_interrupts',)


def prepare(capture,trace,link_map,music,start_call=561,with_keyboard=False):
    source=json.loads(capture.read_text())
    raw=trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched trace')
    names=event_names(link_map.read_text())
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  music_file=music.as_posix(),music_sha256=hashlib.sha256(music.read_bytes()).hexdigest(),
                  scope='One checkpoint per idle wait. Future button changes are recorded as unsupported external input, not clock corrections.',cases=[])
    hardware_fields=HARDWARE_FIELDS+('keyboard',) if with_keyboard else HARDWARE_FIELDS
    initial_fields=('cpu_cs','cpu_ip','cpu_ax','cpu_flags','clock_state','music_driver')
    if with_keyboard:
        initial_fields+=('keyboard_game',)
        result['scope']='One checkpoint per idle wait, including IRQ0/IRQ1 delivery. Changed keys are external replay inputs at their recorded guest-cycle delivery times. No future hardware or game state supplied.'
    begin=None
    previous_input=set()
    input_now=set()
    for line in raw.splitlines():
        row=json.loads(line)
        event=row['event']
        if event=='input':
            input_now.add(tuple(row[k] for k in ('port','device','index','id','value')))
        if event=='frontend':
            if begin is not None and input_now!=previous_input:
                changes.append({'call':row['call'],'before':sorted(previous_input),'after':sorted(input_now)})
            previous_input,input_now=input_now,set()
        call=row.get('launch_call',row.get('call',0))
        if call<start_call:continue
        starts=(event=='frontend' and call==start_call) or (event=='instruction' and row['ip']==0xd72)
        if starts:
            if begin is not None:raise ValueError('Idle start without admission')
            begin=copy.deepcopy(row)
            if event=='instruction':begin.update(cpu_cs=row['cs'],cpu_ip=row['ip'])
            else:begin['pending_cycles']=0
            if begin['music_driver']['external_timer']!=1:raise ValueError('Game does not own the timer')
            if any(e['id'] not in names for e in begin['pic_queue']):raise ValueError('Unmapped hardware callback')
            entries,changes,keyboard_entries,input_events=[],[],[],[]
        elif begin is not None and with_keyboard and event=='keyboard_input':
            # DOSBox Pure KBD_down/right, verified against keyboard.cpp.
            scans={85:80,86:77}
            if row['key'] not in scans:raise ValueError('Unsupported replay key mapping')
            input_events.append({'cycle':round(row['pic_ms']*27000),'key':row['key'],
                                 'scan':scans[row['key']],'pressed':row['pressed'],'extended':True})
        elif begin is not None and with_keyboard and event=='keyboard_irq' and row['ip']==0x12:
            keyboard_entries.append({'hardware':{k:row[k] for k in hardware_fields},'pic_cycle':round(row['pic_ms']*27000),
                                     'return_ip':row['return_ip'],'return_cs':row['return_cs'],
                                     'return_c':bool(row['return_flags']&1),'return_z':bool(row['return_flags']&64)})
        elif begin is not None and event in ('irq','music') and row['ip']==0x232:
            entries.append({'hardware':{k:row[k] for k in HARDWARE_FIELDS},'pic_cycle':round(row['pic_ms']*27000),
                            'return_ip':row['return_ip'],'return_cs':row['return_cs'],
                            'return_c':bool(row['return_flags']&1),'return_z':bool(row['return_flags']&64)})
        elif begin is not None and event=='instruction' and row['ip']==0x444:
            result['cases'].append({'initial':{k:begin[k] for k in hardware_fields+initial_fields},
                                   'start_call':begin.get('launch_call',begin.get('call')),'end_call':call,
                                   'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                   'expected':{k:row[k] for k in hardware_fields},'entries':entries,'input_changes':changes,
                                   'game':{k:row['clock_state'][k] for k in STATE_FIELDS},
                                   'music':{k:row['music_driver'][k] for k in MUSIC_FIELDS},'opl':row['music_driver']['opl_state']})
            if with_keyboard:
                result['cases'][-1].update(keyboard_entries=keyboard_entries,input_events=input_events,keyboard_game=row['keyboard_game'])
            begin=None
    # A completed update at the capture endpoint can start an unfinished wait;
    # preserve only waits whose admission was actually observed.
    if not result['cases']:raise ValueError('No complete idle waits')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','music','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--with-keyboard',action='store_true')
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,args.music,with_keyboard=args.with_keyboard)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} continuous waits; {sum(bool(c['input_changes']) for c in fixture['cases'])} contain external input changes")
