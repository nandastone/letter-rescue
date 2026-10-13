"""Replay original listening-key notation, expiry and tempo boundaries."""
from pathlib import Path
import argparse
from verify_maze_navigation import verify,DATA

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output,DATA/'piano-note-native-b') else 1)
