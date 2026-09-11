"""Extract the startup Apogee PCX without altering the source game files."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.game_dir/'WR1.7'
    destination = ROOT/'assets/extracted/wr1_1_png/WR1.7.png'
    Image.open(source).save(destination)
    (ROOT/'data/wr1/frontend_assets.json').write_text(json.dumps({
        'apogee_source':source.name,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'png_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
    },indent=2)+'\n',encoding='utf-8')
