"""Replay the original 26-cent payment, including coin preparation side effects."""
from pathlib import Path
import argparse
from verify_board_native_journey import ROOT, verify

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output,
        ROOT/'testing/output/treehouse/board-native-loss-a/state',
        ['step-06', 'step-07'], observe_initial=True) else 1)
