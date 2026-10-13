"""Compare original nature screens and exercise the reconstructed animal activity."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960))
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.add_init_script('requestAnimationFrame=()=>0;')
        page.goto(html.resolve().as_uri())
        page.evaluate("treehouseDemo.setScene('nature')")
        cases=[('nature','demo-nature',''),('night','nature-explore','nature.toggleTime();'),
               ('food','nature-explore','nature.selectAttribute(6);'),('plants','nature-explore','nature.selectAttribute(6);'),
               ('mammals','nature-explore','nature.selectClass(0);')]
        for name,folder,code in cases:
            ref=ROOT/'testing/output/treehouse'/folder
            run=json.loads((ref/'run.json').read_text())
            y,x=struct.unpack_from('<HH',(ref/'state'/f'{name}.ram-0').read_bytes(),run['main_image_base']+0x321d0+0x2064)
            page.evaluate(code+f'treehouseDemo.setPointer({x},{y});treehouseDemo.render();')
            image=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB')
            original=Image.open(ref/'state'/f'{name}.png').convert('RGB');delta=ImageChops.difference(image,original)
            count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
            report['pixels'][name]=dict(different_pixels=count,exact=count==0,bounds=delta.getbbox())
            image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        def check(value,label):
            report['checks'].append(dict(name=label,passed=bool(value)))
            if not value:raise AssertionError(label)
        for animal in range(92):
            check(page.evaluate('''id=>{const a=nature.tables.animals[id];nature.time=a.active_time;nature.attribute=0;nature.values[0]=a.attributes[0];nature.selectClass(a.category);nature.selectAnimal(id);nature.objects[nature.time]=[];const o=nature.addAnimal(id);treehouseDemo.render();treehouseDemo.advance(1000);treehouseDemo.render();return !!o&&nature.fact().length>0&&nature.animals().some(a=>a.id===id);}''',animal),f'Animal {animal}: filter, facts, placement and ambient frames')
        check(page.evaluate('''()=>{nature.objects=[[],[]];nature.time=0;for(let i=0;i<45;i++)nature.addAnimal(14);return nature.objects[0].length===40;}'''), 'Forty animals per scene')
        check(page.evaluate('nature.toggleTime();nature.objects[1].length===0&&nature.objects[0].length===40'), 'Day and night preserve separate collages')
        check(page.evaluate('nature.toggleTime();nature.clear();nature.objects[0].length===0'), 'Clear scene')
        check(page.evaluate('nature.undoClear();nature.objects[0].length===40'), 'Undo clear')
        page.evaluate('nature.objects=[[],[]];nature.addAnimal(14,210,110);')
        check(page.evaluate('''()=>{const o=nature.objects[0][0];nature.beginDrag(o.x+1,o.y+1);nature.moveDrag(20,130);nature.endDrag();return nature.objects[0].length===0;}'''), 'Dragging an animal outside removes it')
        page.evaluate("nature.selectAttribute(0,false);nature.selectValue(0);nature.selectClass(3);")
        page.locator('#nature-animal').select_option('36')
        page.get_by_role('button',name='Add this animal',exact=True).click()
        check(page.evaluate('nature.objects[0].length===1&&nature.selected===36'), 'Readable animal controls place an ant')
        page.screenshot(path=str(output/'nature-browser.png'),full_page=True)
        page.set_viewport_size(dict(width=390,height=844))
        page.screenshot(path=str(output/'nature-mobile.png'),full_page=True)
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Mobile layout fits')
        page.get_by_role('button',name='Back',exact=True).click()
        check(page.evaluate("scene==='inside'"), 'Back returns to treehouse')
        check(not report['errors'],'No browser exceptions')
        browser.close()
    report['passed']=all(v['passed'] for v in report['checks'])
    report['all_reference_frames_exact']=all(v['exact'] for v in report['pixels'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(checks=len(report['checks']),passed=report['passed'],pixels=report['pixels'],errors=report['errors']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,default=ROOT/'testing/output/treehouse/continuation-build/index.html')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify(args.html,args.output)
