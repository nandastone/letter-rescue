"""Start a native replay at a visually verified post-load frontend handoff.

One initial state is supplied to the clone. Only the idle prefix calibrates
clock phase; subsequent states are kept exclusively in the comparison fixture.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from prepare_wr1_boundaries import IRQ_SECONDS, prepare

MOTION = ('x', 'y', 'gx', 'gy', 'camera_x', 'camera_y', 'phase', 'sprite',
          'facing', 'background_frame', 'idle_ticks', 'left_index', 'right_index')
ACTORS = ('rng', 'gruzzles', 'entity_timer', 'gruzzle_difficulty', 'gruzzle_cadence',
          'slime_used', 'slime_ever_used', 'render_page', 'miss_timer', 'miss_x', 'miss_y')
PICTURES = ('picture_timers', 'picture_frames', 'picture_animation_enabled')
FRESH_ZERO = ('active_word', 'matched_count', 'mistakes', 'books_collected',
              'mystery_prefix', 'reward_timer', 'miss_timer', 'action_busy',
              'death', 'door_state', 'recap_pending', 'slime_used', 'slime_ever_used')


def video_checkpoint(initial):
    """Only hardware state at the starting handoff, never later observations."""
    result = {'page': initial['display_page']}
    if 'vga_timing' in initial:
        vga = initial['vga_timing']
        result.update(period=vga['vtotal']/1000, retrace=vga['vrstart']/1000,
                      part_period=vga['parts']/1000,
                      frame_start=(vga['frame_start']-initial['pic_ms'])/1000)
    return result


def prepare_level_start(capture, trace, replay, start_counter, level=2, calibration_end=6420):
    # Reuse the strict instruction-order and frontend/capture correspondence checks.
    _, full = prepare(capture, trace, replay, start=350, end=390)
    first_on_level = next(u for u in full['updates'] if u['begin']['level_index'] == level-1
                          and u['begin']['door_state'] == 0)
    reset = [r for r in trace if r['event'] == 'lifecycle' and r['ip'] == 0xcb5
             and r['level_index'] == level-1 and r['pic_ms'] < first_on_level['begin']['pic_ms']][-1]
    frames = {r['call']: r for r in trace if r['event'] == 'frontend'}
    initial = frames[start_counter+1].copy()
    origin = start_counter
    if not origin < calibration_end < replay['source_end_frame']:
        raise ValueError('Require post-load origin < calibration end < replay end')
    first = next(u for u in full['updates'] if u['begin']['pic_ms'] > initial['pic_ms'])
    begin = first['begin']
    previous = full['updates'][first['tick']-2]['completed']
    if previous['level_index'] != level-1 or previous['pic_ms'] > initial['pic_ms']:
        raise ValueError('Initial checkpoint must follow a completed render on the loaded level')
    for key in ('idle_ticks', 'left_index', 'right_index'):
        initial[key] = previous[key]  # Latest completed main-loop locals at this handoff.
    for key in MOTION + ACTORS + PICTURES + ('entrance_timer','drips'):
        if initial[key] != begin[key]:
            raise ValueError(f'Initial handoff is not a stable pre-update state: {key}')
    if any(initial[k] != 0 for k in FRESH_ZERO):
        raise ValueError('Only untouched, freshly loaded levels are supported')
    if initial['entrance_timer'] <= 10:
        raise ValueError('Choose the first displayed level frame, before the entrance starts blinking')
    if any(a['state'] != -1 for a in initial['gruzzles']):
        raise ValueError('Initial actor effects are not supported; choose an untouched level')
    period = 1000/replay['source_fps']
    # The game is idle before its first displayed frame too. Those post-reset
    # observations constrain the initial clock, without simulating loading time.
    calibration_start = next(r['call']-1 for r in frames.values()
                             if r['pic_ms'] > reset['pic_ms'])
    lower, upper = -math.inf, math.inf
    irq_lower, irq_upper = 0., IRQ_SECONDS*8
    for counter in range(calibration_start, calibration_end):
        row = frames[counter+1]
        if row['level_index'] != level-1 or row['threshold'] != 8 or any(row[k] for k in ('up','down','left','right')):
            raise ValueError('Calibration must be an idle prefix on the loaded level')
        ms = round(row['pic_ms'])
        if abs(row['pic_ms']-ms) > .001:
            raise ValueError('Frontend handoff is not on the millisecond grid')
        lower = max(lower, ms-1-(counter+1)*period)
        upper = min(upper, ms-(counter+1)*period)
        updates = (row['entity_timer']-initial['entity_timer']+32768) % 65536-32768
        interrupts = updates*8+row['timer']
        elapsed = (ms-round(initial['pic_ms']))/1000
        irq_lower = max(irq_lower, interrupts*IRQ_SECONDS-elapsed)
        irq_upper = min(irq_upper, (interrupts+1)*IRQ_SECONDS-elapsed)
    if lower >= upper or irq_lower >= irq_upper:
        raise ValueError('Idle prefix has no consistent frontend/IRQ clock phase')
    irq_phase = (irq_lower+irq_upper)/2
    if 'pit0_elapsed_ms' in initial:
        if abs(initial['pit0_delay_ms']/1000-IRQ_SECONDS) > 1e-8:
            raise ValueError('Native PIT period is not the WR1 gameplay rate')
        irq_phase = initial['timer']*IRQ_SECONDS+initial['pit0_elapsed_ms']/1000
        if not irq_lower-1e-6 <= irq_phase <= irq_upper+1e-6:
            raise ValueError('Direct PIT phase contradicts idle-prefix timer observations')
    # Preserve the held input at the new origin and every subsequent event.
    held, events = {}, []
    for event in replay['events']:
        absolute = replay['source_start_frame']+event['frame']
        if absolute < origin:
            held[event['action']] = event['pressed']
        else:
            events.append(dict(event, frame=absolute-origin))
    events = [dict(frame=0, action=k, pressed=True) for k,v in held.items() if v]+events
    if any(e['frame'] < calibration_end-origin for e in events):
        raise ValueError('Input events must follow the idle calibration prefix')
    result = {k:v for k,v in replay.items() if not k.startswith('original_')}
    if 'character' in initial:
        result['character'] = 'girl' if initial['character'] else 'boy'
    if 'difficulty' in initial:
        result['difficulty'] = initial['difficulty']
    result.update(level=level, source_start_frame=origin,
                  total_frames=replay['source_end_frame']-origin, events=events,
                  original_level_start={k:initial[k] for k in MOTION + (
                      'score','words','word_cursor','mystery_index','active_index','word_offset','picture_offset','entrance_timer','drips')},
                  original_entity_start={k:initial[k] for k in ACTORS},
                  original_picture_start={k:initial[k] for k in PICTURES},
                  original_video_start=video_checkpoint(initial),
                  source_clock_quantum_seconds=.001,
                  source_clock_phase_seconds=(((lower+upper)/2+(origin+1)*period)%1)/1000,
                  original_clock_phase_seconds=irq_phase,
                  synchronization_note=f'One initial state at post-load counter {origin}; '
                  f'clock phase from idle counters {calibration_start}..{calibration_end-1}. '
                  'No loading-duration requirement, later state injection or resynchronization.')
    if 'gruzzle_move_timers' in initial:
        if initial['gruzzle_move_timers'] != begin['gruzzle_move_timers']:
            raise ValueError('Initial actor cadence slots are not stable')
        result['original_entity_start']['gruzzle_move_timers'] = initial['gruzzle_move_timers']
    updates = [dict(u, tick=u['tick']-first['tick']+1, native_tick=u['tick'])
               for u in full['updates'] if u['tick'] >= first['tick']]
    if any(u['begin']['level_index'] != level-1 for u in updates):
        raise ValueError('Slice must stop before the next level transition')
    fixture = {k:full[k] for k in ('complete','source_sha256','exe_sha256','core_sha256','core_revision','boundary')}
    fixture.update(initial=initial, initial_counter=origin, initial_native_tick=first['tick']-1,
                   loader_return=reset, calibrated_counters=[calibration_start,calibration_end],
                   validation_input_start_frame=calibration_end, updates=updates,
                   clock_bounds_ms=[lower,upper], irq_phase_bounds_seconds=[irq_lower,irq_upper],
                   frontend_clock=[{'call':r['call'],'pic_ms':r['pic_ms']} for r in frames.values()
                                   if calibration_start <= r['call']-1 < calibration_end])
    return result, fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','replay','output','fixture'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--level',type=int,default=2)
    parser.add_argument('--start-counter',type=int,required=True,
                        help='First displayed gameplay counter, verified from native screenshots')
    parser.add_argument('--calibration-end',type=int,required=True)
    args = parser.parse_args()
    raw = args.trace.read_bytes()
    capture = json.loads(args.capture.read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if capture['instruction_trace_sha256'] != digest:
        parser.error('Trace hash disagrees with capture')
    replay, fixture = prepare_level_start(capture,[json.loads(l) for l in raw.splitlines()],
        json.loads(args.replay.read_text()),args.start_counter,args.level,args.calibration_end)
    for path, data in ((args.output,replay),(args.fixture,fixture)):
        data['instruction_trace_sha256'] = digest
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,indent=2)+'\n')
    print(f"Post-load counter {fixture['initial_counter']}; {len(fixture['updates'])} independent updates")


if __name__ == '__main__':
    main()
