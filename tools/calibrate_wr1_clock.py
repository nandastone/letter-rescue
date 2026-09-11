"""Bound the original IRQ phase using an idle, ordinary-gameplay native interval.

The entity timer must equal the number of admitted gameplay updates since the
chosen origin: no accepted slime action, death, menu, extra wait or counter reset.
Use an interval before movement as calibration, and later movement as validation.
This estimates the IRQ phase, not rendering duration or CPU instruction position.
"""
import argparse
import json
import math
from pathlib import Path

IRQ_SECONDS = 12428.0 / 1193182.0


def calibrate(native, fps, origin, start, end):
    if not native.get('complete') or not math.isfinite(fps) or not 0 < fps <= 1000:
        raise ValueError('Require complete native trace and a valid measured frame rate')
    rows = [row for row in native['samples'] if start <= row['replay_frame'] < end]
    if [row['replay_frame'] for row in rows] != list(range(start, end)) or len(rows) < 2:
        raise ValueError('Calibration requires consecutive native snapshots')
    lower, upper, previous_tick = 0.0, 8 * IRQ_SECONDS, None
    for row in rows:
        tick, timer = row['entity_timer'], row['timer']
        if row['threshold'] != 8 or any(row[key] for key in ('up', 'down', 'left', 'right')):
            raise ValueError('Calibration interval must be idle at the default gate threshold')
        if previous_tick is not None and not 0 <= tick - previous_tick <= 1:
            raise ValueError('Entity timer reset or missed ordinary updates')
        previous_tick = tick
        elapsed = (row['replay_frame'] - origin) / fps
        interrupts = tick * 8 + timer
        lower = max(lower, interrupts * IRQ_SECONDS - elapsed)
        upper = min(upper, (interrupts + 1) * IRQ_SECONDS - elapsed)
    if lower >= upper:
        raise ValueError('No consistent IRQ phase; inspect partial updates, resets, rate and origin')
    return {'source_sha256': native['source_sha256'], 'source_fps': fps,
            'source_start_frame': origin, 'calibration_start_counter': start,
            'calibration_end_counter_exclusive': end, 'samples': len(rows),
            'phase_lower_seconds': lower, 'phase_upper_seconds_exclusive': upper,
            'original_clock_phase_seconds': (lower + upper) / 2,
            'scope': 'IRQ phase under ordinary idle-update assumptions; not a render-completion phase'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--fps', type=float, required=True)
    parser.add_argument('--source-start-frame', type=int, required=True)
    parser.add_argument('--calibration-start', type=int, required=True)
    parser.add_argument('--calibration-end', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = calibrate(json.loads(args.native.read_text()), args.fps, args.source_start_frame,
                           args.calibration_start, args.calibration_end)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f'Clock calibration failed: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
