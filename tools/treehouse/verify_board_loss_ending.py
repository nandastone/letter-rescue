"""Compare the original unaffordable payment and losing-game ending."""
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
        ['step-30', 'step-31'], complete_game=True) else 1)
