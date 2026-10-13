"""Require the original removal sound after an ordinary existing-animal drag."""
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
        def press(name):
            page.get_by_role('button',name=name,exact=True).click();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}''')
        try:
            press('Choose the boy');press('Explore nature')
            category=page.locator('#nature-class option').evaluate_all('o=>o.find(v=>v.value!=="-1").value');page.locator('#nature-class').select_option(category)
            animal=page.locator('#nature-animal option').evaluate_all('o=>o.find(v=>v.value!=="-1").value');page.locator('#nature-animal').select_option(animal);press('Add this animal')
            # Observe the real sound callback, preserving its output path.
            page.evaluate('''()=>{window.removalSounds=[];const speak=nature.speak;nature.speak=(...args)=>{removalSounds.push(args[0]);return speak(...args);};}''')
            x,y=page.evaluate('()=>{const o=nature.objects[nature.time][0];return [o.x+2,o.y+2];}')
            box=page.locator('#game').bounding_box()
            def move(x,y):page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200)
            move(x,y);page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');page.evaluate('advance(30)');move(20,125);page.mouse.up();page.evaluate('render()')
            report['sounds']=page.evaluate('removalSounds')
            report['checks'].append(dict(name='outside drop removes the animal',passed=page.evaluate('nature.objects[nature.time].length===0')))
            report['checks'].append(dict(name='outside drop plays original sound 10034 exactly once',passed=report['sounds']==[10034]))
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==2 and all(c['passed'] for c in report['checks'])
    report['scope']='Normal controls and mouse drag; verifies semantic sound dispatch through the real output callback. Native overlay 2 08FE-0902 calls sound 10034. Waveform and exact audio timing remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
