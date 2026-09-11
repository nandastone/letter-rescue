"""Preserve complete, paired native IRQ / MIDI / OPL observations as a fixture."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from wr1_music_reference import FIELDS, PARAMETERS


def prepare(capture_path, trace_path, music_path, counter=560, end_counter=None):
    capture = json.loads(capture_path.read_text())
    if not capture['complete']:
        raise ValueError('Incomplete native capture')
    raw = trace_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if capture['instruction_trace_sha256'] != digest:
        raise ValueError('Trace hash disagrees with native capture')
    records = [json.loads(line) for line in raw.splitlines()]
    candidates = [i for i,r in enumerate(records) if r['event']=='frontend' and r['call']==counter+1]
    if len(candidates)!=1:
        raise ValueError('Expected one initial frontend state')
    index = candidates[0]
    initial = records[index]
    driver = initial['music_driver']
    result = {k:capture[k] for k in ('source_sha256','exe_sha256','core_sha256')}
    result.update(trace_sha256=digest,
                  music_file=music_path.as_posix(),music_sha256=hashlib.sha256(music_path.read_bytes()).hexdigest(),
                  initial_counter=counter,end_counter=end_counter,initial_pic_ms=initial['pic_ms'],
                  initial={k:driver[k] for k in FIELDS},initial_opl=driver['opl_state'],ticks=[])
    irq = event = operation = None
    found_end = end_counter is None
    for r in records[index+1:]:
        if end_counter is not None and r['event']=='frontend' and r['call']==end_counter+1:
            found_end = True
            break
        if r['event'] in ('irq','music') and r['ip']==0x2d8:
            if r['cycles_max']!=27000 or r['cycles_auto'] or r['decoder']!='DynX86':
                raise ValueError('Unsupported native CPU configuration')
            if irq is not None:
                raise ValueError('Missing IRQ return')
            irq = dict(tick=len(result['ticks'])+1,launch_call=r['launch_call'],pic_ms=r['pic_ms'],events=[],event_cycles=[],event_begin_cycles=[],event_end_cycles=[],writes=[],write_cycles=[])
        elif r['event']=='driver_event' and r['ip']==0x58f1:
            if irq is None or event is not None:
                raise ValueError('Unpaired or out-of-IRQ MIDI event')
            status = r['ax']&255
            event = {'status':status,'data':[r['bx']>>8,r['bx']&255][:PARAMETERS[(status>>4)-8]]}
            event_start,event_opl_cycles = r['pic_ms'],0
            irq['event_begin_cycles'].append(round(event_start*27000))
            irq['events'].append(event)
        elif r['event']=='driver_event' and r['ip']==0x599f:
            if event is None or operation is not None:
                raise ValueError('Missing MIDI entry or OPL return')
            irq['event_cycles'].append(round((r['pic_ms']-event_start)*27000)-event_opl_cycles)
            irq['event_end_cycles'].append(round(r['pic_ms']*27000))
            event = None
        elif r['event']=='opl' and r['ip']==0x579e:
            # CMF repeat resets the instrument bank inside the IRQ, outside
            # any MIDI event. Preserve those writes too; the model must derive them.
            if irq is None or operation is not None:
                raise ValueError('Unpaired OPL write')
            operation = r
            irq['writes'].append([r['ax']&255,r['ax']>>8])
        elif r['event']=='opl' and r['ip']==0x57c3:
            if operation is None or operation['ax']!=r['ax']:
                raise ValueError('Missing or inconsistent OPL entry')
            cycles = round((r['pic_ms']-operation['pic_ms'])*27000)
            irq['write_cycles'].append(cycles)
            if event is not None:
                event_opl_cycles += cycles
            operation = None
        elif r['event'] in ('irq','music') and r['ip']==0x2dc:
            if irq is None or event is not None or operation is not None:
                raise ValueError('Incomplete IRQ operations')
            driver = r['music_driver']
            irq.update(end_pic_ms=r['pic_ms'],state={k:driver[k] for k in FIELDS},opl_state=driver['opl_state'])
            result['ticks'].append(irq)
            irq = None
    if not found_end:
        raise ValueError('Requested final frontend boundary is missing')
    if irq is not None or event is not None or operation is not None:
        raise ValueError('Capture ends in an incomplete IRQ')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['capture','trace','music','output']:
        parser.add_argument(name,type=Path)
    parser.add_argument('--counter',type=int,default=560)
    parser.add_argument('--end-counter',type=int)
    args = parser.parse_args()
    fixture = prepare(args.capture,args.trace,args.music,args.counter,args.end_counter)
    if args.output.suffix=='.gz':
        args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    else:
        args.output.write_text(json.dumps(fixture,indent=2)+'\n')
    print(f"Preserved {len(fixture['ticks'])} complete IRQ ticks")
