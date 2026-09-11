"""Validate instruction observations and prepare an independent WR1 replay fixture.

Requires the six main-loop hooks from wr1_core_trace.patch and a paired capture.
Calibrates only an idle prefix. Does not copy gameplay outcomes into clone input.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

STAGES = (0x444, 0x447, 0xa1e, 0xa43, 0xd44, 0xd72)
# Newer observers also expose contact return and the entity-call boundaries.
# Accept the complete extended sequence, never arbitrary extra/missing hooks.
EXTENDED_STAGES = (0x444, 0x447, 0xa1e, 0xa23, 0xa39, 0xa3e, 0xa43, 0xd44, 0xd72)
IRQ_SECONDS = 12428.0 / 1193182.0


def gameplay_instructions(trace):
    """Recognize a recap's abandoned two-hook admission, never an arbitrary gap."""
    instructions, interruptions = [], []
    active = None
    for row in trace:
        if row['event'] == 'instruction':
            if active is not None:
                raise ValueError('Gameplay instruction inside unfinished recap')
            instructions.append(row)
        elif row['event'] == 'lifecycle' and row['ip'] == 0x151c:
            if active is not None or tuple(r['ip'] for r in instructions[-2:]) != STAGES[:2]:
                raise ValueError('Recap must interrupt exactly the admission pair')
            active = {'kind': 'recap', 'admission': instructions[-2:], 'begin': row}
            del instructions[-2:]
        elif row['event'] == 'lifecycle' and row['ip'] == 0x194f:
            if active is None:
                raise ValueError('Recap return without entry')
            if row['pic_ms'] < active['begin']['pic_ms']:
                raise ValueError('Recap time decreased')
            active['end'] = row
            interruptions.append(active)
            active = None
    if active is not None:
        raise ValueError('Unfinished recap; request an explicit completed-update prefix')
    return instructions, interruptions


def instruction_groups(instructions, trace):
    """A pit rescue bypasses normal actors/render hooks, then completes the tick.

    Accept that three-hook path only with the observed rescue entry and return.
    Every ordinary update still requires all six hooks in order.
    """
    group = []
    for row in instructions:
        group.append(row)
        if row['ip'] != STAGES[-1]:
            continue
        stages = tuple(r['ip'] for r in group)
        if stages == STAGES[:2]+STAGES[-1:]:
            life = [r for r in trace if r['event']=='lifecycle'
                    and group[1]['pic_ms'] < r['pic_ms'] < row['pic_ms']]
            if not row['death'] or not any(r['ip']==0x8b1 for r in life) or not any(r['ip']==0x969 for r in life):
                raise ValueError('Short update lacks a complete observed rescue')
        elif stages not in (STAGES, EXTENDED_STAGES):
            raise ValueError('Instruction stages are missing or out of order')
        yield group
        group = []
    if group:
        raise ValueError('Instruction trace has a missing or partial update')


