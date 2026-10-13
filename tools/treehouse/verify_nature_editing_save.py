"""Create, move, remove, erase and reload day/night collages through controls."""
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
            assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy||nature?.eraseTask)&&n++<30000)advance();render();return n<30000;}''')
        def press(name):
            page.get_by_role('button',name=name,exact=True).click();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');settle()
        def check(name,expression):
            ok=bool(page.evaluate(expression));report['checks'].append(dict(name=name,passed=ok));assert ok,name
        def saved():return page.evaluate('()=>({time:nature.time,attribute:nature.attribute,values:nature.values,category:nature.category,objects:nature.objects.map(list=>list.map(({id,x,y})=>({id,x,y})))})')
        def drag(a,b):
            box=page.locator('#game').bounding_box()
            def move(x,y):page.mouse.move(box['x']+(x+.25)*box['width']/320,box['y']+(y+.25)*box['height']/200)
            move(*a);page.mouse.down();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');page.evaluate('advance(30)');move(*b);page.mouse.up();page.evaluate('render()')
        try:
            press('Choose the boy');press('Explore nature')
            for time in [0,1]:
                if time:press('Switch to nighttime')
                category=page.locator('#nature-class option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                page.locator('#nature-class').select_option(category)
                animal=page.locator('#nature-animal option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                page.locator('#nature-animal').select_option(animal)
                check(f'scene {time}: animal fact is visible','nature.factOpen&&nature.fact().length>0')
                press('Add this animal')
                start=page.evaluate('()=>{const o=nature.objects[nature.time][0];return [o.x+2,o.y+2];}')
                drag(start,[start[0]+13,start[1]+8])
                check(f'scene {time}: moving an existing animal dismisses its fact','!nature.factOpen&&nature.objects[nature.time].length===1')
                press('Clear this scene');press('No')
                check(f'scene {time}: declining erase retains the animal','nature.objects[nature.time].length===1')
            before=saved();report['before_reload']=before
            press('Back');page.reload();press('Choose the boy');press('Explore nature')
            after=saved();report['after_reload']=after
            report['checks'].append(dict(name='both collage geometries and filters survive reload',passed=before==after));assert before==after
            press('Clear day and night scenes');press('No')
            check('declining both-scenes erase preserves both','nature.objects.every(list=>list.length===1)')
            start=page.evaluate('()=>{const o=nature.objects[nature.time][0];return [o.x+2,o.y+2];}')
            drag(start,[20,125]);check('dragging outside removes only the active-scene animal','nature.objects[1].length===0&&nature.objects[0].length===1')
            press('Switch to daytime');press('Clear this scene');press('Yes')
            check('confirmed animated erase completes','!nature.eraseTask&&nature.objects.every(list=>list.length===0)')
            press('Back');page.reload();press('Choose the boy');press('Explore nature')
            check('erased collages remain empty after reload','nature.objects.every(list=>list.length===0)')
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==11 and all(c['passed'] for c in report['checks'])
    report['scope']='Fresh ordinary-control creation, scaled-canvas dragging, both-scene save/reload, erase decline/accept and removal. No gameplay state installed; animations accelerated. Native comparison is a separate suite.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
