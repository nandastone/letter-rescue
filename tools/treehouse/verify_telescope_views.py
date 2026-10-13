"""Compare all four complete telescope views to ordinary-input original captures."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from verify_telescope_centering import DATA


def verify(html, output, reference):
    output.mkdir(parents=True, exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['passed'] and native['content_sha256']=='a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c'
    checkpoints=[c for c in native['checkpoints'] if c['view'] is not None]
    assert sorted(c['view'] for c in checkpoints)==list(range(4))
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), reference=str(reference),
                reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(), checks=[], pixels={}, errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        try:
            page.goto(html.resolve().as_uri())
            def settle():
                assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy||telescopeBusy())&&n++<10000)advance();render();return n<10000;}'''), 'Animation did not finish'
            page.get_by_role('button',name='Choose the boy',exact=True).click();settle()
            page.get_by_role('button',name='Look through the telescope',exact=True).click();settle()
            names=['The planets','A little alien','The birdbath','The robot’s shelf']
            for cp in checkpoints:
                view=cp['view'];name=cp['name'];page.get_by_role('button',name=names[view],exact=True).click();settle()
                x,y=cp['after']['pointer'];box=page.locator('#game').bounding_box()
                page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200);page.evaluate('render()')
                image=Image.open(BytesIO(base64.b64decode(page.evaluate("canvas.toDataURL().split(',')[1]")))).convert('RGB')
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');delta=ImageChops.difference(image,original)
                image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox())
                report['checks'].append(dict(name=names[view]+' completes',passed=page.evaluate("v=>scene==='telescope'&&telescope===v&&!roomTravel&&!telescopeBusy()",view)))
                print(name,count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['pixels'])==4 and all(v['exact'] for v in report['pixels'].values()) and all(c['passed'] for c in report['checks'])
    report['scope']='Fresh browser entrance and four visible view buttons compared over every final RGB pixel to original room-click captures. Empty robot shelf. Browser view order follows the reference; original random selection, intervening room transitions, animation/audio timing and populated shelf are outside this focused comparison. No browser gameplay state or seed injection; animation time is accelerated.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['html','output']:parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--reference',type=Path,default=DATA/'telescope-views-native-b')
    args=parser.parse_args();raise SystemExit(0 if verify(args.html,args.output,args.reference) else 1)
