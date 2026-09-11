"""Compare real clone updates to native instruction-boundary observations.

Pairs by explicit logical update number, checks entry inputs and entry frontend
frame separately from completed state. Never shifts samples to find a match.
"""
import argparse
import hashlib
import json
from pathlib import Path
from compare_wr1_traces import GROUPS, differences
from json_evidence import read as read_evidence

FIELDS = tuple(key for group in GROUPS.values() for key in group) + (
    'idle_ticks','left_index','right_index','gruzzles','rng','entity_timer','gruzzle_count')


def compare(fixture, clone, replay, replay_digest):
    if not fixture.get('complete') or fixture['source_sha256'] != replay['source_sha256']:
        raise ValueError('Boundary fixture is incomplete or belongs to another replay')
    if fixture['instruction_trace_sha256'] != replay.get('instruction_trace_sha256'):
        raise ValueError('Replay clock calibration belongs to a different native instruction trace')
    timed = {}
    for row in clone:
        if 'source_frame' not in row:
            continue
        if row['tick'] in timed:
            raise ValueError('Duplicate clone update')
        if row.get('replay_sha256') != replay_digest or row.get('source_sha256') != fixture['source_sha256']:
            raise ValueError('Clone trace has stale or missing replay provenance')
        if row['source_frame'] != replay['source_start_frame'] + row['replay_frame']:
            raise ValueError('Clone input/source frame mapping is invalid')
        timed[row['tick']] = row
    report = {'source_sha256': fixture['source_sha256'], 'replay_sha256': replay_digest,
              'instruction_trace_sha256': fixture['instruction_trace_sha256'],
              'boundary': fixture['boundary'], 'compared': 0, 'completed_state_exact': 0,
              'validation_updates': 0, 'validation_exact': 0, 'mismatches': [],
              'missing_clone_updates': [], 'expected_updates': len(fixture['updates']),
              'scope': 'entry inputs/frame and completed movement/interaction/background/actor/RNG state; excludes pixels'}
    seen = set()
    for update in fixture['updates']:
        tick = update['tick']
        if tick in seen:
            raise ValueError('Duplicate native update')
        seen.add(tick)
        begin, completed = update['begin'], update['completed']
        if begin['ip'] != 0x444 or completed['ip'] != 0xd72:
            raise ValueError('Unexpected native instruction boundary')
        validation = begin['launch_call'] - 1 >= fixture['validation_input_start_frame']
        report['validation_updates'] += int(validation)
        if tick not in timed:
            report['missing_clone_updates'].append(tick)
            continue
        row = timed[tick]
        state_delta = differences(completed,row,FIELDS)
        # Newer probes include action state; old movement fixtures remain valid.
        state_delta.update(differences(completed,row,tuple(
            key for key in ('slime_used','action_busy','death','slime_pickups','miss_timer','miss_x','miss_y','mystery_prefix','mystery_pickups','picture_timers','picture_frames','picture_animation_enabled','reward_timer','reward_x','reward_y','reward_bonus','drips','words','word_cursor','level_index','door_state','recap_pending','slime_ever_used','entrance_timer','gruzzle_move_timers') if key in completed)))
        input_delta = {key: {'native': begin[key], 'clone': row.get('held',{}).get(key)}
                       for key in ('up','down','left','right')
                       if key not in row.get('held',{}) or bool(begin[key]) != row['held'][key]}
        if 'slime_request' in row.get('held', {}) and 'slime_request' in begin:
            if bool(begin['slime_request']) != row['held']['slime_request']:
                input_delta['slime_request'] = {'native': begin['slime_request'], 'clone': row['held']['slime_request']}
        frame_exact = begin['launch_call'] == row['source_frame'] + 1
        report['compared'] += 1
        report['completed_state_exact'] += int(not state_delta)
        if validation:
            report['validation_exact'] += int(not state_delta and not input_delta and frame_exact)
        if state_delta or input_delta or not frame_exact:
            report['mismatches'].append({'tick':tick, 'validation':validation,
                'state':state_delta, 'inputs':input_delta,
                'native_entry_counter':begin['launch_call'], 'clone_entry_counter':row['source_frame']+1})
    if not report['validation_updates']:
        raise ValueError('No validation updates after calibration')
    report['all_validation_updates_exact'] = (not report['missing_clone_updates']
        and report['validation_exact'] == report['validation_updates'])
    report['clone_updates_beyond_fixture'] = len(set(timed)-seen)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('native','clone','replay','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    try:
        report = compare(read_evidence(args.native),
            [json.loads(line) for line in args.clone.read_text().splitlines() if line],
            json.loads(args.replay.read_text()),hashlib.sha256(args.replay.read_bytes()).hexdigest())
    except (ValueError,KeyError,OSError) as error:
        parser.exit(2,f'Boundary comparison failed: {error}\n')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"Completed state: {report['completed_state_exact']}/{report['compared']}; "
          f"validation including entry frame and inputs: {report['validation_exact']}/{report['validation_updates']}")
    print(f"Outside fixture: {report['clone_updates_beyond_fixture']} clone updates; mismatches: {report['mismatches']}")
    raise SystemExit(0 if report['all_validation_updates_exact'] else 1)


if __name__ == '__main__':
    main()