def prepare(capture, trace, replay, start=350, end=420, through_tick=None):
    if not capture.get('complete') or capture['source_sha256'] != replay['source_sha256']:
        raise ValueError('Require complete capture from the same source replay')
    loads = [i for i, row in enumerate(trace) if row['event'] == 'load']
    if len(loads) != 1:
        raise ValueError('Require exactly one initial savestate load; checkpoints need separate epochs')
    trace = trace[loads[0] + 1:]
    frontend_rows = [row for row in trace if row['event'] == 'frontend']
    frames = {row['call']: row for row in frontend_rows}
    if len(frames) != len(frontend_rows):
        raise ValueError('Duplicate frontend call number')
    instructions = [row for row in trace if row['event'] == 'instruction']
    interruptions = []
    ignored_instructions = 0
    if through_tick is not None:
        ends = [i + 1 for i, row in enumerate(instructions) if row['ip'] == STAGES[-1]]
        if through_tick < 1 or len(ends) < through_tick:
            raise ValueError('Requested completed-update prefix is unavailable')
        end_index = ends[through_tick - 1]
        ignored_instructions = len(instructions) - end_index
        instructions = instructions[:end_index]
    else:
        instructions, interruptions = gameplay_instructions(trace)
    if not instructions:
        raise ValueError('Instruction trace has a missing or partial update')
    updates = []
    for group in instruction_groups(instructions, trace):
        if any(a['pic_ms'] > b['pic_ms'] for a, b in zip(group, group[1:])):
            raise ValueError('Emulated time decreased inside an update')
        if group[-1]['main_iteration'] != (group[0]['main_iteration'] + 1) % 65536:
            raise ValueError('Main-loop iteration did not increment exactly once')
        if updates and group[0]['main_iteration'] != updates[-1]['completed']['main_iteration']:
            raise ValueError('Missing main-loop iteration')
        updates.append({'tick': len(updates)+1, 'begin': group[0], 'completed': group[-1],
                        'stages': [{key: row[key] for key in ('ip', 'pic_ms', 'launch_call',
                            'background_frame', 'render_page', 'display_page')} for row in group]})
    # The worker launched by call C is joined by call C+1. Its stable memory
    # corresponds to paused replay counter C. Validate this against the UDP data.
    compared = 0
    for row in capture['samples']:
        frontend = frames.get(row['replay_frame'] + 1)
        if frontend is None:
            continue  # Last worker can finish after the last observed frontend call.
        for key in ('x','y','gx','gy','sprite','phase','background_frame','entity_timer','timer','score'):
            if frontend.get(key) != row[key]:
                raise ValueError(f'Worker/front-end mapping mismatch: counter {row["replay_frame"]}, {key}')
        compared += 1
    if not compared:
        raise ValueError('No validated worker/front-end correspondence')
    fps = replay['source_fps']
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('Require a measured source frame rate')
    period = 1000 / fps
    lower, upper = -math.inf, math.inf
    irq_lower, irq_upper = 0.0, IRQ_SECONDS * 8
    origin = replay['source_start_frame']
    origin_ms = round(frames[origin+1]['pic_ms'])
    for counter in range(start, end):
        call = counter+1
        row = frames[call]
        if any(row[key] for key in ('up','down','left','right')) or row['threshold'] != 8:
            raise ValueError('Clock calibration must precede movement at the default timer threshold')
        time_ms = round(row['pic_ms'])
        if abs(row['pic_ms'] - time_ms) > .001:
            raise ValueError('Observed frame handoff is not on the expected millisecond grid')
        lower = max(lower, time_ms - 1 - call*period)
        upper = min(upper, time_ms - call*period)
        interrupts = row['entity_timer']*8 + row['timer']
        elapsed = (time_ms - origin_ms)/1000
        irq_lower = max(irq_lower, interrupts*IRQ_SECONDS - elapsed)
        irq_upper = min(irq_upper, (interrupts+1)*IRQ_SECONDS - elapsed)
    if lower >= upper or irq_lower >= irq_upper:
        raise ValueError('No consistent frame/IRQ phase in the idle calibration interval')
    clock_offset = (lower+upper)/2
    result = dict(replay)
    first = updates[0]['begin']
    if 'gruzzle_difficulty' in first:
        result['original_entity_start'] = {key: first[key] for key in (
            'rng','gruzzles','entity_timer','gruzzle_difficulty','gruzzle_cadence','slime_used')}
    if 'picture_timers' in first:
        result['original_picture_start'] = {key: first[key] for key in
            ('picture_timers','picture_frames','picture_animation_enabled')}
    result.update(source_clock_quantum_seconds=.001,
                  source_clock_phase_seconds=((clock_offset+(origin+1)*period)%1)/1000,
                  original_clock_phase_seconds=(irq_lower+irq_upper)/2,
                  synchronization_note='Frame and IRQ phases calibrated only from idle native counters '
                  f'{start}..{end-1}. Millisecond handoff clock; no movement states or future update schedule copied.')
    fixture = {key: capture[key] for key in ('source_sha256','exe_sha256','core_sha256')}
    fixture.update(complete=True, core_revision='db325ff427e3d0df2e6c38bc75b00b6771e03b38',
                   boundary='before WR1 instruction 0096:0d72 / file 0x40d2',
                   calibrated_counters=[start,end], validation_input_start_frame=end,
                   frontend_mapping_samples=compared, updates=updates,
                   clock_bounds_ms=[lower,upper], irq_phase_bounds_seconds=[irq_lower,irq_upper],
                   frontend_clock=[{'call': row['call'], 'pic_ms': row['pic_ms']} for row in frames.values()])
    if interruptions:
        fixture['interrupted_admissions'] = interruptions
    if through_tick is not None:
        fixture['comparison_prefix'] = {'through_tick': through_tick,
            'ignored_later_instructions': ignored_instructions,
            'note':'Explicit completed-update prefix; the full source trace remains hashed and preserved.'}
    return result, fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture','trace','replay','output','fixture'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--through-tick', type=int,
                        help='Explicitly compare a completed-update prefix before an unimplemented cutscene')
    args = parser.parse_args()
    try:
        trace_bytes = args.trace.read_bytes()
        capture = json.loads(args.capture.read_text())
        digest = hashlib.sha256(trace_bytes).hexdigest()
        if capture.get('instruction_trace_sha256',digest) != digest:
            raise ValueError('Instruction trace hash disagrees with capture metadata')
        replay, fixture = prepare(capture,
            [json.loads(line) for line in trace_bytes.splitlines() if line], json.loads(args.replay.read_text()),
            through_tick=args.through_tick)
        replay['instruction_trace_sha256'] = fixture['instruction_trace_sha256'] = digest
        for path, data in ((args.output,replay),(args.fixture,fixture)):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    except (ValueError,KeyError,OSError) as error:
        parser.exit(2,f'Boundary preparation failed: {error}\n')
    print(f'Validated {len(fixture["updates"])} completed updates; prepared calibrated replay {args.output}')


if __name__ == '__main__':
    main()
