"""Check observed sound sources through the complete original maze game."""
from pathlib import Path
import argparse, hashlib, json
from verify_maze_native_journey import verify, ROOT
from compare_maze_audio_events import compare
from verify_maze_hint_input import verify as verify_hint_input

DATA = ROOT / 'testing/output/treehouse'


def main(html, output):
    output.mkdir(parents=True, exist_ok=False)
    reference = DATA / 'maze-audio-control-b'
    journey_passed = verify(html, output / 'journey', observe_audio=True,
        reference=reference, victory=reference / 'state/victory', native_waits=True)
    sound_passed = compare(html, DATA / 'maze-audio-native-b', output / 'journey', reference, output / 'audio')
    input_passed = verify_hint_input(html, output / 'fresh-input')
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
        passed=journey_passed and sound_passed and input_passed, checks=[
            dict(name='complete maze including correct click during automatic hint and victory', passed=journey_passed),
            dict(name='observed original sound sources and rates between player inputs', passed=sound_passed),
            dict(name='fresh desktop and touch automatic-hint sign input', passed=input_passed)],
        journey_report=str(output / 'journey/report.json'), audio_report=str(output / 'audio/report.json'),
        full_audio_parity=False,
        scope='One initial original snapshot, then original pointer presses/releases through wrong choice, eight notes and completed victory song. Full RGB checkpoint membership and gameplay/random state plus observed sound source/rate order per player-input interval. The victory tail has no new input. Raw checkpoint sound mismatches and unmatched browser starts are retained; exact event timing and waveform parity remain open.')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if main(args.html, args.output) else 1)
