"""Build refill, rescue, and mystery-letter input probes from the controlled BSV2.

Keeps the original savestate and startup inputs. No guest memory is modified.
"""
import argparse
import struct
from pathlib import Path
from bsv_replay import frame_start, read_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--probe', choices=['refill','death','letters','letters-complete','level-complete','drips','words'], required=True)
    parser.add_argument('--plan', type=Path, help='JSON actions for the level-complete probe')
    parser.add_argument('--frames', type=int, help='Override probe length; neutral input follows the plan')
    parser.add_argument('--pause-at-step', type=int, help='Insert neutral frames before this plan action')
    parser.add_argument('--pause-frames', type=int, default=0)
    parser.add_argument('--level-two-motion', action='store_true',
                        help='Append fixed-frame walking/jumping after the exit route')
    args = parser.parse_args()
    data = args.source.read_bytes()
    header, frames = read_replay(data)
    if len(frames) != 770:
        parser.error('Expected the 770-frame exploration_controlled.replay')
    count = {'death':1700, 'letters-complete':2300, 'level-complete':5500, 'drips':1100, 'words':2150}.get(args.probe,940)
    if args.frames is not None:
        if args.frames < 770:
            parser.error('--frames must preserve at least the original 770 frames')
        count = args.frames
    if args.probe == 'level-complete':
        if not args.plan:
            parser.error('level-complete requires --plan')
        plan = __import__('json').loads(args.plan.read_text())['actions']
    result = bytearray(data[:frame_start(data, header)])
    for index in range(count):
        source = frames[min(index, len(frames)-1)]
        keys = source['key_events']
        inputs = [dict(e) for e in source['input_events']]
        if index >= 350:
            if args.probe in ['drips','words']:
                # Original Z+L selector, then14 and Enter. Generic Keyboard
                # port2 maps left to Z and right-stick X+ to L. Port0's L/R2
                # buttons type1/4. Use --generic-keyboard-port2 in the capture.
                # Alternate14 and1: selecting the current map takes the cached
                # restart path, which intentionally preserves its seven words.
                phase = 450 + (index-450) % 100 if args.probe == 'words' and 450 <= index < 2050 else index
                select14 = args.probe != 'words' or (index-450) // 100 % 2 == 0
                keys = []
                inputs += [{'port':2,'device':1,'idx':0,'id':6,'value':int(450 <= phase < 456)},
                           {'port':2,'device':5,'idx':1,'id':0,'value':32767 if 450 <= phase < 456 else 0}]
                buttons = {7:False,4:False,5:False,6:False,9:False,
                           10:460 <= phase < 463,13:select14 and 466 <= phase < 469,3:474 <= phase < 478}
            elif args.probe == 'refill':
                buttons = {7:420 <= index < 600 or 624 <= index < 740,
                           4:490 <= index < 518, 6:False,
                           9:any(a <= index < b for a,b in [(620,624),(640,644),(850,854)])}
            elif args.probe == 'death':
                buttons = {7:420 <= index < 710, 4:False, 6:False, 9:False}
            elif args.probe == 'letters':
                buttons = {7:420 <= index < 735, 4:420 <= index < 590 or 596 <= index < 735,
                           6:False, 9:620 <= index < 624}
            elif args.probe == 'letters-complete':
                # Roof route planned against the recovered collision rules.
                # Fixed frontend inputs; no native state or future tick schedule.
                period = 12428 * 8 / 1193182 * 70.086304
                at = lambda step: 420 + round(step * period)
                buttons = {7:420 <= index < at(154), 6:at(154) <= index < at(269),
                           4:420 <= index < at(269) and not (at(30) <= index < at(35) or at(68) <= index < at(69)),
                           9:any(a <= index < a+4 for a in [620,1000,1400,1800])}
            else:
                period = 12428 * 8 / 1193182 * 70.086304
                plan_frame = index
                paused = False
                if args.pause_at_step is not None:
                    pause_start = 420 + round(args.pause_at_step * period)
                    paused = pause_start <= index < pause_start + args.pause_frames
                    if index >= pause_start + args.pause_frames:
                        plan_frame -= args.pause_frames
                step_index = int((plan_frame - 420 + .5) / period) if plan_frame >= 420 and not paused else -1
                held = plan[step_index] if 0 <= step_index < len(plan) else {}
                buttons = {7:held.get('right',False),6:held.get('left',False),
                           4:held.get('up',False),5:held.get('down',False),9:620 <= index < 624}
                if args.level_two_motion and index >= 6420:
                    buttons = {6:index < 6500,7:6506 <= index < 6640,
                               4:index < 6470 or 6530 <= index < 6580,5:False,9:False}
            for event in inputs:
                if event['port'] == 0 and event['device'] == 1 and event['id'] in buttons:
                    event['value'] = int(buttons[event['id']])
        result += struct.pack('<IB', 0, len(keys))
        for e in keys:
            result += struct.pack('<BBHII', e['down'], 0, e['mod'], e['code'], e['character'])
        result += struct.pack('<H', len(inputs))
        for e in inputs:
            result += struct.pack('<BBBBHh', e['port'], e['device'], e['idx'], 0, e['id'], e['value'])
        result += b'f'
    struct.pack_into('<I', result, 24, count)
    read_replay(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)


if __name__ == '__main__':
    main()
