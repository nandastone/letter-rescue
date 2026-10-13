"""Replay the original 18-cent payment with unused second-amount coin preparation."""
from pathlib import Path
import argparse
from verify_board_native_journey import ROOT, verify


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.html, args.output,
        ROOT/'testing/output/treehouse/board-native-loss-a/state',
        ['step-09', 'step-10'], observe_initial=True) else 1)
