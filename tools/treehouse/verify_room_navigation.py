"""Keep friend selection intact when room narration blocks navigation.

Only visible controls change gameplay; advance() runs the production clock.
"""
from pathlib import Path
import argparse
import hashlib
import json
from itertools import product
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            for stage, action in product(['narration', 'rolling'], ['Choose another friend', 'home', 'Go outside', 'Back', 'Make some music']):
                context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch)
                page = context.new_page()
                page.set_default_timeout(5000)
                page.add_init_script('requestAnimationFrame=()=>0;')
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(html.resolve().as_uri())
                label = ('touch' if touch else 'desktop') + ': ' + stage + ': ' + action

                def press(name):
                    control = page.locator('#home') if name == 'home' else page.get_by_role('button', name=name, exact=True)
                    control.tap() if touch else control.click()
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')

                def settle():
                    return page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}''')

                def check(name, expression):
                    passed = bool(page.evaluate(expression))
                    report['checks'].append(dict(name=label+': '+name, passed=passed))

                try:
                    press('Choose the girl' if touch else 'Choose the boy')
                    if not settle():
                        raise AssertionError('Entrance did not settle')
                    press('Read the calendar')
                    if stage == 'rolling':
                        page.evaluate('()=>{let n=0;while(room.calendarRead&&n++<5000)advance();render();}')
                    active = 'room.calendarRead' if stage == 'narration' else 'room.height!==room.target'
                    check('calendar action active', 'scene==="inside"&&resident.selected&&'+active)
                    press(action)
                    check('blocked navigation preserves friend', 'scene==="inside"&&resident.selected&&'+active)
                    if not settle():
                        raise AssertionError('Date narration did not settle')
                    check('narration finishes with calendar open', 'scene==="inside"&&resident.selected&&room.open&&!room.busy')
                    press(action)
                    if not settle():
                        raise AssertionError('Navigation did not settle')
                    expected = 'scene==="outside"&&!resident.selected' if action in ['Choose another friend', 'home'] else 'scene==="music"&&resident.selected' if action == 'Make some music' else 'scene==="outside"&&resident.selected'
                    check('navigation works after narration', expected)
                except Exception as e:
                    report['errors'].append(label+': '+str(e))
                context.close()
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.html, args.output) else 1)
