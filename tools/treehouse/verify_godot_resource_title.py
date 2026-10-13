"""Compare Godot-generated title and child-selection resource ownership.

Executable/platform/archive inputs generate the complete starting state. Script
and sound completion events advance the ownership model without timing claims.
Selection additionally supplies the default cloud and two visible credit
changes from the route. Native heap/catalog snapshots are comparison outputs;
converted shape pixels, live event integration and full gameplay remain open.
Room comparisons supply noon, cloud 5 and the five defined initial objects.
The optional board comparison supplies one native entry RNG seed to the
production board rules; it does not prove continuous upstream RNG or clocks.
"""
import argparse
import hashlib
import json
import subprocess
import struct
from pathlib import Path

from resource_startup_inputs import extract
from verify_resource_growth import ROOT, DATA, digest, arena_state
from verify_near_heap import parse as parse_near
from verify_dos_resource_startup import mcbs
from memory_catalog import read_catalogs, read_files


def verify(godot, output, entrance=False, selection='', assets=None, room=False, transfer=False, board=False, play=False, roll=False, move=False):
    output.mkdir(parents=True, exist_ok=False)
    roll = roll or move
    play = play or roll
    board = board or play
    transfer = transfer or board
    room = room or transfer
    selection = selection or ('boy' if room else '')
    if transfer and selection != 'boy':
        raise ValueError('Native transfer reference covers the boy route')
    entrance = entrance or bool(selection)
    bundle = json.loads(assets.read_text(encoding='utf-8')) if assets else None
    inputs = bundle['resource_ownership'] if bundle else extract(DATA / 'source/The_Treehouse_1991.zip')
    parameters = dict(inputs=inputs, entrance=entrance, selection=selection, room=room, transfer=transfer, board=board, play=play, roll=roll, move=move)
    config = inputs['scenes']['entrance']
    boundaries = [('background-palette', 'resource-startup-palette-a', 1), ('title-palette', 'resource-startup-palette-a', 3),
                  ('animation-before', 'resource-startup-animation-a', 0), ('animation-after', 'resource-startup-animation-a', 1),
                  ('animation-2-before', 'resource-startup-animation-a', 2), ('animation-2-after', 'resource-startup-animation-a', 3),
                  ('animation-3-before', 'resource-startup-animation-a', 4), ('animation-3-after', 'resource-startup-animation-a', 5),
                  ('title-complete', 'resource-startup-palette-a', 4)]
    if entrance:
        boundaries.extend((f"interface-palette-{p['id']}", 'resource-startup-palette-a', 5+2*i) for i, p in enumerate(config['palettes']))
        boundaries.extend((f"child-palette-{p['id']}", 'resource-startup-palette-a', 17+2*i) for i, p in enumerate(config['childPalettes']))
        boundaries.extend([('entrance-animation-before', 'resource-startup-animation-a', 6), ('entrance-animation-after', 'resource-startup-animation-a', 7),
                           ('entrance-animation-2-before', 'resource-startup-animation-a', 8), ('entrance-animation-2-after', 'resource-startup-animation-a', 9),
                           ('entrance-animation-3-before', 'resource-startup-animation-a', 10), ('entrance-animation-3-after', 'resource-startup-animation-a', 11),
                           ('entrance-ready', 'resource-startup-entrance-a', 1)])
    if selection:
        boundaries.append(('selection-before', f'resource-selection-{selection}-a', 0))
        for i in range(3):
            boundaries.extend([(f'selection-animation-{i+1}-before', f'resource-selection-animation-{selection}-a', 12+2*i),
                               (f'selection-animation-{i+1}-after', f'resource-selection-animation-{selection}-a', 13+2*i)])
        boundaries.append(('selection-complete', f'resource-selection-{selection}-a', 1))
    if room:
        boundaries.extend([('room-before', f'resource-room-{selection}-a', 0), ('room-complete', f'resource-room-{selection}-a', 1)])
        if selection == 'boy':
            boundaries.extend((f"room-palette-{p['id']}", 'resource-room-palette-boy-a', 21+2*i)
                              for i, p in enumerate(inputs['scenes']['rooms']['boy']['palettes']))
            boundaries.extend([('room-objects-before', 'resource-room-objects-boy-a', 0), ('room-objects-after', 'resource-room-objects-boy-a', 1)])
    if transfer:
        boundaries.extend([('transfer-before','resource-room-board-transfer-a',0),
                           ('transfer-animation-before','resource-room-board-animation-a',18),('transfer-animation-after','resource-room-board-animation-a',19),
                           ('bubble-animation-before','resource-room-board-animation-a',20),('bubble-animation-after','resource-room-board-animation-a',21),
                           ('transfer-complete','resource-room-board-transfer-a',1),
                           ('room-release-before','resource-room-board-release-a',0),('room-release-after','resource-room-board-release-a',1)])
    if board:
        parameters['board_tables'] = (bundle['boardgame'] if bundle else
                                      json.loads((ROOT / 'treehouse-demo/boardgame-tables.json').read_text(encoding='utf-8')))
        boundaries.append(('board-before','resource-board-start-palette-a',32))
        boundaries.extend((f"board-palette-{p['id']}",'resource-board-start-palette-a',33+2*i)
                          for i,p in enumerate(inputs['scenes']['board']['palettes']))
        boundaries.extend([('board-background-before','resource-board-start-palette-a',44),('board-background-after','resource-board-start-palette-a',45),
                           ('board-options-before','resource-board-start-palette-a',46),('board-options-after','resource-board-start-palette-a',47),
                           ('board-options-painted','resource-board-options-a',1)])
    if play:
        boundaries.extend([('board-play-before','resource-board-play-a',0),
                           ('board-restart-before','resource-board-restart-a',0),
                           ('board-redraw-after','resource-board-redraw-a',1),
                           ('board-dashboard-before','resource-board-dashboard-a',0),
                           ('board-dashboard-after','resource-board-dashboard-a',1),
                           ('board-play-after','resource-board-play-a',1)])
    if roll:
        boundaries.extend([('board-roll-before','resource-board-first-roll-a',0),
                           ('board-roll-faces-before','resource-board-roll-faces-a',0),
                           ('board-roll-faces-after','resource-board-roll-faces-a',1),
                           ('board-roll-after','resource-board-first-roll-a',1)])
        run = json.loads((DATA/'resource-board-first-roll-a/run.json').read_text(encoding='utf-8'))
        events = run['events']
        tick = next(e['pit'] for e in events if e['label']=='roll.click')
        parameters['expected_roll_prompts'] = [[e['pit']-tick,e['stack'][4] if e['stack'][4]<32768 else e['stack'][4]-65536]
                                               for e in events if e['label']=='hint.draw']
        parameters['expected_roll_sounds'] = [[e['pit']-tick,e['stack'][2]] for e in events if e['label']=='sound.play']
        parameters['expected_roll_complete'] = next(e['pit']-tick for e in events if e['label']=='roll.complete')
    if move:
        boundaries.extend([('board-move-before','resource-board-move-a',0),
                           ('board-movement-before','resource-board-movement-a',0),
                           ('board-movement-after','resource-board-movement-a',1),
                           ('board-landing-before','resource-board-move-a',1)])
        run = json.loads((DATA/'resource-board-move-a/run.json').read_text(encoding='utf-8'))
        parameters['move_target'] = run['move_target']
        events = run['events']
        tick = next(e['pit'] for e in events if e['label']=='node.flash')
        end = next(i for i,e in enumerate(events) if e['label']=='landing.begin')
        parameters['expected_move_ticks'] = [[e['label'],e['pit']-tick] for e in events[:end+1]
                                             if e['label'] in ['movement.begin','pawn.paint','movement.end','landing.begin']]
    expected, references = {}, {}
    for label, name, index in boundaries:
        folder = DATA / name
        run = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
        assert run['passed'] and run['fixed_clock']
        references[name] = digest(folder / 'run.json')
        fixture = run['heap'][index]
        path = folder / fixture['path']
        assert digest(path) == fixture['sha256']
        raw = path.read_bytes()
        ss = fixture['ss']
        arena = arena_state(raw, ss)[0]
        payloads = {b['handle']: b.pop('payload') for b in arena['heap']['blocks'] if 'payload' in b}
        expected[label] = dict(arena=arena, near=parse_near(raw, ss), dos=mcbs(raw), files=read_files(raw, ss),
                               catalogs=read_catalogs(raw, ss), payloads=payloads)
        if board and label == 'board-before':
            parameters['board_seed'] = struct.unpack_from('<I',raw,ss*16+0x5290)[0]
        if board and label in ['board-options-before','board-redraw-after']:
            ds = ss*16
            parameters['expected_game' if label=='board-options-before' else 'expected_started_game'] = dict(seed=struct.unpack_from('<I',raw,ds+0x5290)[0],nodes=list(struct.unpack_from('<2h',raw,ds+0x52c4)),
                                              directions=list(struct.unpack_from('<2h',raw,ds+0x5734)),balances=list(struct.unpack_from('<2h',raw,ds+0x5a0c)),
                                              types=list(struct.unpack_from('<24h',raw,ds+0x59da)))
        if roll and label=='board-roll-after':
            parameters['expected_rolled_game'] = dict(seed=struct.unpack_from('<I',raw,ss*16+0x5290)[0],
                                                     remaining=struct.unpack_from('<h',raw,ss*16+0x5276)[0])
        if roll and label=='board-roll-before':
            parameters['roll_hint_countdown'] = struct.unpack_from('<H',raw,ss*16+0x201a)[0]
        if move and label=='board-landing-before':
            parameters['expected_landing_game'] = dict(seed=struct.unpack_from('<I',raw,ss*16+0x5290)[0],
                 remaining=struct.unpack_from('<h',raw,ss*16+0x5276)[0],nodes=list(struct.unpack_from('<2h',raw,ss*16+0x52c4)),
                 directions=list(struct.unpack_from('<2h',raw,ss*16+0x5734)))
    (output / 'fixture.json').write_text(json.dumps(parameters),encoding='utf-8')
    with (output / 'godot.log').open('w', encoding='utf-8') as log:
        process = subprocess.run([str(godot), '--headless', '--path', str(ROOT / 'treehouse-godot'),
                                  '--script', 'testing/check_resource_title.gd', '--', str(output.resolve())],
                                 stdout=log, stderr=subprocess.STDOUT, timeout=90)
    log = (output / 'godot.log').read_text(encoding='utf-8')
    if process.returncode or 'ERROR' in log:
        print(log[:8000])
        return False
    actual = json.loads((output / 'godot.json').read_text(encoding='utf-8'))
    checks = actual['checks']
    for label, state in expected.items():
        value = actual['stages'].get(label, {})
        for field in ['arena', 'near', 'dos', 'files', 'catalogs']:
            equal = value.get(field) == state[field]
            check = dict(name=f'{label} {field}', passed=equal)
            if equal:
                check['state_sha256'] = hashlib.sha256(json.dumps(state[field], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            else:
                check.update(expected=state[field], actual=value.get(field))
            checks.append(check)
        payloads = {int(k): v for k, v in value.get('payloads', {}).items()}
        differences = {k: dict(expected=state['payloads'].get(k), actual=v) for k, v in payloads.items() if state['payloads'].get(k) != v}
        checks.append(dict(name=f'{label} modeled payloads', passed=bool(payloads) and not differences,
                           compared=len(payloads), differences=differences))
    report = dict(passed=all(c['passed'] for c in checks), checks=checks, scope=__doc__, references=references,
                  stages=list(actual['stages']), entrance=entrance, selection=selection, room=room, transfer=transfer, board=board, play=play, roll=roll, move=move,
                  movement_timing=actual.get('movement_timing'),
                  board_semantic_seed=parameters.get('board_seed'),
                  roll_semantic_hint_countdown=parameters.get('roll_hint_countdown'),
                  semantic_inputs=dict(cloud=5, credit_changes=2, hour=12, minute=0, objects=[9,20,8,10,6]) if room else dict(cloud=5,credit_changes=2) if selection else {},
                  source_files={p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT / 'treehouse-godot/scripts').glob('*.gd'))},
                  extractor_sha256=digest(ROOT / 'tools/treehouse/resource_startup_inputs.py'),
                  verifier_sha256=digest(Path(__file__)), test_sha256=digest(ROOT / 'treehouse-godot/testing/check_resource_title.gd'),
                  asset_bundle_sha256=digest(assets) if assets else None, input_sha256=digest(output / 'fixture.json'),
                  full_game_parity=False, playable_integrated=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(checks), failures=[c['name'] for c in checks if not c['passed']])))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--entrance', action='store_true')
    parser.add_argument('--selection', choices=['boy', 'girl'], default='')
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--room', action='store_true')
    parser.add_argument('--transfer', action='store_true')
    parser.add_argument('--board', action='store_true')
    parser.add_argument('--play', action='store_true')
    parser.add_argument('--roll', action='store_true')
    parser.add_argument('--move', action='store_true')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot, args.output, args.entrance, args.selection, args.assets, args.room, args.transfer, args.board, args.play, args.roll, args.move) else 1)
