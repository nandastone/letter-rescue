"""Ordinary mouse/touch object drags, drawing revisits and erase confirmations."""
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
            page = context.new_page(); page.set_default_timeout(5000)
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('1992-01-01T00:00:00Z');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            cdp = context.new_cdp_session(page) if touch else None
            actions = []

            def flush():
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')

            def press(name):
                control = page.get_by_role('button', name=name, exact=True)
                control.tap() if touch else control.click(); flush(); actions.append(name)

            def wait_for(expression):
                done = page.evaluate('''expression=>{let n=0;while(!eval(expression)&&n++<30000)advance();render();return !!eval(expression);}''', expression)
                if not done:
                    raise AssertionError('Did not reach: '+expression)

            def settle():
                wait_for("!entering&&!roomTravel&&!resident.busy&&!room.busy&&!room.speech.length&&tick>=room.speechDue&&(scene!=='theater'||!theater.presentation&&!theater.playing&&!theater.tokenSequence&&!(theater.previewCategory>=0))")

            def check(name, expression, arg=None):
                passed = bool(page.evaluate(expression, arg))
                report['checks'].append(dict(name=label+': '+name, passed=passed))
                if not passed:
                    raise AssertionError(name)

            def location(point):
                page.locator('#game').scroll_into_view_if_needed()
                box = page.locator('#game').bounding_box()
                return dict(x=box['x']+(point[0]+.1)*box['width']/320, y=box['y']+(point[1]+.1)*box['height']/200)

            def down(point):
                pt = location(point)
                if touch:
                    cdp.send('Input.dispatchTouchEvent', dict(type='touchStart', touchPoints=[dict(**pt, id=1)]))
                else:
                    page.mouse.move(**pt); page.mouse.down()
                flush()

            def move(point):
                pt = location(point)
                if touch:
                    cdp.send('Input.dispatchTouchEvent', dict(type='touchMove', touchPoints=[dict(**pt, id=1)]))
                else:
                    page.mouse.move(**pt)
                flush()

            def up():
                cdp.send('Input.dispatchTouchEvent', dict(type='touchEnd', touchPoints=[])) if touch else page.mouse.up()
                flush(); page.evaluate('render()')

            def click(point):
                down(point); up(); actions.append(dict(click=point))

            def object_center(kind):
                return page.evaluate('kind=>{const o=resident.objects.find(o=>o.type===kind);if(!o)throw Error("Missing object "+kind);const r=resident.bounds(o);return [(r[1]+r[3])/2,(r[0]+r[2])/2];}', kind)

            def drag_object(kind, destination):
                origin = object_center(kind); down(origin); page.evaluate('advance(16)')
                move(destination); page.evaluate('advance(2)'); up(); settle()
                actions.append(dict(drag=kind, origin=origin, destination=destination))

            try:
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                for _ in range(3):
                    click(object_center(6)); settle()
                check('three actual balloon clicks remove it', 'balloon.hidden&&!resident.objects.some(o=>o.type===6)')
                drag_object(8, [170,145])
                check('dragged pillow is refused and returned', 'resident.pose!==4&&resident.objects.some(o=>o.type===8&&o.inside)')
                drag_object(20, [287,186])
                check('fruit dropped through trapdoor becomes outdoor food', '!resident.objects.some(o=>o.type===20)&&resident.objects.some(o=>o.type===16&&!o.inside)')
                click(object_center(9)); settle()
                check('bag click produces one nut', 'resident.objects.filter(o=>o.type===11).length===1')
                drag_object(11, [277,186])
                check('dropped nut becomes an outdoor pile', '!resident.objects.some(o=>o.type===11)&&resident.objects.some(o=>o.type===14&&!o.inside)')
                press('Go outside'); settle()
                check('yard receives both dropped objects', 'scene==="outside"&&[14,16].every(type=>resident.objects.some(o=>o.type===type&&!o.inside))')
                press('Go inside'); settle()
                click([68,95])
                check('canvas selects white chalk', 'chalk.tool===0')
                down([80,62])
                for x in range(82,101,2):
                    page.evaluate('advance(2)'); move([x,62])
                up()
                check('held canvas input produces white stroke', 'chalk.bitmap.pixels.filter(v=>v===chalk.colors[0]).length>=40')
                drawing = page.evaluate('Array.from(chalk.bitmap.pixels)')
                for activity in ['Make some music', 'Explore nature', 'Put on a play']:
                    press(activity); settle(); press('Back'); settle()
                    check('drawing survives '+activity, 'saved=>scene==="inside"&&saved.every((v,i)=>chalk.bitmap.pixels[i]===v)', drawing)
                press('Draw on the chalkboard')
                press('Clear chalkboard'); wait_for('preferences?.kind==="question"')
                press('No'); settle()
                check('declining erase preserves every pixel', 'saved=>!preferences&&saved.every((v,i)=>chalk.bitmap.pixels[i]===v)', drawing)
                press('Clear chalkboard'); wait_for('preferences?.kind==="question"')
                press('Yes'); settle()
                check('confirming erase clears drawing', 'chalk.bitmap.pixels.every(v=>v===0xff000000)')
                press('Undo drawing')
                check('undo restores erased drawing', 'saved=>saved.every((v,i)=>chalk.bitmap.pixels[i]===v)', drawing)
                press('Go outside'); settle(); page.reload()
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Go outside'); settle()
                check('dropped yard objects survive a full reload', '[14,16].every(type=>resident.objects.some(o=>o.type===type&&!o.inside))')
            except Exception as e:
                report['errors'].append(label+': '+str(e))
            report['sessions'].append(dict(name=label, actions=actions))
            context.close()
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Visible controls and real mouse/touch pointer input only; production time accelerated. Reads choose object positions and compare retained drawings. No gameplay state installed. Browser integration, not paired native timing/audio parity.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.html, args.output) else 1)
