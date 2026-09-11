"""Preserve whole INT 63h experiments with one continuous music/voice state."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_hardware_reference import event_names
from wr1_music_reference import FIELDS as MUSIC_FIELDS


def prepare(capture,trace,link_map,music,start_call=561):
    source = json.loads(capture.read_text())
    raw = trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched trace')
    result = {k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names = event_names(link_map.read_text())
    result.update(link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),event_names=names,
                  music_file=music.as_posix(),music_sha256=hashlib.sha256(music.read_bytes()).hexdigest(),
                  scope='Continuous music/voice state, hardware initialized at each INT 63h entry. No observed future work or wait durations supplied.',cases=[])
    begin = previous = None
    rep = None
    rep_returns = {0x5c92:0x5c94,0x5ca0:0x5ca2,0x5caa:0x5cac,
                   0x5cb5:0x5cb7,0x602a:0x602c,0x6088:0x608a}
    for line in raw.splitlines():
        row = json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event'] in ('irq','music') and row['ip']==0x2d8:
            if begin is not None:raise ValueError('Unpaired INT 63h entry')
            begin = row
            music_state = {k:row['music_driver'][k] for k in MUSIC_FIELDS}
            if previous and (music_state!=previous['music'] or row['music_driver']['opl_state']!=previous['opl']):
                raise ValueError('Music or voice state changed outside the captured service calls')
            if not result['cases']:
                result.update(initial_music=music_state,initial_opl=row['music_driver']['opl_state'],dispatcher_use_dx=row['music_driver']['dispatcher_use_dx'])
                if 'external_timer' in row['music_driver']:result['external_timer'] = row['music_driver']['external_timer']
            if row['music_driver']['dispatcher_use_dx']!=result['dispatcher_use_dx']:
                raise ValueError('Dispatcher mode changed')
            if row['music_driver'].get('external_timer')!=result.get('external_timer'):
                raise ValueError('Timer ownership changed')
            if row['cycles_max']!=27000 or row['cycles_auto']:raise ValueError('Unsupported CPU configuration')
            for event in row['pic_queue']:
                if event['id'] not in names:raise ValueError('Unmapped callback')
            writes = []
        elif row['event']=='opl' and row['ip']==0x579e:
            if begin is None:raise ValueError('OPL write outside an interrupt')
            writes.append([row['ax']&255,row['ax']>>8])
        elif row['event']=='driver_work' and begin is not None:
            if row['ip'] in rep_returns:
                if rep is None:
                    rep,reentries = row,0
                elif row['ip']==rep['ip'] and row['cx']<=rep['cx']:
                    reentries += 1
                else:raise ValueError('Inconsistent REP re-entry')
            elif rep is not None and row['ip']==rep_returns[rep['ip']]:
                if row['cx']!=0:raise ValueError('REP did not exhaust its count')
                result.setdefault('repeat_memory_cases',[]).append({
                    'ip':rep['ip'],'count':rep['cx'],'reentries':reentries,
                    'initial':{k:rep[k] for k in FIELDS},'expected':{k:row[k] for k in FIELDS},
                    'start_cycle':round(rep['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000)})
                rep = None
        elif row['event'] in ('irq','music') and row['ip']==0x2dc:
            if begin is None:raise ValueError('Unpaired INT 63h return')
            previous = {'music':{k:row['music_driver'][k] for k in MUSIC_FIELDS},'opl':row['music_driver']['opl_state']}
            result['cases'].append({'initial':{k:begin[k] for k in FIELDS},'expected':{k:row[k] for k in FIELDS},
                                    'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                    'launch_call':begin['launch_call'],'writes':writes,**previous})
            begin = None
    if begin is not None or rep is not None or not result['cases']:raise ValueError('Incomplete INT 63h experiments')
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','music','output'):parser.add_argument(name,type=Path)
    args = parser.parse_args()
    fixture = prepare(args.capture,args.trace,args.link_map,args.music)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} complete INT 63h calls")
