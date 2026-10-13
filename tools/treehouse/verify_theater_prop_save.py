"""Drag a decoration on a scaled canvas and retain exact geometry after reload."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        def settle():
            assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}''')
        def press(name):
            page.get_by_role('button',name=name,exact=True).click();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');settle()
        def move(x,y):
            box=page.locator('#game').bounding_box();page.mouse.move(box['x']+x*box['width']/320,box['y']+y*box['height']/200)
        try:
            press('Choose the boy');press('Put on a play');page.locator('#props').check();press('Start the theater')
            page.locator('#theater-part-0').select_option('0');page.locator('#theater-part-1').select_option('0');page.locator('#theater-part-2').select_option('1')
            press('Choose decorations');move(86.25,28.25);page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            page.evaluate('advance(30)');move(220.25,135.25);page.mouse.up();page.evaluate('render()')
            report['before']=page.evaluate('theater.savedState()')
            report['checks'].append(dict(name='drag places a decoration on the stage',passed=len(report['before']['props'][1])==1))
            report['checks'].append(dict(name='decoration uses integer original-pixel coordinates',passed=page.evaluate('theater.props[1].every(p=>Number.isInteger(p.x)&&Number.isInteger(p.y))')))
            press('Back');page.reload();press('Choose the boy');press('Put on a play')
            report['after']=page.evaluate('theater.savedState()')
            report['checks'].append(dict(name='sentence and decoration geometry survive full reload unchanged',passed=report['after']==report['before']))
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==3 and all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
