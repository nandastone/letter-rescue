"""Translate a recorded mouse route to its observed game-tick intervals."""
import json, struct


def mouse_schedule(reference, names):
    recording = json.loads((reference / 'run.json').read_text(encoding='utf-8'))
    callbacks = [json.loads(line) for line in (reference / 'frames.jsonl').read_text().splitlines()]
    by_run = {}
    for row in callbacks: by_run.setdefault(row['run'], row['original_tick'])
    cursor = max(by_run) + 1 - sum(a['frames'] for a in recording['actions'])
    prior = None; press = None; release = None; held = False; result = {}
    for action in recording['actions']:
        down = bool(action.get('mouse', {}).get('left'))
        if down and not held: press = by_run[cursor]
        if held and not down: release = by_run[cursor]
        held = down; cursor += action['frames']
        if name := action.get('capture'):
            end = struct.unpack_from('<I', (reference / 'state' / (name + '.ram-0')).read_bytes(), 0x323f0 + 0x201e)[0]
            if name in names:
                result[name] = dict(click=press is not None, before=0 if prior is None or press is None else press - prior,
                    held=0 if press is None else release - press, total=0 if prior is None else end - prior)
                assert 0 <= result[name]['before'] + result[name]['held'] <= result[name]['total']
                prior = end
            press = release = None
    assert list(result) == names
    return result
