"""Replay native resource ownership operations in Godot from one initial fixture.

All 104 checkpoints compare complete near/far structures and active/static
handles. Requests and initial RAM are offline diagnostic inputs, not generated
game lifetimes. This does not establish a delivered payment or timing fix.
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path

from verify_godot_resource_heap import ROOT, digest, fixtures


def verify(godot, output, reference):
    output.mkdir(parents=True, exist_ok=False)
    trace, heaps, near = fixtures(reference, 'trace.json')
    assert len(heaps) == 104
    static_ids = set()
    for event in trace['events']:
        if event['label'].startswith('memory.catalog.pin'):
            identifier = event['bx'] if event['label'].endswith('.find') else event['bp']
            if 0 < identifier < near[0]['start']:
                static_ids.add(identifier)
    for heap, entry in zip(heaps, trace['heap']):
        data = (reference / entry['path']).read_bytes()
        for identifier in sorted(static_ids):
            state, segment = struct.unpack_from('<HH', data, 16 * entry['ss'] + identifier)
            heap['handles'].append(dict(id=identifier, state=state, segment=segment))
        heap['handles'].sort(key=lambda h: h['id'])
        for block in heap['blocks']:
            block.pop('payload', None)
    states = [dict(heap=h, near=n) for h, n in zip(heaps, near)]
    beginning, ending = trace['heap'][0]['milliseconds'], trace['heap'][-1]['milliseconds']
    stream = [dict(type='checkpoint', milliseconds=f['milliseconds'], index=i, requested=f['requested'])
              for i, f in enumerate(trace['heap'])]
    stream.extend(dict(e, type='event') for e in trace['events']
                  if beginning <= e['milliseconds'] <= ending and e['label'].startswith('memory.'))
    stream.sort(key=lambda e: e['milliseconds'])
    (output / 'fixture.json').write_text(json.dumps(dict(initial=states[0], stream=stream, static_ids=sorted(static_ids))), encoding='utf-8')
    with (output / 'godot.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([str(godot), '--headless', '--path', str(ROOT / 'treehouse-godot'),
                                 '--script', 'testing/check_resource_memory.gd', '--', str(output.resolve())],
                                stdout=log, stderr=subprocess.STDOUT, timeout=90)
    log = (output / 'godot.log').read_text(encoding='utf-8')
    if result.returncode or 'ERROR' in log:
        print(log[:6000])
        return False
    actual = json.loads((output / 'godot.json').read_text(encoding='utf-8'))
    checks = actual['checks']
    for i, (a, e) in enumerate(zip(actual['states'], states)):
        checks.append(dict(name=f'complete memory {i}', passed=a == e,
                           differences={} if a == e else dict(actual=a, expected=e)))
    passed = (len(actual['states']) == 104 and actual['allocations'] == 159 and actual['frees'] == 43
              and all(c['passed'] for c in checks))
    sources = ['scripts/resource_heap.gd', 'scripts/resource_near_heap.gd', 'scripts/resource_memory.gd', 'testing/check_resource_memory.gd']
    report = dict(passed=passed, scope=__doc__, checks=checks, allocations=actual['allocations'], frees=actual['frees'],
                  source_sha256={p: digest(ROOT / 'treehouse-godot' / p) for p in sources},
                  reference_sha256=digest(reference / 'trace.json'), verifier_sha256=digest(Path(__file__)),
                  full_game_parity=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=passed, checks=len(checks), allocations=actual['allocations'], frees=actual['frees'],
                          failures=[c['name'] for c in checks if not c['passed']])))
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, default=ROOT / 'testing/output/treehouse/nature-lifetime-d')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot, args.output, args.reference) else 1)
