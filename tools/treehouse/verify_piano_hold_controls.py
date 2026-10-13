"""Fresh mouse, keyboard and touch journeys for long notes and idle interruption."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for mode in ['mouse','keyboard','touch']:
            touch=mode=='touch'
            context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch)
            page=context.new_page();page.set_default_timeout(5000);page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
            cdp=context.new_cdp_session(page) if touch else None
            def flush():page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            def check(name,expression):report['checks'].append(dict(name=mode+': '+name,passed=bool(page.evaluate(expression))))
            def press(name):
                b=page.get_by_role('button',name=name,exact=True);b.tap() if touch else b.click();flush()
                assert page.evaluate('()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}')
            def down():
                canvas=page.locator('#game');canvas.scroll_into_view_if_needed();canvas.focus()
                if mode=='keyboard':page.keyboard.down('n')
                else:
                    box=canvas.bounding_box();point=dict(x=box['x']+185.1*box['width']/320,y=box['y']+183.1*box['height']/200)
                    if touch:cdp.send('Input.dispatchTouchEvent',dict(type='touchStart',touchPoints=[dict(**point,id=1)]))
                    else:page.mouse.move(**point);page.mouse.down()
                flush()
            def up():
                if mode=='keyboard':page.keyboard.up('n')
                elif touch:cdp.send('Input.dispatchTouchEvent',dict(type='touchEnd',touchPoints=[]))
                else:page.mouse.up()
                flush()
            try:
                press('Choose the girl' if touch else 'Choose the boy');press('Make some music')
                seed=page.evaluate('gameplayRandom.seed');down()
                check('press starts one A note','held.size===1&&[...held.values()][0].pitch===9')
                page.evaluate('advance(1800);render()')
                check('long hold defers idle and its random draw',f'held.size===1&&musicIdle.frame===-1&&gameplayRandom.seed==={seed}')
                up();page.evaluate('advance(200);render()')
                check('release clears held state and expired notation','held.size===0&&musicAuditionPitch===null&&musicIdle.frame===-1')
                assert page.evaluate('()=>{let n=0;while(musicIdle.frame<0&&n++<4000)advance();render();return musicIdle.frame>=0;}')
                seed=page.evaluate('gameplayRandom.seed');expected=(seed*214013+2531011)&0xffffffff
                down()
                check('new input interrupts idle and schedules it once',f'musicIdle.frame===-1&&held.size===1&&gameplayRandom.seed==={expected}')
                page.evaluate('advance(300);render()')
                check('interrupted animation stays stopped while key is held',f'held.size===1&&musicIdle.frame===-1&&gameplayRandom.seed==={expected}')
                up();page.evaluate('advance(2);render()')
                check('second release stops the key','held.size===0')
            except Exception as e:report['errors'].append(mode+': '+str(e))
            context.close()
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==18 and all(c['passed'] for c in report['checks'])
    report['scope']='Three fresh sessions through visible navigation and production mouse, keyboard and real Chromium touch events. Animation time is advanced; game state is only read. Checks held notes, release, idle interruption and random-call count. Native pixel/audio timing is covered separately.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
