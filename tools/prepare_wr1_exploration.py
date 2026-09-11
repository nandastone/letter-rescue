"""Prepare a post-load exploration fixture and its independently captured images.

The full native trace is hashed and retained. Only initial state and held inputs
enter the replay; later observations are comparison data exclusively.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from bsv_replay import read_replay
from replay_to_json import frames_to_godot_json
from prepare_wr1_level_start import prepare_level_start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--level', type=int, required=True)
    parser.add_argument('--start-counter', type=int, default=580)
    parser.add_argument('--calibration-end', type=int, default=620)
    parser.add_argument('--directory', type=Path, default=Path('testing/fixtures'))
    args = parser.parse_args()
    if not args.name.replace('_', '').isalnum():
        parser.error('Scenario name must contain only letters, digits, and underscores')
    paths = {kind: args.directory/f'wr1_{args.name}_{kind}.json' for kind in ('replay','boundaries','pixels')}
    if any(p.exists() for p in paths.values()):
        parser.error('Refusing to overwrite existing scenario evidence')
    capture = json.loads(args.capture.read_text())
    digest = hashlib.sha256()
    trace = []
    with args.trace.open('rb') as stream:
        for line in stream:
            digest.update(line)
            row = json.loads(line)
            if row['event'] in ('load','frontend','instruction','lifecycle'):
                trace.append(row)
    trace_hash = digest.hexdigest()
    if trace_hash != capture['instruction_trace_sha256']:
        raise ValueError('Capture and full native trace hashes disagree')
    data = args.replay.read_bytes()
    header, frames = read_replay(data)
    replay = frames_to_godot_json(frames, start_frame=338, end_frame=capture['end_frame'])
    replay.update(source_sha256=hashlib.sha256(data).hexdigest(),
                  source_frame_count=header['frame_count'], source_fps=70.086304)
    replay, fixture = prepare_level_start(capture, trace, replay,
        args.start_counter, args.level, args.calibration_end)
    replay['instruction_trace_sha256'] = fixture['instruction_trace_sha256'] = trace_hash
    manifest = {'source_sha256':replay['source_sha256'],
                'instruction_trace_sha256':trace_hash, 'pairs':[]}
    images = []
    for row in capture['samples']:
        counter = row['replay_frame']
        if 'screenshot' not in row or counter < args.start_counter:
            continue
        source = Path(row['screenshot'])
        name = f'wr1_{args.name}_counter_{counter:06d}.png'
        image_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if counter == args.start_counter:
            manifest.update(initial_file=name, initial_sha256=image_hash)
        else:
            manifest['pairs'].append({'native_counter':counter, 'clone_source_frame':counter-1,
                                     'native_file':name, 'sha256':image_hash})
        images.append((source,args.directory/name))
    if 'initial_file' not in manifest:
        raise ValueError('A native screenshot of the initial checkpoint is required')
    args.directory.mkdir(parents=True, exist_ok=True)
    for source,destination in images:
        if destination.exists():
            raise ValueError(f'Refusing to overwrite native image {destination}')
    for source,destination in images:
        shutil.copyfile(source,destination)
    for kind, value in [('replay',replay),('boundaries',fixture),('pixels',manifest)]:
        paths[kind].write_text(json.dumps(value,indent=2)+'\n')
    states = [u['completed'] for u in fixture['updates']]
    print(json.dumps({'scenario':args.name,'updates':len(states),'images':len(images),
                      'seconds':replay['total_frames']/replay['source_fps'],
                      'unique_positions':len({(r['gx'],r['gy']) for r in states}),
                      'x_range':[min(r['gx'] for r in states),max(r['gx'] for r in states)],
                      'y_range':[min(r['gy'] for r in states),max(r['gy'] for r in states)],
                      'rescues':sum(bool(r['death']) for r in states)}))


if __name__ == '__main__':
    main()
