"""Compare observed original cues through nature editing and a complete quiz."""
from pathlib import Path
import argparse, hashlib, json
from verify_nature_editing_native import verify as editing, DATA
from verify_nature_native_journey import verify as quiz
from compare_nature_audio_events import compare


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    journeys = {}
    for name, reference, capture in [
        ('editing', 'nature-edit-native-a', 'nature-edit-audio-native-a'),
        ('quiz', 'nature-native-journey-c', 'nature-quiz-audio-native-a'),
    ]:
        journey_output = output / name
        if name == 'editing':
            passed = editing(html, journey_output, DATA / reference, True)
        else:
            passed = quiz(html, journey_output, observe_audio=True)
        checks.append(dict(name=name + ' images and gameplay state', passed=passed))
        audio_output = output / (name + '-audio')
        audio_passed = compare(html, DATA / capture, journey_output, DATA / reference, audio_output) if passed else False
        checks.append(dict(name=name + ' observed original sound sources and rates in order', passed=audio_passed))
        journeys[name] = dict(journey_report=str(journey_output / 'report.json'), audio_report=str(audio_output / 'report.json'))
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
        passed=all(c['passed'] for c in checks), checks=checks, journeys=journeys,
        full_audio_parity=False,
        scope='Ordinary-input editing and complete quiz/prize/room-return journeys from initial snapshots. Full RGB checkpoint membership, active gameplay state and observed original sound source/rate order. Native control media, actions and checkpoints must be unchanged. Does not prove complete repeated-source counts, rendered whole-journey waveform or exact event timing.')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.html, args.output) else 1)
