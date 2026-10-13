"""Audit observed original board sounds against the ordinary browser replay.

The browser report identifies whether its waits follow recorded input ticks or
idle 420 ticks after an action settles. Differing reminder repetitions remain
explicit findings. Same-source native
restarts can also escape callback observation. Full waveform/timing and image
fidelity remain independent requirements.
"""
from pathlib import Path
import argparse, base64, hashlib, json, struct
from compare_nature_audio_events import rate

digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))


def compare(html, native, browser, control, output):
    output.mkdir(parents=True, exist_ok=False)
    text = html.read_text(encoding='utf-8')
    start = text.index('const ORIGINAL = ') + len('const ORIGINAL = ')
    assets = json.loads(text[start:text.index(';</script>', start)])
    hashes = {k: hashlib.sha256(base64.b64decode(v['pcm'])).hexdigest() for k, v in assets['pcm'].items()}
    keys = {}
    for key, sha in hashes.items(): keys.setdefault(sha, []).append(key)
    reference = read(native / 'run.json'); original = read(control / 'run.json'); actual = read(browser / 'report.json')
    assert reference['passed'] and original['passed'] and actual['demo_sha256'] == digest(html) and not actual['errors']
    names = ['initial'] + [d['name'] for d in reference['decisions']]
    assert names == [c['name'] for c in actual['checkpoints']]
    files = [p.relative_to(control) for p in (control / 'state').glob('*.png')] + [Path('state/audio.wav'), Path('frames.jsonl')]
    checks = [dict(path=str(p), passed=(native / p).exists() and digest(native / p) == digest(control / p)) for p in files]
    checks += [dict(path=key, passed=reference[key] == original[key]) for key in ['actions', 'initial', 'decisions', 'ending']]
    ticks = {name: struct.unpack_from('<I', (native / 'state' / (name + '.ram-0')).read_bytes(), 0x323f0 + 0x201e)[0] for name in names}
    rows = read(native / 'sound-observations.json')['rows']
    intervals = []; missing = []; replacements = []; prior = ticks[names[0]]
    for name in names:
        observed = [dict(tick=r['tick'], keys=keys.get(r['pcm_sha256'], []), pcm_sha256=r['pcm_sha256'], rate=rate(r['header'][1])) for r in rows if r['active'] and prior < r['tick'] <= ticks[name]]
        dispatched = [e for e in actual['sound_events'] if e['type'] == 'start' and e['checkpoint'] == name]
        # Consecutive identical starts at one scheduling instant leave only the
        # last voice audible. Preserve the raw calls but do not match a later
        # native observation to such a zero-duration restart.
        audible = [i for i, e in enumerate(dispatched) if not (i + 1 < len(dispatched) and
            all(e[k] == dispatched[i + 1][k] for k in ['tick', 'key', 'rate']))]
        cursor = 0; matches = []; matched = set()
        for event in observed:
            index = next((i for i in audible if i >= cursor and hashes[dispatched[i]['key']] == event['pcm_sha256'] and dispatched[i]['rate'] == event['rate']), None)
            matches.append(dict(native=event, browser=dispatched[index] if index is not None else None))
            if index is None: missing.append(dict(checkpoint=name, **event))
            else: cursor = index + 1; matched.add(index)
        for a, b in zip(matches, matches[1:]):
            if a['browser'] and b['browser'] and a['browser']['tick'] == b['browser']['tick'] and b['native']['tick'] - a['native']['tick'] > 2:
                replacements.append(dict(checkpoint=name, first=a, second=b))
        intervals.append(dict(name=name, native_tick_start=prior, native_tick_end=ticks[name], native=observed, browser=dispatched, matches=matches,
            same_tick_identical_restarts=[e for i,e in enumerate(dispatched) if i not in audible],
            unmatched_browser=[e for i, e in enumerate(dispatched) if i not in matched], passed=all(m['browser'] is not None for m in matches)))
        prior = ticks[name]
    report = dict(demo_sha256=digest(html), reference=str(native), browser_report=str(browser / 'report.json'), browser_report_sha256=digest(browser / 'report.json'),
        control=str(control), control_checks=checks, checkpoints=intervals, missing=missing, suspicious_same_tick_replacements=replacements,
        input_timing='recorded native callback/checkpoint ticks' if 'native_input_schedule' in actual else 'settle then 420 idle ticks',
        browser_images_and_state_passed=actual['passed'], passed=all(c['passed'] for c in checks) and not missing and not replacements,
        full_audio_parity=False, scope=__doc__)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('control', all(c['passed'] for c in checks), 'observed', sum(len(c['native']) for c in intervals), 'missing', len(missing), 'same-tick replacements', len(replacements))
    for c in intervals:
        if not c['passed']: print(c['name'], 'native', [n['keys'] for n in c['native']], 'browser', [e['key'] for e in c['browser']])
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['html', 'native', 'browser', 'control', 'output']: parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if compare(args.html, args.native, args.browser, args.control, args.output) else 1)
