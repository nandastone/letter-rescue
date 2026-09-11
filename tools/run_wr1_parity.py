"""Run actual Godot gameplay against saved native evidence; never skip the engine.

Exit 0: all measured comparisons exact; 1: divergence; 2: execution/evidence error.
Native captures are immutable references, not a fresh DOSBox run. No timing residual
allowlist is used. Uncaptured pixels and unobserved gameplay remain unverified.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageChops
from compare_wr1_boundaries import compare, FIELDS
from compare_wr1_traces import differences
from build_wr1_demo_replay import DEMO_ORDER
from json_evidence import read, digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'testing/fixtures'
SCENARIOS = tuple(f'demo_level{level}' for level in DEMO_ORDER)
PIXELS = {name: name for name in SCENARIOS}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def summarize_comparison(report):
    """Keep pre-validation observations visible, separately from validation."""
    result = {'updates': report['compared'], 'state_exact': report['completed_state_exact'],
              'expected_updates': report['expected_updates'],
              'missing_updates': report['missing_clone_updates'],
              'outside_fixture': report['clone_updates_beyond_fixture']}
    for name, predicate in (
        ('state', lambda m: bool(m['state'])),
        ('inputs', lambda m: bool(m['inputs'])),
        ('timing', lambda m: m['native_entry_counter'] != m['clone_entry_counter'])):
        rows = [m for m in report['mismatches'] if predicate(m)]
        result[name] = {'count': len(rows), 'validation_count': sum(m['validation'] for m in rows),
                        'first': next((m for m in rows if m['validation']), None),
                        'first_observed': next(iter(rows), None)}
    return result


def compare_demo_terminal(fixture, clone):
    terminal = fixture.get('demo_terminal')
    if not terminal:
        return None
    index = terminal['begin']['main_iteration']
    rows = [r for r in clone if r.get('demo_input_index') == index]
    if len(rows) != 1 or rows[0].get('input_clock') != 'native_demo':
        return {'exact':False, 'error':'Missing or duplicate terminal demo update', 'demo_input_index':index}
    row, native = rows[0], terminal['completed']
    fields = set(FIELDS) | {k for u in fixture['updates'] for k in u['completed'] if k in row}
    state = differences(native, row, sorted(fields & native.keys()))
    inputs = {k:{'native':bool(terminal['begin'][k]),'clone':row['held'].get(k)}
              for k in ('up','down','left','right','slime_request') if bool(terminal['begin'][k]) != row['held'].get(k)}
    return {'exact':not state and not inputs, 'state':state, 'inputs':inputs,
            'demo_input_index':index, 'boundary':terminal['boundary'],
            'timing_exact':native['launch_call'] == row['completed_source_frame']+1,
            'native_final_counter':native['launch_call'], 'clone_final_counter':row['completed_source_frame']+1}


def run_engine(godot, args, directory, label, timeout):
    # Fixed simulation delta is already independent of wall time. Avoid waiting
    # for monitor refresh when synchronously capturing the same replay frames.
    command = [godot, '--path', str(ROOT), '--fixed-fps', '70', '--disable-vsync', '--verbose'] + args
    save(directory / (label + '_command.json'), command)
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (directory / (label + '.log')).write_text(process.stdout + '\n' + process.stderr, encoding='utf-8')
    errors = [line for line in process.stderr.splitlines() if line.startswith(('ERROR:', 'SCRIPT ERROR:'))]
    # Existing accelerated shutdown can retain known WAV resources. Preserve the
    # warning in the report and reject any other engine error or leaked resource.
    resource_warning = re.compile(r'^ERROR: [1-9][0-9]* resources still in use at exit\.$')
    leaks = re.findall(r'Resource still in use: (.+)', process.stdout)
    safe_leaks = bool(leaks) and all(re.fullmatch(
        r'res://assets/audio/sfx/(collect|wrong|reveal|correct|unlock)\.wav \(AudioStreamWAV\)', x) for x in leaks)
    fatal = [e for e in errors if not (resource_warning.fullmatch(e) and safe_leaks)]
    if process.returncode or fatal:
        raise RuntimeError(f'{label}: engine failed ({process.returncode}): {fatal[:8]}; '
                           f'{len(fatal)} error lines total; see {label}.log')
    return errors


def pixel_pairs(name, replay, replay_path):
    if name not in PIXELS:
        return []
    manifest = read(FIXTURES / f'wr1_{PIXELS[name]}_pixels.json')
    for key in ('source_sha256', 'instruction_trace_sha256'):
        if key in manifest and manifest[key] != replay.get(key):
            raise ValueError(f'Pixel {key} does not match replay')
    if 'source_replay_sha256' in manifest and manifest['source_replay_sha256'] != replay['source_sha256']:
        raise ValueError('Pixel source replay hash does not match replay')
    if 'replay' in manifest and manifest['replay'] != replay_path.name:
        raise ValueError('Pixel manifest belongs to another replay')
    pairs = [dict(p, native_file=p.get('native_file', p.get('file')))
             for p in manifest.get('pairs', manifest.get('frames', [manifest] if 'native_file' in manifest else []))]
    for p in pairs:
        p['clone_file'] = f"source_{p['clone_source_frame']:06d}.png"
        if p['native_counter'] != p['clone_source_frame'] + 1:
            raise ValueError('Pixel frame mapping is not exact')
    if 'initial_file' in manifest:
        # Older level-two manifest stores this hash in the replay checkpoint.
        expected = manifest.get('initial_sha256')
        if expected is None:
            raise ValueError('Initial pixel manifest requires initial_sha256')
        pairs.insert(0, {'native_file': manifest['initial_file'], 'sha256': expected, 'clone_file': 'initial.png'})
    captures = {}
    for p in pairs:
        if digest(FIXTURES / p['native_file']) != p['sha256']:
            raise ValueError(f"Native image hash mismatch: {p['native_file']}")
        if 'capture_file' in p:
            capture_path = FIXTURES / p['capture_file']
            if digest(capture_path) != p['capture_sha256']:
                raise ValueError('Supplemental pixel capture hash mismatch')
            if p['capture_file'] not in captures:
                capture = read(capture_path)
                if not capture.get('complete') or capture.get('source_sha256') != replay['source_sha256']:
                    raise ValueError('Supplemental pixel capture is incomplete or belongs to another replay')
                captures[p['capture_file']] = {r['replay_frame'] for r in capture['samples'] if 'screenshot' in r}
            if p['native_counter'] not in captures[p['capture_file']]:
                raise ValueError('Supplemental pixel counter was not captured')
    return pairs


def compare_pixels(pairs, directory):
    results = []
    for pair in pairs:
        native = Image.open(FIXTURES / pair['native_file']).convert('RGB')
        clone = Image.open(directory / 'pixels' / pair['clone_file']).convert('RGB')
        row = dict(pair, native_size=list(native.size), clone_size=list(clone.size))
        row['exact'] = native.size == clone.size and native.tobytes() == clone.tobytes()
        if not row['exact'] and native.size == clone.size:
            delta = ImageChops.difference(native, clone)
            channels = iter(delta.tobytes())
            row['different_pixels'] = sum(any(p) for p in zip(channels, channels, channels))
            row['bbox'] = delta.getbbox()
            delta.save(directory / 'pixels' / ('diff_' + pair['clone_file']))
            panel = Image.new('RGB', (native.width * 3, native.height))
            for i, img in enumerate((native, clone, delta)):
                panel.paste(img, (i * native.width, 0))
            panel.save(directory / 'pixels' / ('comparison_' + pair['clone_file']))
        results.append(row)
    return results


def run_scenario(name, godot, output, timeout, vga_scanout=False, snapshot_video=False, clear_text=False):
    directory = output / name
    directory.mkdir()
    replay_path = FIXTURES / f'wr1_{name}_replay.json'
    fixture_path = FIXTURES / f'wr1_{name}_boundaries.json'
    replay, fixture = read(replay_path), read(fixture_path)
    validate_demo_evidence(name, replay, fixture)
    args = ['--legacy', '--replay', str(replay_path)]
    if clear_text:
        args += ['--clear-text', '--capture-reference-video']
    if vga_scanout:
        args += ['--vga-scanout']
    if snapshot_video:
        args += ['--snapshot-video']
    use_scanout = not snapshot_video
    if not replay.get('original_level_start'):
        args += ['--mystery-word', 'cup']
    trace = directory / 'clone.jsonl'
    pairs = pixel_pairs(name, replay, replay_path)
    if not pairs:
        raise ValueError('Maintained demos require native screenshot evidence')
    frames = ','.join(str(p['clone_source_frame']) for p in pairs if 'clone_source_frame' in p)
    capture = ['--minimized', '--script', 'testing/capture_wr1_replay_frames.gd', '--'] + args + [
        '--state-trace', str(trace), '--capture-through-replay-end',
        '--capture-source-frames', frames, '--capture-directory', str(directory / 'pixels')]
    if any(p['clone_file'] == 'initial.png' for p in pairs):
        capture += ['--capture-initial']
    warnings = run_engine(godot, capture, directory, 'game', timeout)
    clone = [json.loads(line) for line in trace.read_text().splitlines() if line]
    if replay.get('original_demo_inputs'):
        demo_hash = replay['demo_provenance']['sha256']
        if fixture.get('demo_sha256') != demo_hash or any(
                r.get('input_clock') != 'native_demo' or r.get('demo_sha256') != demo_hash
                or ('source_frame' in r and r.get('demo_input_index') != replay['demo_input_offset'] + r['tick'] - 1)
                for r in clone):
            raise ValueError('Demo trace has stale or missing input provenance')
    report = compare(fixture, clone, replay, digest(replay_path))
    save(directory / 'comparison.json', report)
    result = dict(name=name, **summarize_comparison(report), warnings=warnings,
                  presentation=('clear_text_with_reference_' if clear_text else '') + ('vga_scanout' if use_scanout else 'snapshot'),
                  measured_video_phase='frame_start' in replay.get('original_video_start', {}),
                  replay_sha256=digest(replay_path), native_fixture_sha256=digest(fixture_path))
    result['initial'] = {}
    result['demo_terminal'] = compare_demo_terminal(fixture, clone)
    if result['demo_terminal'] is not None:
        save(directory / 'demo_terminal.json', result['demo_terminal'])
    if 'initial' in fixture:
        # Compare shared observable game fields, excluding native CPU metadata.
        fields = set(FIELDS) | {k for u in fixture['updates'] for k in u['completed'] if k in clone[0]}
        result['initial'] = differences(fixture['initial'], clone[0], sorted(fields & fixture['initial'].keys()))
    timed = {r['tick']: r for r in clone if 'source_frame' in r}
    for category in ('state', 'inputs', 'timing'):
        first = result[category]['first'] or result[category]['first_observed']
        if first:
            tick = first['tick']
            save(directory / f'first_{category}.json', {
                'divergence': first, 'context': [
                    {'native': u, 'clone': timed.get(u['tick'])}
                    for u in fixture['updates'] if tick - 2 <= u['tick'] <= tick + 2]})
    pixels = compare_pixels(pairs, directory)
    save(directory / 'pixels.json', pixels)
    result['pixels'] = {'compared': len(pixels), 'exact': sum(p['exact'] for p in pixels),
                        'first': next((p for p in pixels if not p['exact']), None)}
    # Timing remains a failing dimension inside the fixture's validation span;
    # startup calibration is still reported. Known residuals are never forgiven.
    result['exact'] = (not result['missing_updates'] and not result['initial'] and all(result[c]['count'] == 0 for c in ('state', 'inputs'))
                       and result['timing']['validation_count'] == 0 and result['pixels']['first'] is None
                       and (result['demo_terminal'] is None or
                            (result['demo_terminal']['exact'] and result['demo_terminal']['timing_exact'])))
    return result


def validate_demo_evidence(name, replay, fixture):
    """Every maintained demo must include controls and its observed ending."""
    if name not in SCENARIOS or replay.get('level') != int(name.removeprefix('demo_level')):
        raise ValueError('Demo replay belongs to a different level')
    if not replay.get('original_demo_inputs') or replay.get('events'):
        raise ValueError('Demo requires decoded original controls')
    if not fixture.get('updates') or not fixture.get('demo_terminal'):
        raise ValueError('Demo requires ordinary and terminal native evidence')
    if fixture.get('demo_sha256') != replay.get('demo_provenance', {}).get('sha256'):
        raise ValueError('Demo hash does not match native evidence')


def write_report(output, results, godot):
    completed = [r for r in results if 'error' not in r]
    totals = {'scenarios': len(results), 'errors': len(results) - len(completed),
              'state_exact': sum(r['state_exact'] for r in completed),
              'updates': sum(r['updates'] for r in completed),
              'missing_updates': sum(len(r['missing_updates']) for r in completed),
              'input_differences': sum(r['inputs']['count'] for r in completed),
              'timing_validation_differences': sum(r['timing']['validation_count'] for r in completed),
              'timing_all_differences': sum(r['timing']['count'] for r in completed),
              'terminal_differences': sum(not (r['demo_terminal']['exact'] and r['demo_terminal'].get('timing_exact',False)) for r in completed if r.get('demo_terminal') is not None),
              'pixels_exact': sum(r['pixels']['exact'] for r in completed),
              'pixels_compared': sum(r['pixels']['compared'] for r in completed)}
    save(output / 'report.json', {'godot': godot, 'native': 'saved immutable captures', 'totals': totals, 'scenarios': results})
    lines = ['# Actual-game parity', '',
             'Fresh Godot runs against saved native captures. Timing is reported without shifting frames or allowing known residuals.', '',
             'For Clear Text runs, pixel comparisons check the preserved original video stream, not the deliberately different readable display. The displayed images are retained separately as `*_clear.png`.', '',
             f"{totals['state_exact']}/{totals['updates']} matching update-state comparisons; {totals['missing_updates']} missing clone updates; {totals['pixels_exact']}/{totals['pixels_compared']} matching images; {totals['timing_validation_differences']} validation timing differences; {totals['terminal_differences']} terminal differences; {totals['errors']} execution/evidence errors.", '',
             '| Scenario | Presentation | State exact | Input differences | Timing differences (validation / all) | Pixels exact |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    for r in results:
        if 'error' in r:
            lines += [f"| {r['name']} | | ERROR | | | |", '', f"{r['name']}: {r['error']}", '']
            continue
        p = r['pixels']
        policy = r.get('presentation', 'unspecified')
        if policy.endswith('vga_scanout') and not r.get('measured_video_phase', False):
            policy += ' (phase assumed)'
        lines += [f"| [{r['name']}]({r['name']}/comparison.json) | {policy} | {r['state_exact']}/{r['updates']} | {r['inputs']['count']} | {r['timing']['validation_count']} / {r['timing']['count']} | {str(p['exact'])+'/'+str(p['compared']) if p['compared'] else 'unverified'} |"]
    lines += ['', '## First differences', '']
    for r in results:
        if 'error' in r:
            continue
        if r['initial']:
            lines += [f"- {r['name']}: initial state differs: {list(r['initial'])}"]
        if r['missing_updates']:
            lines += [f"- {r['name']}: {len(r['missing_updates'])} missing clone updates, starting at tick {r['missing_updates'][0]}; this is a failing comparison, not verified coverage."]
        if r.get('demo_terminal') is not None:
            terminal = r['demo_terminal']
            lines += [f"- {r['name']}: terminal demo ending state/inputs {'match' if terminal['exact'] else 'differ'} ([comparison]({r['name']}/demo_terminal.json)); its special return is separate from ordinary D72 updates."]
            if not terminal.get('timing_exact',False):
                lines += [f"  Terminal timing differs: native counter {terminal.get('native_final_counter')}, clone counter {terminal.get('clone_final_counter')}."]
        for category in ('state', 'inputs', 'timing'):
            first = r[category]['first'] or r[category]['first_observed']
            if first:
                lines += [f"- {r['name']} {category}: tick {first['tick']}, native counter {first['native_entry_counter']}, clone counter {first['clone_entry_counter']} ([context]({r['name']}/first_{category}.json))."]
        if r['pixels']['first']:
            p = r['pixels']['first']
            lines += [f"- {r['name']} pixels: {p['clone_file']} ([native / clone / difference]({r['name']}/pixels/comparison_{p['clone_file']}))."]
    lines += ['', '## Coverage limits', '',
              'The maintained suite is the 15 original demos. Each run checks every recorded ordinary gameplay update after its post-load checkpoint, the consumed demo controls, admission timing, and any recorded terminal death or exit. Image coverage is limited to the listed native screenshots; a green result does not establish pixel equality for every displayed frame. Audio, menus, attract-mode transitions and gameplay outside these demos remain unverified. Missing fixtures, updates and terminal evidence fail the gate. Loading duration is excluded.', '',
              'Isolated CPU/renderer model tests are separate research checks and do not count as gameplay improvements. Engine warnings are preserved in JSON and logs.']
    (output / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', default=os.environ.get('GODOT') or shutil.which('godot'))
    parser.add_argument('--scenario', choices=SCENARIOS, action='append')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--timeout', type=float, default=420)
    parser.add_argument('--clear-text', action='store_true',
                        help='Exercise Clear Text display and compare its preserved original video stream; retain HD screenshots separately')
    presentation = parser.add_mutually_exclusive_group()
    presentation.add_argument('--vga-scanout', action='store_true',
                        help='Use VGA page latch/scanout (the default); drawing costs remain incomplete')
    presentation.add_argument('--snapshot-video', action='store_true',
                              help='Force compatibility presentation even with measured VGA phase')
    args = parser.parse_args()
    if not args.godot or not Path(args.godot).is_file():
        parser.error('Godot is required: pass --godot or set GODOT. Engine comparisons cannot be skipped.')
    output = (args.output or ROOT / 'testing/output/parity' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in dict.fromkeys(args.scenario or SCENARIOS):
        try:
            result = run_scenario(name, str(Path(args.godot).resolve()), output, args.timeout, args.vga_scanout, args.snapshot_video, args.clear_text)
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as error:
            result = {'name': name, 'error': str(error)}
        results.append(result)
        write_report(output, results, args.godot)
        print(json.dumps(result), flush=True)
    print(f'Report: {output / "report.md"}', flush=True)
    return 2 if any('error' in r for r in results) else int(any(not r['exact'] for r in results))


if __name__ == '__main__':
    sys.exit(main())
