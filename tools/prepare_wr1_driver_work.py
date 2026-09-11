"""Preserve original-binary instruction-path digests for independent runtime tests."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from wr1_driver_cpu import DriverCPU

ROOT = Path(__file__).resolve().parents[1]


def constructed_cases(initial):
    """Explicit source-level experiments, separate from native observed coverage."""
    base = copy.deepcopy(initial)
    base.update(rhythm=192,voices=[65535]*9,notes=[0]*9,programs=[3]*16)
    cases = []
    def add(label,midi,changes=None):
        state = copy.deepcopy(base)
        if changes:state.update(copy.deepcopy(changes))
        cases.append({'label':label,'midi':midi,'initial_opl':state})
    for rhythm in (192,224):
        for channel in (0,3,15):
            add(f'all-notes-off-{rhythm}-{channel}',{'status':176+channel,'data':[123,0]},
                {'rhythm':rhythm,'voices':[(c<<8)|3 for c in [0,3,15,3,15,0,15,3,0]],'notes':[0,40,41,42,43,44,45,46,47]})
    for bend in (0,63,128,255):
        for volume in (0,95,96,127):
            add(f'bend-{bend}-volume-{volume}',{'status':146,'data':[60,100]},
                {'bends':[bend]*16,'volumes':[volume]*16,'voices':[515]+[65535]*8})
    for label,notes in [('full',[48]*9),('recycle',[48]*8+[0])]:
        add(label,{'status':146,'data':[60,100]},{'voices':[1027]*9,'notes':notes})
    for status,velocity in [(130,100),(146,0)]:
        add(f'note-off-{status}',{'status':status,'data':[60,velocity]},
            {'voices':[515]*9,'notes':[50]*8+[48]})
    for controller,values in [(7,[0,95,127]),(103,[0,1,2]),(104,[0,63,128,255]),(105,[0,63,128,255])]:
        for value in values:
            add(f'controller-{controller}-{value}',{'status':178,'data':[controller,value]})
    for status in (208,224):add(f'ignored-{status}',{'status':status,'data':[64,64]})
    return cases


def prepare(executable):
    result = {'scope':'Original-binary work paths; native MIDI and OPL states. Intervals overlap.', 'recordings':[]}
    for name,limit in [('wr1_opl_ticks.json',561),('wr1_opl_startup_ticks.json',363),('wr1_opl_loop_ticks.json.gz',9281)]:
        raw = (ROOT/'testing/fixtures'/name).read_bytes()
        fixture = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
        cpu = DriverCPU(executable,(ROOT/fixture['music_file']).read_bytes(),fixture['initial_opl'])
        recording = {'source':name,'source_sha256':hashlib.sha256(raw).hexdigest(),
                     'last_tick':limit,'events':[]}
        for tick in fixture['ticks']:
            if tick['tick']>limit:break
            writes = []
            for midi in tick['events']:
                actual,cost = cpu.event(midi)
                encoded = json.dumps(cpu.timeline,separators=(',',':')).encode()
                recording['events'].append({'work_sha256':hashlib.sha256(encoded).hexdigest(),'instructions':cost})
                writes += actual
            if writes!=tick['writes']:raise ValueError(f"Original interpreter disagrees with native writes at {name}:{tick['tick']}")
        result['recordings'].append(recording)
    short = json.loads((ROOT/'testing/fixtures/wr1_opl_ticks.json').read_text())
    result['constructed_music_file'] = short['music_file']
    result['constructed_cases'] = constructed_cases(short['initial_opl'])
    for case in result['constructed_cases']:
        cpu = DriverCPU(executable,(ROOT/short['music_file']).read_bytes(),case['initial_opl'])
        case['writes'],case['instructions'] = cpu.event(case['midi'])
        case['work_sha256'] = hashlib.sha256(json.dumps(cpu.timeline,separators=(',',':')).encode()).hexdigest()
        case['expected_opl'] = cpu.snapshot()
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'testing/fixtures/wr1_driver_work.json.gz')
    args = parser.parse_args()
    args.output.write_bytes(gzip.compress(json.dumps(prepare(args.executable.read_bytes()),separators=(',',':')).encode(),mtime=0))
