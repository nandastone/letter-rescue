"""Preserve complete timer-body observations, from the timer increment to IRET."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_hardware_reference import event_names
from wr1_music_reference import FIELDS as MUSIC_FIELDS
from wr1_irq_work import STATE_FIELDS

ENTRY_FIELDS = STATE_FIELDS+('speaker_entry','speaker_next','bios_code','int1c_code','bios_handler','int1c_handler')


def prepare(capture,trace,link_map,music,start_call=561,max_cases=None):
    if max_cases is not None and max_cases<1:raise ValueError('max_cases must be positive')
    source = json.loads(capture.read_text())
    raw = trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched trace')
    result = {k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names = event_names(link_map.read_text())
    hardware_fields = FIELDS+('pic_interrupts',)
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  music_file=music.as_posix(),music_sha256=hashlib.sha256(music.read_bytes()).hexdigest(),
                  scope='Continuous music/voice state; game/speaker and hardware state initialized at each IRQ body entry. Ends before IRET.',cases=[])
    begin = previous = None
    for line in raw.splitlines():
        row = json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event'] in ('irq','music') and row['ip']==0x232:
            if begin is not None:raise ValueError('Unpaired IRQ body')
            begin = row
            current = {k:row['music_driver'][k] for k in MUSIC_FIELDS}
            if previous and (current!=previous['music'] or row['music_driver']['opl_state']!=previous['opl']):
                raise ValueError('Music/voice state changed outside an IRQ')
            if not result['cases']:
                result.update(initial_music=current,initial_opl=row['music_driver']['opl_state'],
                              dispatcher_use_dx=row['music_driver']['dispatcher_use_dx'],external_timer=row['music_driver']['external_timer'])
            for key in ('dispatcher_use_dx','external_timer'):
                if row['music_driver'][key]!=result[key]:raise ValueError('Driver configuration changed')
            if row['cycles_max']!=27000 or row['cycles_auto']:raise ValueError('Unsupported CPU configuration')
            if any(e['id'] not in names for e in row['pic_queue']):raise ValueError('Unmapped event')
            writes=[]
        elif row['event']=='opl' and row['ip']==0x579e:
            if begin is None:raise ValueError('OPL write outside paired IRQ')
            writes.append([row['ax']&255,row['ax']>>8])
        elif row['event'] in ('irq','music') and row['ip']==0x313:
            if begin is None:raise ValueError('Unpaired IRQ return')
            previous = {'music':{k:row['music_driver'][k] for k in MUSIC_FIELDS},'opl':row['music_driver']['opl_state']}
            result['cases'].append({'initial':{k:begin[k] for k in hardware_fields},'expected':{k:row[k] for k in hardware_fields},
                                    'initial_game':{k:begin[k] for k in ENTRY_FIELDS},'expected_game':{k:row[k] for k in STATE_FIELDS},
                                    'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                    'launch_call':begin['launch_call'],'writes':writes,**previous})
            begin = None
            if max_cases is not None and len(result['cases'])>=max_cases:break
    if begin is not None or not result['cases']:raise ValueError('Incomplete IRQ experiment set')
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','music','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--max-cases',type=int)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,args.music,max_cases=args.max_cases)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} complete timer bodies")
