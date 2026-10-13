"""Compare short, held and long stationary basket-to-worm gestures with DOS."""
from pathlib import Path
import argparse
import hashlib
import json
from verify_room_native_journey import verify as compare, DATA


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for hold, reference in [(8, 'open-basket-click-native-8-a'),
                            (30, 'open-basket-click-native-30-a'),
                            (60, 'basket-handoff-native-60-a')]:
        destination = output / str(hold)
        passed = compare(html, destination, DATA / reference)
        results.append(dict(hold_frames=hold, passed=passed,
                            report=str(destination / 'report.json')))
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                  passed=all(r['passed'] for r in results), journeys=results,
                  scope='Continuous ordinary mouse replay from one initial snapshot per journey; full checkpoint RGB membership and gameplay/object/random state. Exact presentation and audio timing remain separate requirements.')
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output) else 1)
