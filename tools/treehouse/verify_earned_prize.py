"""Earn, offer, revisit and reload a magnifying glass through ordinary controls."""
from pathlib import Path
import argparse
import hashlib
import json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], sessions=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            label = 'touch-girl' if touch else 'mouse-boy'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch)
            page = context.new_page()
            page.set_default_timeout(5000)
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('1992-01-01T00:00:00Z');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(html.resolve().as_uri())
            cdp = context.new_cdp_session(page) if touch else None
            actions = []

            def flush():
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')

            def press(name):
                button = page.get_by_role('button', name=name, exact=True)
                button.tap() if touch else button.click()
                flush(); actions.append(name)

            def settle():
                assert page.evaluate('''()=>{const busy=()=>entering||roomTravel||resident.busy||room.busy||rewards.active&&rewards.phase!=='choose'||scene==='nature'&&nature.mode==='quiz'&&(nature.quiz.busy||nature.quiz.winAnimation&&!nature.quiz.winAnimation.done);let n=0;while(busy()&&n++<30000)advance();render();return !busy();}'''), 'Unfinished activity'

            def check(name, expression):
                report['checks'].append(dict(name=label+': '+name, passed=bool(page.evaluate(expression))))

            def position(point):
                page.locator('#game').scroll_into_view_if_needed()
                box = page.locator('#game').bounding_box()
                return dict(x=box['x']+(point[0]+.1)*box['width']/320, y=box['y']+(point[1]+.1)*box['height']/200)

            try:
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Explore nature'); settle(); press('Play the animal guessing game')
                page.locator('#quiz-opponent').select_option('1')
                press('Start the guessing game'); settle()
                for attempt in range(6):
                    press('Roll for the next turn'); settle(); press('Make a guess'); settle()
                    answer = page.evaluate('()=>{const q=nature.quiz;return nature.name(q.cards[q.player][q.secret[q.player]]);}')
                    press('Guess '+answer); settle(); press('Choose a prize'); settle()
                    if page.get_by_role('button', name='Magnifying glass', exact=True).count():
                        press('Magnifying glass'); settle(); break
                    press(page.locator('#controls button').first.inner_text()); settle()
                else:
                    raise AssertionError('Magnifying glass absent after six earned prizes')
                check('game awards magnifying glass', 'resident.objects.some(o=>o.type===2)&&!rewards.active')
                press('Back'); press('Back'); settle()
                origin = page.evaluate('()=>{const r=resident.bounds(resident.objects.find(o=>o.type===2));return [(r[1]+r[3])/2,(r[0]+r[2])/2];}')
                point = position(origin)
                if touch:
                    cdp.send('Input.dispatchTouchEvent', dict(type='touchStart', touchPoints=[dict(**point, id=1)]))
                else:
                    page.mouse.move(**point); page.mouse.down()
                flush(); page.evaluate('advance(16)')
                target = position([169,145])
                if touch:
                    cdp.send('Input.dispatchTouchEvent', dict(type='touchMove', touchPoints=[dict(**target, id=1)]))
                else:
                    page.mouse.move(**target)
                flush(); page.evaluate('advance(2)')
                cdp.send('Input.dispatchTouchEvent', dict(type='touchEnd', touchPoints=[])) if touch else page.mouse.up()
                flush(); settle(); actions.append(dict(drag=2, origin=origin, destination=[169,145]))
                # Source placement 96C5/97AE: released x retained, floor bottom
                # 173 from the original surface table; magnifier size 28 x 26.
                correct = "(()=>{const o=resident.objects.find(o=>o.type===2);return o&&o.inside&&o.state===1&&JSON.stringify(resident.bounds(o))==='[147,155,173,183]';})()"
                check('offered prize settles at original floor position', correct)
                check('offer leaves exactly one prize and no active drag', "resident.objects.filter(o=>o.type===2).length===1&&!resident.drag&&!resident.busy")
                press('Go outside'); settle(); press('Go inside'); settle()
                check('room revisit preserves offered prize position', correct)
                page.reload(); press('Choose the girl' if touch else 'Choose the boy'); settle()
                check('reload preserves offered prize position', correct)
                report['sessions'].append(dict(name=label, actions=actions, prize=page.evaluate('resident.objects.find(o=>o.type===2)')))
            except Exception as error:
                report['errors'].append(label+': '+str(error))
            context.close()
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Fresh mouse/boy and touch/girl games earn the prize through quiz controls, offer it by canvas drag, leave/reenter, and reload. No gameplay state or RNG is installed. Expected returned geometry comes from original object size and floor placement. Native timing, intermediate frames and all prize types remain separate requirements.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raise SystemExit(0 if verify(args.html, args.output) else 1)
