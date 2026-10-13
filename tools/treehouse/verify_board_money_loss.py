"""Exercise money payment loss through ordinary visible controls."""
from pathlib import Path
import argparse, sys
from verify_board_journeys import verify

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    sys.exit(0 if verify(args.html,args.output,money_loss_only=True) else 1)
