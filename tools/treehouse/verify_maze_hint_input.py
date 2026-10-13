"""Fresh desktop/touch maze entry and a sign press during automatic replay.

Only the clock is advanced; state is read to select a correct sign. This checks
the real input route. Native behavior is separately proved by the paired maze
journey, including its interrupted automatic audition at correct-5.
"""
from pathlib import Path
import argparse, hashlib, json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            label = 'touch' if touch else 'desktop'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch)
            page = context.new_page(); page.set_default_timeout(5000)
            page.add_init_script("requestAnimationFrame=()=>0;{const D=Date,fixed=D.parse('2026-09-28T10:00:00+10:00');Date=class extends D{constructor(...a){super(...(a.length?a:[fixed]));}static now(){return fixed;}};}")
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            def press(name):
                button=page.get_by_role('button',name=name,exact=True)
                button.tap() if touch else button.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                if name=='Play the musical maze':
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")
            def settle():
                assert page.evaluate("()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='maze'&&maze.busy;while(busy()&&n++<30000)advance();render();return !busy();}")
            def check(name, expression):
                ok=bool(page.evaluate(expression))
                report['checks'].append(dict(name=label+': '+name,passed=ok))
            try:
                press('Choose the girl' if touch else 'Choose the boy');settle()
                press('Make some music');settle();press('Play the musical maze');press('Skip introduction');settle()
                check('fresh ordinary entry reaches playable challenge',"scene==='maze'&&maze.phase==='play'&&!maze.busy&&maze.earned===0")
                # Let the actual idle timer start its automatic target replay.
                check('idle timer starts an audible target',"()=>{let n=0;while(!maze.busy&&n++<2000)advance();return maze.busy&&!!maze.currentEvent;}")
                canvas=page.locator('#game');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
                x,y=page.evaluate('()=>{const[y,x]=maze.t.sign_positions[maze.node][maze.correct];return [x+14,y+18];}')
                px=box['x']+x*box['width']/320;py=box['y']+y*box['height']/200
                page.touchscreen.tap(px,py) if touch else page.mouse.click(px,py)
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                check('same press starts correct sign feedback','maze.feedback===maze.correct')
                settle();check('one press earns exactly one note','maze.earned===1&&!maze.busy&&maze.phase==="play"')
            except Exception as e:
                report['errors'].append(label+': '+str(e))
            context.close()
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==8 and all(c['passed'] for c in report['checks'])
    report['scope']=__doc__
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if verify(args.html,args.output) else 1)
