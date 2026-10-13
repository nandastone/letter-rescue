"""Feed a friend, let them tire, and exercise natural/interrupted naps via controls.

Only visible buttons change gameplay. The clock is advanced through production
updates; no hunger, fatigue, pose, inventory or random state is installed.
"""
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
            label = 'touch-girl' if touch else 'desktop-boy'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch, timezone_id='Australia/Brisbane')
            page = context.new_page()
            page.set_default_timeout(5000)
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('1992-01-01T10:00:00Z');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            page.evaluate('room.now=()=>new Date(+new Date(1992,0,1,10)+(tick*1000/TICK_HZ))')
            actions, states = [], []

            def press(name):
                button = page.get_by_role('button', name=name, exact=True)
                button.tap() if touch else button.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                actions.append(name)

            def wait_for(expression, limit=100000):
                result = page.evaluate('''({expression,limit})=>{
                    const predicate=()=>eval(expression), start=tick;
                    while(!predicate()&&tick-start<limit)advance();
                    render();return predicate();
                }''', dict(expression=expression, limit=limit))
                if not result:
                    raise AssertionError('Did not reach: '+expression)

            idle = '!entering&&!roomTravel&&!resident.busy&&!room.busy&&!room.speech.length&&tick>=room.speechDue'

            def check(name, expression):
                passed = bool(page.evaluate(expression))
                report['checks'].append(dict(name=label+': '+name, passed=passed))
                if not passed:
                    raise AssertionError(name)

            def mark(name):
                states.append(dict(name=name, state=page.evaluate('()=>({scene,tick,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,wakeTime:resident.wakeTime?.toISOString()??null,pillow:resident.objects.some(o=>o.type===8),selected:resident.selected})')))

            try:
                press('Choose the girl' if touch else 'Choose the boy')
                wait_for(idle)
                press('Offer the pillow')
                wait_for(idle)
                check('rested friend refuses pillow and returns it', 'resident.pose!==4&&resident.objects.some(o=>o.type===8)&&!resident.wakeTime')
                wait_for('resident.hunger>=3&&'+idle)
                press('Offer an apple')
                wait_for(idle)
                check('hungry friend eats the offered apple', 'resident.hunger===1&&!resident.objects.some(o=>o.type===18)')
                mark('fed')

                for ending in ['natural', 'activity']:
                    wait_for('resident.fatigue>=4&&'+idle)
                    press('Offer the pillow')
                    wait_for(idle)
                    check(ending+' nap starts', 'resident.pose===4&&resident.fatigue===1&&!!resident.wakeTime&&!resident.objects.some(o=>o.type===8)')
                    press('Talk to your friend')
                    wait_for(idle)
                    check(ending+' sleeping friend stays asleep when clicked', 'resident.pose===4&&!!resident.wakeTime')
                    mark(ending+' asleep')
                    if ending == 'natural':
                        press('Go outside')
                        wait_for(idle)
                        check('yard preserves sleeping friend', 'scene==="outside"&&resident.selected&&resident.pose===4')
                        press('Go inside')
                        wait_for(idle)
                        check('room reentry preserves nap', 'scene==="inside"&&resident.pose===4')
                        wait_for('resident.pose!==4&&!resident.wakeTime&&'+idle)
                        check('natural wake restores rested friend and pillow', 'resident.fatigue===1&&resident.objects.some(o=>o.type===8)')
                    else:
                        press('Make some music')
                        wait_for(idle)
                        # A hungry friend may already have changed standing pose
                        # during departure; being awake is the required behavior.
                        check('activity wakes friend and restores pillow', 'scene==="music"&&resident.pose!==4&&resident.fatigue===4&&!resident.wakeTime&&resident.objects.some(o=>o.type===8)')
                        press('Back')
                        wait_for(idle)
                        check('return from activity remains usable', 'scene==="inside"&&resident.selected&&!roomTravel')
                    mark(ending+' awake')
                report['sessions'].append(dict(name=label, actions=actions, states=states))
            except Exception as e:
                report['errors'].append(label+': '+str(e))
                report['sessions'].append(dict(name=label, actions=actions, states=states, final=page.evaluate('()=>({scene,tick,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,roomBusy:room.busy,residentBusy:resident.busy})')))
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
