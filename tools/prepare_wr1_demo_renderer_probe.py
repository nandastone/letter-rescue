"""Preserve the first recap world draw as an independent renderer experiment."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def prepare(capture, trace, replay):
    provenance = json.loads(capture.read_text())
    replay_data = json.loads(replay.read_text())
    digest = hashlib.file_digest(trace.open('rb'), 'sha256').hexdigest()
    if not provenance['complete'] or digest != provenance['instruction_trace_sha256']:
        raise ValueError('Incomplete or changed native trace')
    ready = False
    entry = None
    expected = None
    for line in trace.open('rb'):
        if line.startswith(b'{"event":"lifecycle"') and b'"ip":6525,' in line:
            ready = True
        if ready and line.startswith(b'{"event":"graphics","kind":"renderer"'):
            row = json.loads(line)
            if row['entry']:
                entry = row
            elif entry is not None:
                expected = row
                break
    if entry is None or expected is None:
        raise ValueError('No complete recap world draw')
    return {'source_trace_sha256':digest, 'exe_sha256':provenance['exe_sha256'],
            'core_sha256':provenance['core_sha256'],
            'scope':'First native recap world-renderer entry and expected return. Only entry state is model input; return state is test evidence.',
            'event_names':replay_data['original_music_clock']['event_names'],
            'entry':entry,'expected':expected}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','replay','output'):
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    args.output.write_bytes(gzip.compress(json.dumps(prepare(args.capture,args.trace,args.replay),separators=(',',':')).encode(),mtime=0))
