"""Fresh mouse/touch theater previews, curtain lifecycle and cancellation."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for touch in [False,True]:
            label='touch' if touch else 'mouse'
            context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch)
            page=context.new_page();page.set_default_timeout(5000);page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            def check(name,value):report['checks'].append(dict(name=label+': '+name,passed=bool(value)))
            def press(name):
                b=page.get_by_role('button',name=name,exact=True);b.tap() if touch else b.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            def settle():
                assert page.evaluate("()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='theater'&&(theater.presentation||theater.previewCategory>=0||theater.preview&&!theater.preview.done||theater.playing);while(busy()&&n++<30000)advance();render();return !busy();}")
            def choose(category,index):page.locator(f'#theater-part-{category}').select_option(str(index))
            def pointer_image(x,y):
                canvas=page.locator('#game');canvas.scroll_into_view_if_needed();b=canvas.bounding_box()
                page.mouse.move(b['x']+(x+.1)*b['width']/320,b['y']+(y+.1)*b['height']/200)
                return page.evaluate("()=>{render();return canvas.toDataURL();}")
            try:
                page.goto(html.resolve().as_uri());press('Choose the girl' if touch else 'Choose the boy');settle();press('Put on a play');settle()
                page.locator('#mix-up').check();press('Start the theater')
                check('options remain during the click sound',page.evaluate('theater.stageOptions===true&&theater.openingEditor'))
                page.evaluate('advance(4)')
                check('closing curtains retain options and busy cursor',page.evaluate('theater.curtainMoving&&theater.busyCursor&&theater.stageOptions===true'))
                page.evaluate('advance(24)')
                check('opening curtains replace options behind the curtain',page.evaluate('theater.curtainMoving&&theater.stageOptions===false&&theater.openingEditor'))
                settle();check('editor restores normal cursor',page.evaluate('!theater.curtainMoving&&!theater.busyCursor&&!theater.hideCursor&&!theater.openingEditor'))
                choose(0,0);settle()
                for action in range(8):
                    choose(1,action)
                    assert page.evaluate('()=>{let n=0;while(!theater.preview&&!theater.presentation&&n++<500)advance();while(theater.presentation&&n++<1000)advance();render();return !!theater.preview&&!theater.preview.done;}')
                    check(f'action {action}: running preview hides cursor',page.evaluate('theater.hideCursor'))
                    if not touch:check(f'action {action}: pointer movement leaves full RGB unchanged',pointer_image(110,85)==pointer_image(240,150))
                    settle();check(f'action {action}: preview restores cursor',page.evaluate('!theater.hideCursor&&!theater.busyCursor'))
                if not touch:check('normal pointer is visible after preview',pointer_image(110,85)!=pointer_image(240,150))
                choose(1,0);page.evaluate('advance(120)');press('Options')
                check('options cancels preview and restores cursor',page.evaluate('theater.options&&!theater.preview&&!theater.hideCursor&&!theater.curtainMoving'))
                press('Start the theater');page.evaluate('advance(4)');press('Options')
                check('cancel during curtain resets presentation flags',page.evaluate('theater.options&&!theater.presentation&&!theater.openingEditor&&!theater.curtainMoving&&theater.stageOptions==null'))
                press('Start the theater');settle();choose(2,1)
                page.evaluate('()=>{let n=0;while(theater.presentation&&!theater.curtainMoving&&n++<1000)advance();render();}')
                check('place change starts with busy curtain cursor',page.evaluate('theater.curtainMoving&&theater.busyCursor'))
                press('Back');settle();check('leaving during curtain returns to room',page.evaluate("scene==='inside'&&!roomTravel"))
            except Exception as e:report['errors'].append(label+': '+str(e))
            context.close()
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==57 and all(c['passed'] for c in report['checks'])
    report['scope']=__doc__+' Actual controls and pointer movement, reading state only and advancing time. Includes eight previews per session and full RGB pointer-visibility comparisons on desktop; exact native timing remains separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c['name'] for c in report['checks'] if not c['passed']],errors=report['errors']),indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
