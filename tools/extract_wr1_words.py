"""Preserve WR1's byte-addressed word stream for its seven-word loader."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_dir', type=Path)
    args = parser.parse_args()
    data = (args.game_dir/'WR1.3').read_bytes()
    words = data.decode('ascii').split()
    if any(not word.isalpha() or not 1 <= len(word) <= 7 for word in words):
        parser.error('Expected WR1 words of one to seven ASCII letters')
    (ROOT/'data/wr1/word_list.json').write_text(json.dumps({
        'source_sha256':hashlib.sha256(data).hexdigest(),
        'text':data.decode('ascii')},indent=2)+'\n')


if __name__ == '__main__':
    main()
