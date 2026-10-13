"""Exercise stationary click/placement classification through mouse and touch input."""
from pathlib import Path
import argparse
import hashlib
import json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch)
            page = context.new_page()
            page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            cdp = context.new_cdp_session(page) if touch else None
            page.evaluate('''()=>{
                const click=resident.clickObject, release=resident.releaseDrag;
                resident.clickObject=function(o,...args){gestureEvents.push('click');return click.call(this,o,...args);};
                resident.releaseDrag=function*(d){gestureEvents.push('place');yield* release.call(this,d);};
            }''')
            for kind in [1, 2, 7, 8, 12]:
                for duration in [5, 20, 29, 30, 35]:
                    try:
                        page.evaluate('''kind=>{
                            releaseAll();resident.active=null;resident.actionPreparation=null;resident.queue=[];
                            resident.objectTask=null;resident.ambientAnimation=null;resident.objectMotion=null;
                            resident.objects=[];resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;
                            setScene('inside');resident.selected=true;resident.pose=0;room.leave();room.height=room.target=28;
                            balloon.hidden=true;const o=resident.create(kind);o.rect=[120,50,140,80];
                            window.gestureEvents=[];render();
                        }''', kind)
                        page.locator('#game').scroll_into_view_if_needed()
                        box = page.locator('#game').bounding_box()
                        point = dict(x=box['x']+65.1*box['width']/320, y=box['y']+130.1*box['height']/200)
                        if touch:
                            cdp.send('Input.dispatchTouchEvent', dict(type='touchStart', touchPoints=[dict(**point, id=1)]))
                        else:
                            page.mouse.move(**point)
                            page.mouse.down()
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                        page.wait_for_function('!!resident.drag')
                        page.evaluate('n=>advance(n)', duration)
                        if touch:
                            cdp.send('Input.dispatchTouchEvent', dict(type='touchEnd', touchPoints=[]))
                        else:
                            page.mouse.up()
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                        actual = page.evaluate('gestureEvents')
                        expected = ['click' if duration < 30 else 'place']
                        report['checks'].append(dict(input='touch' if touch else 'mouse', kind=kind,
                                                     held_ticks=duration, expected=expected, actual=actual,
                                                     passed=actual == expected))
                    except Exception as e:
                        report['errors'].append(f'{touch}/{kind}/{duration}: {e}')
            context.close()
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Object fixtures, real production canvas mouse/touch handlers, read-only dispatch observation. Thresholds derive from original 9141 and 67F2. Native complete basket journeys separately check pixels and gameplay continuity.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']), failed=sum(not c['passed'] for c in report['checks']), errors=report['errors']), indent=2))
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output) else 1)
