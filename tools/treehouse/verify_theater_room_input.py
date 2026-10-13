"""Replay original theater room hotspot clicks through fresh mouse/touch sessions."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright
from verify_telescope_centering import DATA


def verify(html,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['passed'] and len(native['cases'])==8
    assert native['content_sha256']=='a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c'
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
                reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for touch in [False,True]:
            for case in native['cases']:
                label=('touch-' if touch else 'mouse-')+case['name']
                context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch)
                page=context.new_page();page.set_default_timeout(5000)
                page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
                try:
                    page.goto(html.resolve().as_uri())
                    def settle():
                        assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<10000)advance();render();return n<10000;}'''), 'Animation did not finish'
                    button=page.get_by_role('button',name='Choose the girl' if touch else 'Choose the boy',exact=True)
                    button.tap() if touch else button.click();settle()
                    assert page.evaluate("scene==='inside'")
                    canvas=page.locator('#game');canvas.scroll_into_view_if_needed();box=canvas.bounding_box();x,y=case['point']
                    px=box['x']+(x+.1)*box['width']/320;py=box['y']+(y+.1)*box['height']/200
                    page.touchscreen.tap(px,py) if touch else page.mouse.click(px,py);settle()
                    actual=page.evaluate("scene==='inside'?5:scene==='theater'?(theater.options?13:2):scene")
                    expected=case['after']['scene']
                    report['checks'].append(dict(name=label,point=case['point'],expected=expected,actual=actual,passed=actual==expected))
                    print(label,actual,actual==expected,flush=True)
                except Exception as e:report['errors'].append(label+': '+str(e))
                context.close()
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==16 and all(c['passed'] for c in report['checks'])
    report['scope']='Sixteen fresh mouse/touch browser sessions replay eight native theater entrance edge clicks. Compare staying in the room versus opening theater options. No game-state or seed injection; animation clock accelerated. Does not prove whole-scene pixels, sound or timing parity.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['html','output']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'theater-room-input-native-b')
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output,a.reference) else 1)
