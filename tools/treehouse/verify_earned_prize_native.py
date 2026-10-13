"""Join the original quiz win/award to actual use and revisit of its room prize."""
from pathlib import Path
from io import BytesIO
import argparse
import base64
import hashlib
import json
from PIL import Image, ImageChops
from verify_nature_native_journey import ROOT, REFERENCE, verify

FOLLOWUP = ROOT/'testing/output/treehouse/earned-prize-native-f'


def continue_prize(page, report, output):
    native = json.loads((FOLLOWUP/'run.json').read_text(encoding='utf-8'))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert native['complete'] and native['passed']
    assert native['parent_report_sha256'] == digest(REFERENCE/'run.json')
    assert native['restore_sha256'] == digest(REFERENCE/'state/back-to-room.state')
    report['earned_prize_continuation'] = dict(reference=str(FOLLOWUP), reference_sha256=digest(FOLLOWUP/'run.json'), parent_verified=True)
    held = False
    for checkpoint in native['checkpoints']:
        name, expected = 'earned-'+checkpoint['name'], checkpoint['after']
        frames = []
        for action in checkpoint['inputs']:
            box = page.locator('#game').bounding_box()
            x, y = action['point']
            page.mouse.move(box['x']+(x+.1)*box['width']/320, box['y']+(y+.1)*box['height']/200)
            if held != action['left']:
                page.mouse.down() if action['left'] else page.mouse.up()
                held = action['left']
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            frames.extend(page.evaluate('n=>observeNature(n)', action['to_tick']-action['from_tick']))
        if not frames:
            frames = page.evaluate('observeNature(0)')
        actual = page.evaluate('''()=>({scene:{inside:5,outside:4,hollow:14}[scene],seed:gameplayRandom.seed,
          selected:resident.selected,sex:character==='girl'?1:0,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,
          objects:resident.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:resident.drag?.moved&&resident.drag.object===o?resident.drag.rect:resident.bounds(o)}))})''')
        differences = {key: dict(expected=expected[key], actual=actual[key]) for key in ['scene','seed','selected','sex','pose','hunger','fatigue'] if expected[key] != actual[key]}
        expected_objects = [{key:o[key] for key in ['type','state','inside','rect']} for o in expected['objects']]
        if sorted(expected_objects, key=lambda o:o['type']) != sorted(actual['objects'], key=lambda o:o['type']):
            differences['objects'] = dict(expected=expected_objects, actual=actual['objects'])
        original = Image.open(FOLLOWUP/'state'/f"{checkpoint['name']}.png").convert('RGB')
        chosen, match = None, None
        for frame in frames:
            generated = Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
            if generated.tobytes() == original.tobytes():
                chosen, match = generated, frame['tick']
                break
        if chosen is None:
            chosen = Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB')
        delta = ImageChops.difference(chosen, original)
        count = sum(a != b for a,b in zip(chosen.getdata(), original.getdata()))
        chosen.save(output/f'{name}.png'); delta.save(output/f'{name}-difference.png')
        report['checks'].append(dict(name=name+' state/objects/random sequence', passed=not differences))
        report['checkpoints'].append(dict(name=name, differences=differences, actual=actual))
        report['pixels'][name] = dict(exact=count==0, different_pixels=count, bounds=delta.getbbox(), generated_tick=match)
        print(name, 'PASS' if not count and not differences else 'FAIL', list(differences), count, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raise SystemExit(0 if verify(args.html, args.output, continuation=continue_prize) else 1)
