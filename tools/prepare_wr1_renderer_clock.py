"""Preserve renderer-to-admission experiments with one initial checkpoint.

Intermediate graphics/IRQ checkpoints are assertions, never replay inputs.
Changed keyboard inputs retain their external guest-cycle delivery contract.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from prepare_wr1_renderer_background import prepare as prepare_renderers
from prepare_wr1_idle_clock import prepare as prepare_waits
from prepare_wr1_hardware import FIELDS


def prepare(capture,trace,link_map,music):
    result=prepare_renderers(capture,trace,link_map,stage=0x1689)
    waits=prepare_waits(capture,trace,link_map,music,with_keyboard=True)
    by_start={c['start_cycle']:c for c in waits['cases']}
    renderers={c['start_cycle']:c for c in result.pop('cases')}
    result.update(music_file=music.as_posix(),music_sha256=hashlib.sha256(music.read_bytes()).hexdigest(),
                  scope='One checkpoint at renderer entry predicts rendering, display selection and the following ordinary idle wait. Later graphics, IRQ and admission observations are assertions only. Changed keys have externally supplied guest-cycle delivery times.',
                  cases=[],excluded=[])
    fields=FIELDS+('pic_interrupts','keyboard')
    contexts=('clock_state','music_driver','keyboard_game')
    begin=None
    for line in trace.read_bytes().splitlines():
        row=json.loads(line)
        if row.get('launch_call',0)<561:continue
        if row['event']=='graphics' and row['kind']=='renderer' and row['entry']:
            if begin is not None:raise ValueError('Unfinished renderer-to-wait interval')
            cycle=round(row['pic_ms']*27000)
            if row['renderer_tail']['death'] or row['renderer_post']['door_state']==2:
                result['excluded'].append({'cycle':cycle,'launch_call':row['launch_call'],
                                          'reason':'death or exit transition','tail':row['renderer_tail'],
                                          'post':row['renderer_post']})
                continue
            if row['return_ip']!=0x3da3-0x3360:raise ValueError('Renderer did not return to ordinary main loop')
            begin={'initial':{k:row[k] for k in fields+contexts},'post':row['renderer_post'],
                   'renderer':renderers[cycle],'display_state':row['display_state'],
                   'return_cs':row['return_cs'],'start_cycle':cycle,'start_call':row['launch_call']}
            begin['initial'].update(cpu_cs=row['cs'],cpu_ip=row['ip'],cpu_ax=row['ax'],cpu_flags=row['renderer_post']['cpu_flags'])
        elif begin is not None and row['event'] in ('keyboard_input','keyboard_irq','irq','music'):
            if row['event']=='keyboard_input' or (row['event']=='keyboard_irq' and row['ip']==0x12) or (row['event'] in ('irq','music') and row['ip']==0x232):
                raise ValueError('This fixture requires rendering/display without interrupt or external input preemption')
        elif begin is not None and row['event']=='graphics' and row['kind']=='display_page':
            key='display_entry' if row['entry'] else 'display_return'
            if key in begin:raise ValueError('Multiple display calls before ordinary idle wait')
            begin[key]={'hardware':{k:row[k] for k in FIELDS+('pic_interrupts',)},
                        'cycle':round(row['pic_ms']*27000),'state':row['display_state'],'args':row['args']}
        elif begin is not None and row['event']=='instruction' and row['ip']==0xd72:
            cycle=round(row['pic_ms']*27000)
            if cycle not in by_start:raise ValueError('Missing following idle admission')
            wait=by_start[cycle]
            wait.pop('initial') # Do not duplicate a future checkpoint as input.
            begin.update(wait=wait,update_done={'hardware':{k:row[k] for k in fields},'cycle':cycle},end_cycle=wait['end_cycle'])
            result['cases'].append(begin)
            begin=None
    if begin is not None or not result['cases']:raise ValueError('Incomplete renderer-to-admission capture')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','music','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,args.music)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} renderer-to-admission intervals; {len(fixture['excluded'])} explicit transition exclusions")
