"""Preserve the three demo timing windows as per-stage CPU-work experiments.

Movement, contacts and rendering each receive their own native entry state.
These diagnose instruction costs; they are not full gameplay replays from one
checkpoint and must never be loaded by the game's runtime.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys

from index_wr1_trace import window
from json_evidence import read

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'testing/output/python_packages'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16


def prepare(executable):
    binary = executable.read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != 'b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        raise ValueError('Unsupported original executable')
    instructions = {str(i.address):[i.mnemonic,i.address+i.size]
                    for a,b in [(0x3d7e,0x3dad),(0x409b,0x40d5),(0x50e8,0x5862),(0x23f5f,0x23f70)]
                    for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(binary[a:b],a)}
    cases = []
    sources = []
    for level, name, targets in [(6,'demo_level6_native_isolated',[131913.0]),
                                  (13,'demo_level13_native',[64211.0,88709.950629652])]:
        trace = Path(f'testing/output/{name}.jsonl')
        capture = read(trace.with_suffix('.json'))
        with trace.open('rb') as stream:
            trace_hash = hashlib.file_digest(stream,'sha256').hexdigest()
        if not capture['complete'] or trace_hash != capture['instruction_trace_sha256']:
            raise ValueError('Incomplete or changed native trace')
        replay = read(f'testing/fixtures/wr1_demo_level{level}_replay.json')
        sources.append({'level':level,'trace_sha256':trace_hash,'exe_sha256':capture['exe_sha256'],
                        'core_sha256':capture['core_sha256']})
        for target in targets:
            rows = list(window(trace,target-100,target+1,['instruction','graphics']))
            expected = max((r for r in rows if r['event']=='instruction' and r['ip']==0xd72 and r['pic_ms']<target),
                           key=lambda r:r['pic_ms'])
            start = max(r['pic_ms'] for r in rows if r['event']=='instruction' and r['ip']==0x444 and r['pic_ms']<expected['pic_ms'])
            current = [r for r in rows if start <= r['pic_ms'] <= expected['pic_ms']]
            next_admission = min((r for r in rows if r['event']=='instruction' and r['ip']==0x444 and r['pic_ms']>expected['pic_ms']),
                                 key=lambda r:r['pic_ms'])
            checkpoint = replay['original_music_clock'].copy()
            checkpoint['initial'] = dict(expected,cpu_cs=expected['cs'],cpu_ip=expected['ip'])
            cases.append({'level':level,'begin':current[0],
                          'contact':next(r for r in current if r.get('kind')=='contact' and r['entry']),
                          'world':next(r for r in current if r.get('kind')=='renderer' and r['entry']),
                          'expected':expected,'names':replay['original_music_clock']['event_names'],
                          'idle_checkpoint':checkpoint,'next_admission':next_admission})
    return {'scope':__doc__,'exe_sha256':digest,'sources':sources,'instructions':instructions,'cases':cases}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    args = parser.parse_args()
    output = Path('testing/fixtures/wr1_demo_update_work.json.gz')
    if output.exists():
        raise FileExistsError(output)
    result = prepare(args.executable)
    output.write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0))
    print(f'{len(result["cases"])} per-stage demo update work cases')
