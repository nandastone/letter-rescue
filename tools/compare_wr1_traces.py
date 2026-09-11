"""Compare clone update samples at exact native frontend frame numbers.

Adjacent-frame matches are diagnostics only and never count as exact matches.
This compares sampled state, not pixels or guaranteed DOS instruction boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path

GROUPS = {
    'position': ('x', 'y', 'gx', 'gy', 'camera_x', 'camera_y', 'world_x', 'world_y'),
    'motion': ('phase', 'sprite', 'facing'),
    'interaction': ('score', 'books_collected', 'active_word', 'active_index',
                    'matched_count', 'mistakes', 'word_offset', 'picture_offset'),
    'background': ('background_frame',),
}


def differences(native, clone, fields):
    return {key: {'native': native.get(key), 'clone': clone.get(key)} for key in fields
            if key not in native or key not in clone or native[key] != clone[key]}


def compare(native, clone, replay, replay_digest):
    if not native.get('complete'):
        raise ValueError('Native capture is incomplete')
    digest = replay.get('source_sha256')
    if not digest or native.get('source_sha256') != digest:
        raise ValueError('Replay and native capture source hashes differ or are missing')
    indexed = {}
    for row in native['samples']:
        frame = row['replay_frame']
        if frame in indexed:
            raise ValueError(f'Duplicate native frame {frame}')
        indexed[frame] = row
    expected_frames = set(range(native['start_frame'], native['end_frame'] + 1))
    if set(indexed) != expected_frames:
        raise ValueError('Native capture has missing or out-of-range frames')
    report = {'source_sha256': digest, 'replay_sha256': replay_digest,
              'scope': 'clone logical-update samples at exact frontend frames',
              'clock': {key: replay.get(key) for key in ('source_start_frame', 'source_fps',
                  'source_clock_quantum_seconds', 'source_clock_phase_seconds',
                  'original_clock_phase_seconds', 'original_start_background_frame', 'synchronization_note')},
              'native_boundary': native.get('boundary'), 'compared': 0, 'exact': 0,
              'outside_capture': 0, 'groups': {name: {'exact': 0, 'mismatches': []} for name in GROUPS},
              'uncompared': ['pixels', 'gruzzles', 'slime', 'sound', 'death/level transitions']}
    seen = set()
    for row in clone:
        if 'source_frame' not in row:
            continue  # Explicit initialization record, not a timed update.
        frame = row['source_frame']
        if frame in seen:
            raise ValueError(f'Duplicate clone frame {frame}')
        seen.add(frame)
        if row.get('source_sha256') != digest:
            raise ValueError('Clone trace lacks matching replay provenance; rerun the clone')
        if not replay_digest or row.get('replay_sha256') != replay_digest:
            raise ValueError('Clone trace was produced with a different replay configuration; rerun it')
        if frame != replay['source_start_frame'] + row['replay_frame']:
            raise ValueError('Clone source frame disagrees with replay slice')
        if not 0 <= row['replay_frame'] < replay['total_frames']:
            raise ValueError('Clone frame outside replay duration')
        # BSV's counter increments AFTER core_run(). Input frame N therefore
        # produces native completed-frame counter N+1 (RetroArch 69a4f0e).
        native_frame = frame + 1
        if native_frame not in indexed:
            report['outside_capture'] += 1
            continue
        report['compared'] += 1
        exact = True
        for name, fields in GROUPS.items():
            delta = differences(indexed[native_frame], row, fields)
            if not delta:
                report['groups'][name]['exact'] += 1
                continue
            exact = False
            adjacent = [offset for offset in (-1, 1) if native_frame + offset in indexed
                        and not differences(indexed[native_frame + offset], row, fields)]
            report['groups'][name]['mismatches'].append({'source_frame': frame,
                'native_completed_frames': native_frame, 'tick': row['tick'],
                'fields': delta, 'adjacent_match_offsets': adjacent})
        report['exact'] += int(exact)
    if not report['compared']:
        raise ValueError('No overlapping timed clone samples')
    report['all_compared_samples_exact'] = report['exact'] == report['compared']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--clone', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare(json.loads(args.native.read_text()),
                         [json.loads(line) for line in args.clone.read_text().splitlines() if line],
                         json.loads(args.replay.read_text()), hashlib.sha256(args.replay.read_bytes()).hexdigest())
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f'Trace comparison failed: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"Exact sampled states: {report['exact']}/{report['compared']}; "
          f"outside native capture: {report['outside_capture']}")
    for name, group in report['groups'].items():
        first = group['mismatches'][:1]
        print(f"{name}: {group['exact']}/{report['compared']}; first mismatch: {first}")
    raise SystemExit(0 if report['all_compared_samples_exact'] else 1)


if __name__ == '__main__':
    main()
