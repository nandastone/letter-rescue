"""Compare Godot resource allocation with pinned native operation fixtures.

Initial heap RAM and the near-heap request stream are offline fixtures. This
checks allocation semantics, not generated game lifetimes or a payment fix.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from verify_heap import ROOT, parse as parse_heap
from verify_near_heap import parse as parse_near


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixtures(directory, filename):
    trace = json.loads((directory / filename).read_text(encoding='utf-8'))
    states, near = [], []
    for entry in trace['heap']:
        raw = (directory / entry['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry['sha256']
        states.append(parse_heap(raw, entry['ss']))
        near.append(parse_near(raw, entry['ss']))
    return trace, states, near


def verify(godot, output, preparation, packing):
    output.mkdir(parents=True, exist_ok=False)
    trace, states, near = fixtures(preparation, 'trace.json')
    packed, pack_states, _ = fixtures(packing, 'run.json')
    assert len(states) == 104 and len(pack_states) == 4
    calls = []
    expected = []
    for operation, source, values in [('prepare', trace, states), ('pack', packed, pack_states)]:
        for i in range(0, len(values), 2):
            before, after = source['heap'][i:i + 2]
            assert before['phase'] == 0 and after['phase'] == 1
            assert before['requested'] == after['requested']
            calls.append(dict(operation=operation, initial=values[i], requested=before['requested']))
            expected.append(values[i + 1])
    beginning, ending = trace['heap'][0]['milliseconds'], trace['heap'][-1]['milliseconds']
    stream = [dict(type='checkpoint', milliseconds=f['milliseconds'], index=i)
              for i, f in enumerate(trace['heap'])]
    stream.extend(dict(e, type='event') for e in trace['events']
                  if beginning <= e['milliseconds'] <= ending
                  and (e['label'].startswith('memory.near.') or e['label'] == 'memory.handle.allocate'))
    stream.sort(key=lambda e: e['milliseconds'])
    (output / 'fixture.json').write_text(json.dumps(dict(calls=calls, near_initial=near[0], stream=stream)), encoding='utf-8')
    with (output / 'godot.log').open('w', encoding='utf-8') as log:
        process = subprocess.run([str(godot), '--headless', '--path', str(ROOT / 'treehouse-godot'),
                                  '--script', 'testing/check_resource_heap.gd', '--', str(output.resolve())],
                                 stdout=log, stderr=subprocess.STDOUT, timeout=90)
    errors = (output / 'godot.log').read_text(encoding='utf-8')
    if process.returncode or 'ERROR' in errors:
        print(errors[:6000])
        return False
    actual = json.loads((output / 'godot.json').read_text(encoding='utf-8'))
    checks = []
    for i, (a, e) in enumerate(zip(actual['calls'], expected)):
        diff = {k: dict(actual=a['state'].get(k), expected=v) for k, v in e.items() if a['state'].get(k) != v}
        if calls[i]['operation'] == 'pack':
            after = packed['heap'][(i - 52) * 2 + 1]
            event = next(x for x in packed['events'] if x['label'] == 'heap.pack.return' and x['milliseconds'] == after['milliseconds'])
            available = event['ax'] + 65536 * event['dx']
            if available != a['available']:
                diff['available'] = dict(actual=a['available'], expected=available)
        checks.append(dict(name=f"{calls[i]['operation']}-{i}", passed=not diff, differences=diff, moves=len(a['moves'])))
    for i, (a, e) in enumerate(zip(actual['near'], near)):
        checks.append(dict(name=f'near-{i}', passed=a == e,
                           differences={} if a == e else dict(actual=a, expected=e)))
    checks.extend(actual['checks'])
    passed = (len(actual['calls']) == 54 and len(actual['near']) == 104
              and actual['allocations'] == 237 and actual['frees'] == 206
              and all(c['passed'] for c in checks))
    sources = ['scripts/resource_heap.gd', 'scripts/resource_near_heap.gd', 'testing/check_resource_heap.gd']
    report = dict(passed=passed, scope=__doc__, checks=checks, allocations=actual['allocations'], frees=actual['frees'],
                  sources={p: digest(ROOT / 'treehouse-godot' / p) for p in sources},
                  references={str(p): digest(p) for p in [preparation / 'trace.json', packing / 'run.json']},
                  verifier_sha256=digest(Path(__file__)), full_game_parity=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=passed, checks=len(checks), failures=[c['name'] for c in checks if not c['passed']],
                          moves=sum(c.get('moves', 0) for c in checks), allocations=actual['allocations'], frees=actual['frees'])))
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, default=ROOT / 'testing/output/treehouse/nature-lifetime-d')
    parser.add_argument('--packing', type=Path, default=ROOT / 'testing/output/treehouse/board-cursor-relocation-c')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot, args.output, args.preparation, args.packing) else 1)
