"""Generate Godot startup resource state from executable/platform/archive inputs.

Native boundary states are comparison outputs only. This covers font/cursor
conversion, seven archive catalogs and the retained initial sound. Later scene
lifetimes and live gameplay integration remain open; no timing claim is made.
"""
import argparse
import json
import subprocess
from pathlib import Path

from resource_startup_inputs import extract
from verify_dos_resource_startup import mcbs
from verify_resource_growth import ROOT, DATA, digest, arena_state
from verify_near_heap import parse as parse_near
from memory_catalog import read_catalogs, read_files


def verify(godot, output, assets=None):
    output.mkdir(parents=True, exist_ok=False)
    inputs = (json.loads(assets.read_text(encoding='utf-8'))['resource_ownership'] if assets
              else extract(DATA / 'source/The_Treehouse_1991.zip'))
    (output / 'fixture.json').write_text(json.dumps(inputs), encoding='utf-8')
    expected, references = {}, {}
    for stage in ['font-activation', 'cursor-source', 'cursor-activation', 'catalog', 'startup-sound']:
        folder = DATA / ('resource-startup-sound-a' if stage == 'startup-sound' else f'resource-startup-{stage}-a')
        run = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
        assert run['passed'] and run['fixed_clock']
        references[stage] = digest(folder / 'run.json')
        expected[stage] = []
        for fixture in run['heap'][:14 if stage == 'catalog' else 2]:
            path = folder / fixture['path']
            assert digest(path) == fixture['sha256']
            raw = path.read_bytes()
            ss = fixture['ss']
            state = dict(arena=arena_state(raw, ss)[0], near=parse_near(raw, ss), dos=mcbs(raw))
            if stage in ['catalog', 'startup-sound']:
                state.update(files=read_files(raw, ss), catalogs=read_catalogs(raw, ss))
                for catalog in state['catalogs']:
                    next(b for b in state['arena']['heap']['blocks'] if b.get('handle') == catalog['handle']).pop('payload')
            expected[stage].append(state)
    with (output / 'godot.log').open('w', encoding='utf-8') as log:
        process = subprocess.run([str(godot), '--headless', '--path', str(ROOT / 'treehouse-godot'),
                                  '--script', 'testing/check_resource_startup.gd', '--', str(output.resolve())],
                                 stdout=log, stderr=subprocess.STDOUT, timeout=90)
    log = (output / 'godot.log').read_text(encoding='utf-8')
    if process.returncode or 'ERROR' in log:
        print(log[:8000])
        return False
    actual = json.loads((output / 'godot.json').read_text(encoding='utf-8'))
    checks = actual['checks']
    for stage, states in expected.items():
        observed = actual['boundaries'].get(stage, [])
        checks.append(dict(name=f'{stage} boundary count', passed=len(observed) == len(states)))
        for phase, (a, e) in enumerate(zip(observed, states)):
            for field, value in e.items():
                checks.append(dict(name=f'{stage} {phase} {field}', passed=a.get(field) == value,
                                   differences={} if a.get(field) == value else dict(actual=a.get(field), expected=value)))
    report = dict(passed=all(c['passed'] for c in checks), checks=checks, scope=__doc__, references=references,
                  source_files={p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT / 'treehouse-godot/scripts').glob('resource_*.gd'))},
                  verifier_sha256=digest(Path(__file__)), test_sha256=digest(ROOT / 'treehouse-godot/testing/check_resource_startup.gd'),
                  extractor_sha256=digest(ROOT / 'tools/treehouse/resource_startup_inputs.py'),
                  asset_bundle_sha256=digest(assets) if assets else None,
                  input_sha256=digest(output / 'fixture.json'), full_game_parity=False, playable_integrated=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(checks), failures=[c['name'] for c in checks if not c['passed']])))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--assets', type=Path, help='Use the normal Godot asset bundle instead of direct extraction.')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot, args.output, args.assets) else 1)
