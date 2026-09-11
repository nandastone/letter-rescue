"""Preserve renderer entry through enemy and drip drawing."""
import argparse
import gzip
import json
from pathlib import Path
from prepare_wr1_renderer_background import prepare

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','link_map','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    fixture=prepare(args.capture,args.trace,args.link_map,stage=0x113e)
    if any('actor_images' not in c for c in fixture['cases']):raise ValueError('Missing live actor images')
    args.output.write_bytes(gzip.compress(json.dumps(fixture,separators=(',',':')).encode(),mtime=0))
    print(f"Preserved {len(fixture['cases'])} renderer actor intervals")
