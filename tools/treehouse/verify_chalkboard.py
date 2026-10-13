"""Compare reconstructed chalk strokes/cursors with ordinary native input captures."""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0;')
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        page.evaluate("treehouseDemo.setScene('inside');chalk.select(1);treehouseDemo.advance(100);")
        cases=[('chalk-position','chalk-capture','',80,69),
               ('chalk-dot','chalk-capture','chalk.begin(80,69);',80,69),
               ('chalk-stroke','chalk-capture','chalk.move(115,69,true);',82,69),
               ('erased','eraser-capture','chalk.select(6);chalk.begin(79,69);chalk.move(77,67,true);',77,67)]
        for name,folder,code,x,y in cases:
            page.evaluate(code+f'treehouseDemo.setPointer({x},{y});treehouseDemo.render();')
            image=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB')
            original=Image.open(ROOT/'testing/output/treehouse/research-writing'/folder/'state'/f'{name}.png').convert('RGB')
            # Native room animations are independent of this recovered drawing loop.
            for label,region in [('drawing',(60,45,154,92)),('tray',(63,92,149,95))]:
                a,b=image.crop(region),original.crop(region)
                delta=ImageChops.difference(a,b);count=sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
                report['pixels'][name+'-'+label]=dict(different_pixels=count,exact=count==0,region=region,bounds=delta.getbbox())
            image.save(output/f'{name}.png')
        def check(value,label):
            report['checks'].append(dict(name=label,passed=bool(value)))
            if not value:raise AssertionError(label)
        check(page.evaluate('chalk.move(168,118);chalk.tool===-1'), 'Leaving board returns tool')
        check(page.evaluate('chalk.clear();chalk.select(2);chalk.begin(60,45);chalk.bitmap.pixels.filter(x=>x!==0xff000000).length===1'), 'Brush clips to board edge')
        check(page.evaluate('chalk.end();chalk.clear();chalk.select(0);chalk.begin(80,69);chalk.move(115,69,true);chalk.previous[0]===82'), 'Native movement clamps to two pixels')
        check(page.evaluate('chalk.undo();chalk.bitmap.pixels.every(x=>x===0xff000000)'), 'Undo restores stroke backing bitmap')
        check(page.evaluate('chalk.begin(80,69);chalk.move(115,69,true,true);chalk.bitmap.pixels.filter(x=>x!==0xff000000).length===74'), 'Enlarged pad draws continuous strokes')
        check(page.evaluate("const saved=Array.from(chalk.bitmap.pixels);setScene('music');setScene('inside');saved.every((p,i)=>chalk.bitmap.pixels[i]===p)"), 'Drawing persists between activities')
        page.get_by_role('button',name='Draw on the chalkboard',exact=True).click()
        page.locator('#chalk-tool').select_option('4')
        pad=page.locator('#chalk-pad').bounding_box()
        page.mouse.move(pad['x']+30,pad['y']+30);page.mouse.down();page.mouse.move(pad['x']+120,pad['y']+60,steps=10);page.mouse.up()
        check(page.evaluate('chalk.bitmap.pixels.some(x=>x===chalk.colors[4])'), 'Pointer input draws with selected green chalk')
        page.get_by_role('button',name='Clear chalkboard',exact=True).click()
        check(page.evaluate('advance(100);answerQuestion(true);advance(100);chalk.bitmap.pixels.every(x=>x===0xff000000)'), 'Clear affects drawing bitmap')
        page.get_by_role('button',name='Undo drawing',exact=True).click()
        check(page.evaluate('chalk.bitmap.pixels.some(x=>x===chalk.colors[4])'), 'Undo restores clear')
        page.evaluate('treehouseDemo.render()');page.screenshot(path=str(output/'chalkboard-browser.png'),full_page=True)
        page.set_viewport_size(dict(width=390,height=844))
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Enlarged drawing pad fits mobile')
        page.screenshot(path=str(output/'chalkboard-mobile.png'),full_page=True)
        check(not report['errors'],'No browser exceptions')
        browser.close()
    report['passed']=all(v['passed'] for v in report['checks'])
    report['all_reference_regions_exact']=all(v['exact'] for v in report['pixels'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify(args.html,args.output)
