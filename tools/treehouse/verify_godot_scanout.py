"""Compare the production Godot presenter with 306 native video callbacks.

Component proof only: source images are independently generated legacy-clone
question frames, and commit times/initial video phase are native trace fixtures.
The production presenter then advances its own periodic clock. No native frame
pixels are fed to it. This does not prove Godot gameplay draws, input timing,
absolute video phase, or browser delivery. The atomic baseline must fail on the
15 mixed displays so that the comparison detects removal of scanout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from build_demo import ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(engine, trace_folder, generated, output):
    output.mkdir(parents=True, exist_ok=False)
    trace = json.loads((trace_folder/'trace.json').read_text(encoding='utf-8'))
    generated_report = json.loads((generated/'report.json').read_text(encoding='utf-8'))
    if not generated_report['passed']:
        raise ValueError('Generated source frames failed their existing comparison')
    states = generated_report['sequences']['robot-turn']['states']
    targets = {s['actorFrame']: s for s in states if s['actorFrame'] is not None}
    ends = [e for e in trace['events'] if e['label'] == 'scr.copy.end'][1:]
    if len(ends) != 24 or sorted(targets) != list(range(1, 24)):
        raise ValueError('Question display sequence differs')
    commits = []
    images = {}
    for index, event in enumerate(ends, 1):
        state = targets[min(index, 23)]
        path = generated/state['image']
        pixels = Image.open(path).convert('RGB').tobytes()
        if hashlib.sha256(pixels).hexdigest() != state['hash']:
            raise ValueError('Generated image hash differs')
        images[path.name] = sha(path)
        commits.append(dict(milliseconds=event['milliseconds'], image=str(path.resolve())))
    boundaries = [b for b in trace['boundaries'] if 2115 <= b['run'] <= 2420]
    if len(boundaries) != 306:
        raise ValueError('Native callback window incomplete')
    meta = boundaries[0]['video_timing']
    if meta[1] != 0 or meta[9:11] != [4, 50]:
        raise ValueError('Reference is not the researched VGA PART mode')
    start = meta[5]
    initial = [c for c in commits if c['milliseconds'] <= start][-1]
    fixture = dict(start=start, initial=initial['image'],
                   commits=[c for c in commits if c['milliseconds'] > start],
                   frames=[dict(run=b['run'], callback=b['milliseconds']) for b in boundaries])
    (output/'fixture.json').write_text(json.dumps(fixture, indent=2), encoding='utf-8')
    command = [str(engine.resolve()), '--headless', '--path', str(ROOT/'treehouse-godot'),
               '--script', 'testing/replay_presentation.gd', '--', str(output.resolve())]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=60)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log, encoding='utf-8')
    if result.returncode or 'ERROR' in log:
        raise RuntimeError(log)
    actual = json.loads((output/'godot.json').read_text(encoding='utf-8'))['frames']
    rows = {r['run']: r for r in map(json.loads, (trace_folder/'frames.jsonl').read_text().splitlines())}
    comparisons = [dict(**a, exact=a['hash'] == rows[a['run']]['rgb_sha256'],
                        atomic_exact=a['atomic_hash'] == rows[a['run']]['rgb_sha256']) for a in actual]
    exact = sum(c['exact'] for c in comparisons)
    atomic_exact = sum(c['atomic_exact'] for c in comparisons)
    passed = len(comparisons) == 306 and exact == 306 and atomic_exact == 291
    report = dict(passed=passed, scope=__doc__, exact=exact, atomic_exact=atomic_exact,
                  total=len(comparisons), comparisons=comparisons, command=command,
                  presenter_sha256=sha(ROOT/'treehouse-godot/scripts/presentation.gd'),
                  trace_sha256=sha(trace_folder/'trace.json'), frames_sha256=sha(trace_folder/'frames.jsonl'),
                  generated_report_sha256=sha(generated/'report.json'), generated_images=images)
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=passed, exact=exact, atomic_exact=atomic_exact, total=len(comparisons))))
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--generated', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot, args.trace, args.generated, args.output) else 1)
