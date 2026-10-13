"""Observe board-game digital sources without changing the original journey."""
from pathlib import Path
import argparse, json
import capture_board_completion as journey
from capture import digest
from capture_theater_audio_journey import AudioRecorder

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--chips', action='store_true')
    args = parser.parse_args()
    journey.Recorder = AudioRecorder
    passed = journey.capture(args.output, chips=args.chips)
    path = args.output / 'run.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    report['audio_capture_tool_sha256'] = digest(Path(__file__))
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if passed else 1)
