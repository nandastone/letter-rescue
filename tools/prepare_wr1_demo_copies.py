"""Keep native demo HUD copies as independent graphics regression evidence."""
import gzip
import hashlib
import json
from pathlib import Path
from index_wr1_trace import window


def prepare():
    cases = {}
    sources = []
    for level, name, spans in [(6, 'demo_level6_native_isolated', [(130000,132000)]),
                               (13, 'demo_level13_native', [(10000,12000),(60000,65000),(88000,90000)])]:
        trace = Path(f'testing/output/{name}.jsonl')
        capture = json.loads(trace.with_suffix('.json').read_text())
        with trace.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if not capture['complete'] or digest != capture['instruction_trace_sha256']:
            raise ValueError('Incomplete or changed native capture')
        sources.append({'level':level,'trace_sha256':digest,'exe_sha256':capture['exe_sha256'],
                        'core_sha256':capture['core_sha256'],'windows_ms':spans})
        entry = None
        for start, end in spans:
            for row in window(trace,start,end,['graphics']):
                if row.get('kind') != 'copy_rect':
                    continue
                if row['entry']:
                    entry = row
                elif entry is not None:
                    a = entry['args']
                    if (a[2] % 8 or a[7] % 8 or (a[5]-a[7]+1) % 8) and entry['clock_state'] == row['clock_state']:
                        cases.setdefault(tuple(a),{'level':level,'entry':entry,'expected':row})
                    entry = None
    replay = json.loads(Path('testing/fixtures/wr1_demo_level13_replay.json').read_text())
    return {'scope':'Unique unaligned EGA copies in native demo windows. Expected returns are test evidence only.',
            'sources':sources,'event_names':replay['original_music_clock']['event_names'],'cases':list(cases.values())}


if __name__ == '__main__':
    result = prepare()
    output = Path('testing/fixtures/wr1_demo_hud_copies.json.gz')
    if output.exists():
        raise FileExistsError(output)
    output.write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0))
    print(f'{len(result["cases"])} native demo HUD copies')
