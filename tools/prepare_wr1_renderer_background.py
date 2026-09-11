"""Preserve the renderer background work from entry through the cache update.

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


def prepare(capture,trace,link_map,start_call=561,stage=0x671):
    source=json.loads(capture.read_text())
    raw=trace.read_bytes()
    if not source['complete'] or hashlib.sha256(raw).hexdigest()!=source['instruction_trace_sha256']:
        raise ValueError('Incomplete or mismatched renderer capture')
    result={k:source[k] for k in ('source_sha256','exe_sha256','core_sha256','instruction_trace_sha256')}
    names=event_names(link_map.read_text())
    result.update(event_names=names,link_map_sha256=hashlib.sha256(link_map.read_bytes()).hexdigest(),
                  scope=f'Independent renderer entry-to-stage {stage:04x} experiments. One entry checkpoint; later graphics calls and camera/picture/device state are expected results, not model inputs.',cases=[])
    fields=FIELDS+('pic_interrupts',)
    begin=None
    children=[]
    configuration_seen=False
    for line in raw.splitlines():
        row=json.loads(line)
        if row.get('launch_call',0)<start_call:continue
        if row['event'] in ('irq','music') and row['ip']==0x232:
            if row['cycles_max']!=27000 or row['cycles_auto']:raise ValueError('Unsupported CPU configuration')
            configuration_seen=True
        if row['event']=='graphics' and row['kind']=='renderer' and row['entry']:
            if begin is not None:raise ValueError('Unfinished renderer background')
            begin=row
            calls=[]
            children=[]
        elif begin is not None and row['event']=='graphics' and row['kind']!='renderer':
            if row['entry']:
                children.append(row)
            else:
                if not children:raise ValueError('Unpaired background graphics call')
                child=children.pop()
                if any(child[k]!=row[k] for k in ('kind','return_ip','return_cs')):raise ValueError('Unpaired background graphics call')
                if children:continue
                calls.append({'kind':child['kind'],'args':child['args'],'entry_cycle':round(child['pic_ms']*27000),
                              'return_cycle':round(row['pic_ms']*27000),'initial':{k:child[k] for k in fields},
                              'expected':{k:row[k] for k in fields}})
        elif begin is not None and row.get('kind')=='renderer' and row['ip']==stage and (row['event']=='graphics_stage' or (stage==0x1689 and row['event']=='graphics' and not row['entry'])):
            if children:raise ValueError('Background ends inside a primitive')
            if any(begin[k]!=row[k] for k in ('return_ip','return_cs')):raise ValueError('Renderer stack mismatch')
            if any(e['id'] not in names for e in begin['pic_queue']):raise ValueError('Unmapped callback')
            result['cases'].append({'initial':{k:begin[k] for k in fields},'expected':{k:row[k] for k in fields},
                                   'background':begin['renderer_background'],'initial_prefix':begin['renderer_prefix'],'prefix':row['renderer_prefix'],
                                   'graphics':{k:begin[k] for k in DETAILS+('graphics_flags','fill_state')},
                                   'expected_graphics_state':row['graphics_state'],'calls':calls,
                                   'start_cycle':round(begin['pic_ms']*27000),'end_cycle':round(row['pic_ms']*27000),
                                   'launch_call':begin['launch_call']})
            if 'renderer_tiles' in begin:
                result['cases'][-1].update(tiles=begin['renderer_tiles'],expected_tiles=row['renderer_tiles'])
            if 'renderer_doors' in begin:
                result['cases'][-1].update(doors=begin['renderer_doors'],expected_doors=row['renderer_doors'])
            for name in ('matching','player','actors','tail'):
                if 'renderer_'+name in begin:
                    result['cases'][-1].update({name:begin['renderer_'+name],'expected_'+name:row['renderer_'+name]})
            if 'actor_images' in begin:result['cases'][-1]['actor_images']=begin['actor_images']
            if 'text_state' in begin:result['cases'][-1]['graphics']['text_state']=begin['text_state']
            begin=None
    if begin is not None or children or not result['cases'] or not configuration_seen:
        raise ValueError('Incomplete renderer-background evidence')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map)
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} renderer backgrounds")
