"""Read JSON evidence with an optional lossless, deterministic gzip wrapper."""
import gzip
import hashlib
import json
from pathlib import Path


def resolve(path):
    path = Path(path)
    packed = path.with_suffix(path.suffix + '.gz')
    return packed if not path.exists() and packed.exists() else path


def read(path):
    path = resolve(path)
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def digest(path):
    with resolve(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
