"""Check adaptive maze difficulty survives ordinary exits, reentry and reload."""
from pathlib import Path
import argparse, hashlib, json, re
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], journeys=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            label = 'touch' if touch else 'desktop'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch)
            page = context.new_page(); page.set_default_timeout(5000)
            page.add_init_script("{const D=Date;globalThis.Date=class extends D{constructor(...a){super(...(a.length?a:['2026-09-28T10:00:00+10:00']));}static now(){return new D('2026-09-28T10:00:00+10:00').getTime();}};}requestAnimationFrame=()=>0;")
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            actions = []
            def check(name, expression):
                report['checks'].append(dict(name=label+': '+name, passed=bool(page.evaluate(expression))))
            def settle():
                assert page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='maze'&&maze.busy;while(busy()&&n++<30000)advance();render();return !busy();}'''), 'Animation did not settle'
            def press(name):
                button = page.get_by_role('button', name=name, exact=True)
                button.tap() if touch else button.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))'); actions.append(name)
                if name == 'Play the musical maze':
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")
            def enter():
                press('Play the musical maze')
                if page.get_by_role('button', name='Skip introduction', exact=True).is_visible(): press('Skip introduction')
                settle()
            def choose(correct):
                index = page.evaluate('maze.correct')
                if not correct: index = (index+1)%4
                press(page.get_by_role('button', name=re.compile('^'+['Left','Up','Right','Down'][index]+':')).inner_text()); settle()
            try:
                page.goto(html.resolve().as_uri())
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Make some music'); settle(); enter()
                choose(False)
                check('wrong answer selects easy mode', '!maze.hard&&!gameSave.preferences.advanced')
                choose(True); choose(True)
                check('two consecutive correct answers select advanced mode', 'maze.hard&&gameSave.preferences.advanced')
                press('Back to the piano'); settle(); enter()
                check('advanced mode survives piano exit and reentry', 'maze.hard&&gameSave.preferences.advanced')
                press('Back to the piano'); settle(); page.reload()
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Make some music'); settle(); enter()
                check('advanced mode survives browser reload', 'maze.hard&&gameSave.preferences.advanced')
                choose(False)
                check('wrong answer switches saved advanced mode to easy', '!maze.hard&&!gameSave.preferences.advanced')
                press('Back to the piano'); settle(); enter()
                check('easy mode survives piano exit and reentry', '!maze.hard&&!gameSave.preferences.advanced')
                page.screenshot(path=str(output/(label+'.png')), full_page=True)
                report['journeys'].append(dict(name=label, actions=actions))
            except Exception as e:
                report['errors'].append(label+': '+str(e))
            context.close()
        browser.close()
    report['passed'] = not report['errors'] and len(report['checks'])==12 and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Two fresh mouse/touch sessions with wrong/correct signs, adaptive difficulty, piano exits, reentry and reload. Reads answers only and advances animation ticks. Original difficulty is the shared advanced preference (overlay1 state A8); no CPU or exact timing claim.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2)); return report['passed']


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['html','output']: parser.add_argument('--'+key, type=Path, required=True)
    args=parser.parse_args(); raise SystemExit(0 if verify(args.html,args.output) else 1)
