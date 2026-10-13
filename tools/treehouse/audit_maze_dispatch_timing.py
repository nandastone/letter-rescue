"""Locate maze sound dispatch differences without shifting either timeline.

The native observer samples the active source at video callbacks, so an observed
tick is not an exact start timestamp. This report compares those observations
with browser dispatch ticks anchored at the shared initial snapshot. A passing
observation comparison would still not establish sample-level audio parity.
"""
from pathlib import Path
import argparse
import hashlib
import json


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(html, journey, comparison, output):
    actual, paired = read(journey), read(comparison)
    sha = digest(html)
    assert actual['demo_sha256'] == paired['demo_sha256'] == sha
    assert paired['browser_report_sha256'] == digest(journey)
    assert actual['passed'] and not actual['errors']
    assert all(c['passed'] for c in paired['control_checks'])
    assert not paired['input_interval_missing']
    assert 'sound_clock_origin' in actual, 'Rerun with explicit browser clock origin'
    native_origin = paired['checkpoints'][0]['native_tick_start']
    browser_origin = actual['sound_clock_origin']
    groups = []
    for interval in paired['input_intervals']:
        # Source-only matching can pair a later automatic replay with an earlier
        # identical audition. Use every possible ordered match to expose that
        # ambiguity; never pick the closest timestamp to make timing look better.
        native_events, browser_events = interval['native'], interval['browser']
        same = lambda n, b: b['key'] in n['keys'] and b['rate'] == n['rate']
        earliest, latest = [], [None] * len(native_events)
        cursor = 0
        for native in native_events:
            index = next(i for i in range(cursor, len(browser_events)) if same(native, browser_events[i]))
            earliest.append(index)
            cursor = index + 1
        cursor = len(browser_events) - 1
        for j in range(len(native_events)-1, -1, -1):
            index = next(i for i in range(cursor, -1, -1) if same(native_events[j], browser_events[i]))
            latest[j] = index
            cursor = index - 1
        events = []
        used = set()
        for j, match in enumerate(interval['matches']):
            native, browser = match['native'], match['browser']
            assert browser is not None and browser['id'] not in used
            used.add(browser['id'])
            assert browser['key'] in native['keys'] and browser['rate'] == native['rate']
            nt, bt = native['tick'] - native_origin, browser['tick'] - browser_origin
            possible = [browser_events[i] for i in range(earliest[j], latest[j]+1)
                if same(native, browser_events[i])]
            events.append(dict(key=browser['key'], rate=browser['rate'],
                native_observed_tick=nt, browser_dispatch_tick=bt,
                browser_minus_native=bt-nt, browser_voice_id=browser['id'],
                uniquely_matched=len(possible) == 1,
                possible_browser_dispatches=[dict(id=b['id'], tick=b['tick']-browser_origin,
                    browser_minus_native=b['tick']-browser_origin-nt) for b in possible]))
        spacing = [dict(first=i, second=i+1,
            native_observed_ticks=b['native_observed_tick']-a['native_observed_tick'],
            browser_dispatch_ticks=b['browser_dispatch_tick']-a['browser_dispatch_tick'])
            for i, (a, b) in enumerate(zip(events, events[1:]))]
        groups.append(dict(checkpoints=interval['names'], events=events, spacing=spacing,
            exact_observed_ticks=sum(e['browser_minus_native'] == 0 for e in events),
            unmatched_browser=interval['unmatched_browser']))
    events = [e for g in groups for e in g['events']]
    assert events, 'Empty timing comparison'
    unique = [e for e in events if e['uniquely_matched']]
    aligned = len(unique) == len(events) and all(e['browser_minus_native'] == 0 for e in unique)
    report = dict(demo_sha256=sha, journey_sha256=digest(journey),
        comparison_sha256=digest(comparison), tool_sha256=digest(Path(__file__)),
        clock_origins=dict(native=native_origin, browser=browser_origin),
        groups=groups, matched_observations=len(events),
        uniquely_matched_observations=len(unique), ambiguous_observations=len(events)-len(unique),
        exact_uniquely_matched_ticks=sum(e['browser_minus_native'] == 0 for e in unique),
        minimum_unique_browser_minus_native=min((e['browser_minus_native'] for e in unique), default=None),
        maximum_unique_browser_minus_native=max((e['browser_minus_native'] for e in unique), default=None),
        observed_tick_alignment=aligned, passed=aligned,
        full_audio_parity=False, scope=__doc__)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ['groups','scope']}, indent=2))
    return aligned


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['html', 'journey', 'comparison', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if audit(args.html, args.journey, args.comparison, args.output) else 1)
