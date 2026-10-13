"""Check observed sound sources through the complete original money game."""
from pathlib import Path
import argparse, hashlib, json
from verify_board_native_journey import verify, ROOT
from compare_board_audio_events import compare

DATA = ROOT / 'testing/output/treehouse'


def main(html, output):
    output.mkdir(parents=True, exist_ok=False)
    reference = DATA / 'board-native-completion-a'
    native = json.loads((reference / 'run.json').read_text(encoding='utf-8'))
    names = ['initial'] + [d['name'] for d in native['decisions']]
    journey_passed = verify(html, output / 'journey', reference / 'state', names,
        complete_game=True, observe_audio=True, native_waits=True)
    sound_passed = compare(html, DATA / 'board-money-audio-native-a', output / 'journey', reference, output / 'audio')
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
        passed=journey_passed and sound_passed, checks=[
            dict(name='complete money game images and state on recorded input schedule', passed=journey_passed),
            dict(name='observed original sound sources and rates in checkpoint order', passed=sound_passed)],
        journey_report=str(output / 'journey/report.json'), audio_report=str(output / 'audio/report.json'),
        full_audio_parity=False,
        scope='Complete money game with original input intervals and unchanged native capture control. Full RGB checkpoint membership and gameplay/random state, plus observed source/rate order. Same-source restarts, full waveform and precise event timing are not established. Chip game is audited separately with its retained visual failure.')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if main(args.html, args.output) else 1)
