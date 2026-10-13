"""Compare a complete original chip game with continuous browser gameplay."""
from pathlib import Path
import argparse, json, sys
from verify_board_native_journey import ROOT, verify

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--observe-audio',action='store_true');parser.add_argument('--native-waits',action='store_true');args=parser.parse_args()
    reference=ROOT/'testing/output/treehouse/board-native-chips-b'
    run=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    if not run['complete'] or not run['passed'] or not run['chips']:
        raise ValueError('Complete original chip-game ending is required')
    names=['initial']+[decision['name'] for decision in run['decisions']]
    sys.exit(0 if verify(args.html,args.output,reference/'state',names,complete_game=True,observe_audio=args.observe_audio,native_waits=args.native_waits) else 1)
