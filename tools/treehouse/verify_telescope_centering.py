"""Compare the alien telescope image after entering through visible controls."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

DATA = Path(__file__).resolve().parents[2] / 'testing/output/treehouse'


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    reference = DATA / 'maze-activity-tour-native-a'
    native = json.loads((reference / 'run.json').read_text(encoding='utf-8'))
    assert native['passed']
    assert native['content_sha256'] == 'a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c'
    checkpoint = next(c for c in native['checkpoints'] if c['name'] == 'telescope-visit')
    original_path = reference / 'state/telescope-visit.png'
    original = Image.open(original_path).convert('RGB')
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), errors=[], checks=[], pixels={},
                  reference=str(original_path), reference_sha256=hashlib.sha256(original_path.read_bytes()).hexdigest())
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport=dict(width=1360, height=960))
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        try:
            page.goto(html.resolve().as_uri())
            def settle():
                assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy||telescopeBusy())&&n++<10000)advance();render();return n<10000;}'''), 'Animation did not finish'
            page.get_by_role('button', name='Choose the boy', exact=True).click(); settle()
            page.get_by_role('button', name='Look through the telescope', exact=True).click(); settle()
            page.get_by_role('button', name='A little alien', exact=True).click(); settle()
            x, y = checkpoint['after']['pointer']; box = page.locator('#game').bounding_box()
            page.mouse.move(box['x']+(x+.1)*box['width']/320, box['y']+(y+.1)*box['height']/200)
            page.evaluate('render()')
            image = Image.open(BytesIO(base64.b64decode(page.evaluate("canvas.toDataURL().split(',')[1]")))).convert('RGB')
            image.save(output/'alien.png'); delta = ImageChops.difference(image, original); delta.save(output/'alien-difference.png')
            count = sum(a != b for a, b in zip(image.getdata(), original.getdata()))
            report['pixels']['alien'] = dict(exact=count==0, different_pixels=count, bounds=delta.getbbox())
            report['checks'].append(dict(name='ordinary controls reach completed alien view', passed=page.evaluate("scene==='telescope'&&telescope===1&&!roomTravel&&!telescopeBusy()")))
        except Exception as e:
            report['errors'].append(str(e))
        browser.close()
    report['passed'] = not report['errors'] and bool(report['pixels']) and all(x['exact'] for x in report['pixels'].values()) and all(x['passed'] for x in report['checks'])
    report['scope'] = 'Fresh visible-control entrance and alien selection, completed animation, full 320x200 RGB comparison to the original tour endpoint with its pointer coordinates. No clock/seed/game-state injection. Animation time is accelerated; this is a final-image check, not equal animation timing or whole-tour parity.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2)); return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['html', 'output']: parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args(); raise SystemExit(0 if verify(args.html, args.output) else 1)
