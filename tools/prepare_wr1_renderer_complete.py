"""Preserve complete renderer intervals, excluding the outer RETF."""
import argparse
import gzip
import json
from pathlib import Path
from prepare_wr1_renderer_background import prepare

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--start-call',type=int,default=561)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,start_call=args.start_call,stage=0x1689)
    if any('tail' not in c for c in fixture['cases']):raise ValueError('Missing live renderer tail state')
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} complete renderer intervals")
