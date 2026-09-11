"""Preserve paired original graphics calls and ordinary-update timing profiles.

This is measurement evidence for recovering work, not a runtime duration table.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_hardware import FIELDS
from wr1_hardware_reference import event_names

STAGES={0x444:'admission',0xa1e:'movement_done',0xa23:'contacts_done',
        0xa39:'entities_start',0xa3e:'entities_done',0xa43:'renderer_done',
        0xd44:'display_done',0xd72:'update_done'}
SEGMENTS={'renderer':0x812,'copy_rect':0x10ed,'masked_sprite':0x13ae,
          'draw_page':0xc9d,'display_page':0x14c0,'fill_style':0xc9d,'fill_rect':0xc6e,'fill_raw':0xa43,
          'contact':0x97a,'text_color':0xc9d,'text_background':0xc9d,'text_cursor':0xb18,
          'text_string':0xd86,'text_font':0xd86,'string_length':0x1fa6}
DETAILS=('args','graphics_state','device_handle','device_slot','device_record','device_descriptor')


def prepare(capture,trace,link_map,start_call=561):
    source=json.loads(capture.read_text())
    raw=trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched graphics capture')
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names=event_names(link_map.read_text())
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  scope='Measured graphics entry/return experiments and update stages. Durations include intervening interrupts; not a predictive runtime model.',
                  cases=[],updates=[])
    stack=[]
    update=None
    update_case_start=0
    fields=FIELDS+('pic_interrupts',)
    for line in raw.splitlines():
        row=json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event']=='instruction' and row['ip'] in STAGES:
            if row['ip']==0x444:
                if update is not None or stack:raise ValueError('Unfinished update before next admission')
                update={'start_call':row['launch_call'],'stages':{},'cases':[]}
                update_case_start=len(result['cases'])
            if update is None:continue
            update['stages'][STAGES[row['ip']]]=round(row['pic_ms']*27000)
            if row['ip']==0xd72:
                if stack:raise ValueError('Graphics call did not return before update completion')
                update['end_call']=row['launch_call']
                result['updates'].append(update)
                update=None
        elif update is not None and row['event']=='graphics':
            if row['entry']:
                stack.append(row)
            else:
                if not stack:raise ValueError('Graphics return without entry')
                begin=stack.pop()
                for key in ('kind','return_ip','return_cs'):
                    if begin[key]!=row[key]:raise ValueError(f'Graphics stack mismatch: {key}')
                if any(e['id'] not in names for e in begin['pic_queue']):raise ValueError('Unknown callback')
                case={'kind':row['kind'],'initial':{k:begin[k] for k in fields},'expected':{k:row[k] for k in fields},
                      'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                      'entry_file':0x2a00+16*SEGMENTS[row['kind']]+begin['ip'],
                      'return_file':0x2a00+16*SEGMENTS[row['kind']]+row['ip'],
                      'return_ip':begin['return_ip'],'return_cs':begin['return_cs'],'result_ax':row['ax'],
                      'expected_graphics_state':row['graphics_state'],
                      'expected_args':row['args'],
                      'launch_call':begin['launch_call'],**{k:begin[k] for k in DETAILS}}
                if 'graphics_flags' in begin:case['graphics_flags']=begin['graphics_flags']
                for name in ('text_state','text_bytes','contact','contact_attributes'):
                    if name in begin:
                        case[name]=begin[name]
                        case['expected_'+name]=row[name]
                if 'fill_state' in begin:
                    case['fill_state']=begin['fill_state']
                    case['expected_fill_state']=row['fill_state']
                if 'image_header' in begin:
                    case['image_header']=begin['image_header']
                    case['expected_image_header']=row['image_header']
                if 'display_state' in begin:
                    case['display_state']=begin['display_state']
                    case['expected_display_state']=row['display_state']
                if 'clock_state' in begin:
                    for name in ('clock_state','music_driver','keyboard_game','keyboard'):
                        case[name]=begin[name]
                        case['expected_'+name]=row[name]
                update['cases'].append(len(result['cases']))
                result['cases'].append(case)
    if update is not None:
        result['incomplete_tail']={'start_call':update['start_call'],'stages':update['stages'],
                                   'open_calls':[r['kind'] for r in stack]}
        del result['cases'][update_case_start:]
    elif stack:raise ValueError('Open graphics calls outside a measured update')
    if not result['cases']:raise ValueError('No graphics measurements')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--start-call',type=int,default=561)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,args.start_call)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} graphics calls across {len(fixture['updates'])} complete updates")
