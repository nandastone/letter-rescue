"""Compare actual gameplay with recorded update-entry controls, excluding wall time/pixels.

This is an additional diagnostic, not a replacement for run_wr1_parity.py.
Only the five input bits cross into the engine; later observed state stays here.
"""
import argparse
import json
import os
from pathlib import Path
import shutil

from compare_wr1_boundaries import compare, FIELDS
from compare_wr1_traces import differences
from run_wr1_parity import ROOT, FIXTURES, SCENARIOS, read, save, digest, run_engine


def input_stream(fixture, replay, replay_digest):
    if (not fixture['complete'] or fixture['source_sha256'] != replay['source_sha256']
            or fixture['instruction_trace_sha256'] != replay['instruction_trace_sha256']):
        raise ValueError('Input evidence does not belong to this replay')
    if [u['tick'] for u in fixture['updates']] != list(range(1, len(fixture['updates']) + 1)):
        raise ValueError('Logical input stream requires contiguous updates from 1')
    return {'source_sha256': replay['source_sha256'], 'replay_sha256': replay_digest,
            'instruction_trace_sha256': fixture['instruction_trace_sha256'],
            'inputs': [{key: bool(u['begin'][key]) for key in
                        ('up', 'down', 'left', 'right', 'slime_request')} for u in fixture['updates']]}


def run(name, godot, output):
    directory = output / name
    directory.mkdir()
    replay_path = FIXTURES / ('wr1_controlled_quantized_replay.json' if name == 'controlled' else f'wr1_{name}_replay.json')
    replay = read(replay_path)
    fixture = read(FIXTURES / f'wr1_{name}_boundaries.json')
    inputs = directory / 'inputs.json'
    save(inputs, input_stream(fixture, replay, digest(replay_path)))
    trace = directory / 'clone.jsonl'
    args = ['--legacy', '--replay', str(replay_path), '--logical-inputs', str(inputs), '--state-trace', str(trace)]
    if not replay.get('original_level_start'):
        args += ['--mystery-word', 'cup']
    warnings = run_engine(godot, ['--headless', '--'] + args, directory, 'state', 120)
    clone = [json.loads(line) for line in trace.read_text().splitlines() if line]
    input_digest = digest(inputs)
    if not clone or any(r.get('input_clock') != 'logical_update' or r.get('logical_inputs_sha256') != input_digest for r in clone):
        raise ValueError('Missing logical input provenance')
    report = compare(fixture, clone, replay, digest(replay_path))
    fields = set(FIELDS) | {k for u in fixture['updates'] for k in u['completed'] if k in clone[0]}
    initial = differences(fixture['initial'], clone[0], sorted(fields & fixture['initial'].keys())) if 'initial' in fixture else {}
    failures = [m for m in report['mismatches'] if m['state'] or m['inputs']]
    # Keep the comparison evidence, explicitly label unpaired wall-clock samples.
    save(directory / 'comparison.json', report)
    result = {'name': name, 'scope': 'completed gameplay with update-entry controls; wall time and pixels excluded',
              'state_exact': report['completed_state_exact'], 'expected_updates': report['expected_updates'],
              'missing_updates': report['missing_clone_updates'], 'initial': initial,
              'first_difference': next(iter(failures), None), 'warnings': warnings,
              'exact': not initial and not failures and not report['missing_clone_updates']}
    save(directory / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', default=os.environ.get('GODOT') or shutil.which('godot'))
    parser.add_argument('--scenario', choices=SCENARIOS, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.godot or not Path(args.godot).is_file():
        parser.error('A real Godot executable is required')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = [run(name, str(Path(args.godot).resolve()), output) for name in args.scenario]
    save(output / 'report.json', results)
    for result in results:
        print(json.dumps(result))
    return int(any(not r['exact'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
