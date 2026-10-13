"""Check a continuous native quiz win, second reveal, prize and next deal.

Room return is covered separately by verify_nature_native_journey, including
its remaining timing/random-stream discrepancy. This suite ends in nature.
"""
from pathlib import Path
import argparse, sys
from verify_nature_native_journey import verify

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.html,a.output,until='back-to-nature') else 1)
