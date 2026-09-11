"""Preserve renderer entry through matching objects or the player draw."""
import argparse
import gzip
import json
from pathlib import Path
from prepare_wr1_renderer_background import prepare

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--player',action='store_true')
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,stage=0xf18 if args.player else 0xecc)
    if any('matching' not in c or 'player' not in c for c in fixture['cases']):raise ValueError('Missing live renderer state')
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} renderer {'player' if args.player else 'matching'} intervals")
