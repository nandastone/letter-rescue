"""Exercise print output through ordinary input in the uninstrumented Web export.

Checks all downloaded pixels against the displayed frozen preview, and score
pixels against independently reached headless previews. Repeated downloads,
print media layout and a real beforeprint event per document are checked.
Headless Edge leaves print requests pending (no afterprint event), so repeated
printer-dialog completion is outside this check. No window.print replacement,
game-state injection, screenshot-fed runtime or physical printer claim.
"""
import argparse,base64,functools,hashlib,http.server,io,json,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(web,output,fixtures,status_fixture=None):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[];errors=[]
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text())
    def check(value,name):checks.append(dict(name=name,passed=bool(value)))
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            for activity,mode in [('score',0),('score',1),('nature',0),('nature',1)]:
                context=browser.new_context(viewport={'width':1280,'height':800},device_scale_factor=1,accept_downloads=True)
                page=context.new_page()
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
                if status_fixture:
                    # This route starts from the packaged profile, through the
                    # same explicit import available to a player.
                    page.keyboard.press('F9')
                    with page.expect_file_chooser(timeout=10000) as pending:
                        page.get_by_role('button',name='Load game',exact=True).click()
                    pending.value.set_files(status_fixture)
                    page.wait_for_timeout(350)
                    page.keyboard.press('Escape');page.wait_for_timeout(150)
                canvas=page.locator('#canvas');bounds=canvas.bounding_box()
                def frame():return Image.open(io.BytesIO(canvas.screenshot())).convert('RGB').resize((320,200),Image.Resampling.NEAREST)
                def move(x,y):page.mouse.move(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
                def click(x,y):move(x,y);page.mouse.down();page.mouse.up();page.wait_for_timeout(100)
                def match(reference,region,label):
                    expected=Image.open(reference).convert('RGB').crop(region).tobytes()
                    for _ in range(160):
                        actual=frame()
                        if actual.crop(region).tobytes()==expected:break
                        page.wait_for_timeout(150)
                    actual.save(output/(label+'.png'))
                    check(actual.crop(region).tobytes()==expected,label)
                click(95,145)
                match(ROOT/'testing/output/treehouse/entry-verified-a/state/after-click.png',(284,0,320,75),activity+'-room')
                if activity=='score':
                    click(60,185)
                    match(ROOT/'testing/output/treehouse/godot-music-component-e/song-0-20.png',(88,27,300,102),'music-entry')
                    click(274,169);page.keyboard.press('z');page.keyboard.press('c')
                else:
                    click(134,109)
                    match(ROOT/'testing/output/treehouse/nature-edit-native-a/state/initial.png',(3,4,126,165),'nature-entry')
                    move(14,112);page.mouse.down();move(210,110);page.mouse.up();page.wait_for_timeout(250)
                label=f'{activity}-{mode}'
                if mode:
                    if activity=='score':click(275,149)
                    else:
                        r=assets['nature']['rectangles'][13];click((r[1]+r[3])//2,(r[0]+r[2])//2)
                if activity=='score':click(298,125);click(23,70)
                else:click(30,185);click(30,145)
                # Two disjoint pointer positions expose every source pixel.
                # The print image is frozen; both screenshots are observations.
                move(1,199);page.wait_for_timeout(100);left=frame()
                move(319,199);page.wait_for_timeout(100);right=frame()
                left.save(output/(label+'-preview-left.png'))
                right.save(output/(label+'-preview-right.png'))
                page.keyboard.press('F9')
                page.get_by_role('dialog',name='Print picture',exact=True).wait_for(timeout=10000)
                page.wait_for_function("!document.querySelector('[data-action=print-picture]').disabled")
                check(page.get_by_role('button',name='Load game',exact=True).is_hidden(),label+': file controls hidden during printing')
                page.screenshot(path=str(output/(label+'-controls.png')))
                with page.expect_download(timeout=10000) as pending:
                    page.get_by_role('button',name='Save picture',exact=True).click()
                download=pending.value;download.save_as(output/(label+'.png'))
                check(download.suggested_filename=='TREEHOUSE.PNG',label+': PNG filename')
                png=(output/(label+'.png')).read_bytes()
                image=Image.open(io.BytesIO(png)).convert('RGB')
                pixels=sum(a!=b and a!=c for a,b,c in zip(image.getdata(),left.getdata(),right.getdata()))
                checks.append(dict(name=label+': all downloaded pixels equal displayed preview',passed=image.size==(320,200) and pixels==0,different_pixels=pixels))
                if activity=='score':
                    wanted=Image.open(fixtures/(label+'.png')).convert('RGB')
                    check(image.tobytes()==wanted.tobytes(),label+': complete score equals independent renderer')
                src=page.locator('#treehouse-print-page img').get_attribute('src')
                check(base64.b64decode(src.split(',')[1])==png,label+': print uses identical PNG bytes')
                page.evaluate("window.treehousePrintEvents=0;window.addEventListener('beforeprint',()=>window.treehousePrintEvents++)")
                page.get_by_role('button',name='Print picture',exact=True).click()
                check(page.evaluate('window.treehousePrintEvents')>0,label+': browser print invoked from real button')
                page.emulate_media(media='print')
                page.screenshot(path=str(output/(label+'-print-layout.png')))
                layout=page.evaluate("""() => {
                  const img=document.querySelector('#treehouse-print-page img');
                  const r=img.getBoundingClientRect();
                  return {width:r.width,height:r.height,pixelated:getComputedStyle(img).imageRendering,
                    canvas:getComputedStyle(document.querySelector('#canvas')).display,
                    dialog:getComputedStyle(document.querySelector('#treehouse-files')).display,
                    page:getComputedStyle(document.querySelector('#treehouse-print-page')).display};
                }""")
                check(layout['canvas']=='none' and layout['dialog']=='none' and layout['page']=='block',label+': print hides game and utility UI')
                check(abs(layout['width']/layout['height']-1.6)<0.001 and layout['pixelated']=='pixelated',label+': print retains original aspect and sharp pixels')
                page.emulate_media(media='screen')
                page.keyboard.press('Escape');page.wait_for_timeout(100)
                check(page.get_by_role('dialog').is_hidden(),label+': cancel returns to preview')
                page.keyboard.press('F9')
                with page.expect_download(timeout=10000) as pending:page.get_by_role('button',name='Save picture',exact=True).click()
                pending.value.save_as(output/(label+'-repeat.png'))
                check((output/(label+'-repeat.png')).read_bytes()==png,label+': repeated output is byte-identical')
                page.keyboard.press('Escape');page.wait_for_timeout(150)
                page.keyboard.press('Escape');page.wait_for_timeout(150)
                page.keyboard.press('F9');page.wait_for_timeout(150)
                check(page.get_by_role('dialog',name='Save files',exact=True).is_visible(),label+': original preview exit restores file controls')
                page.keyboard.press('Escape')
                context.close()
            # Desktop helper is a standalone file with the same embedded image.
            page=browser.new_page()
            page.goto((fixtures/'score-0.html').as_uri())
            page.get_by_role('button',name='Print picture').wait_for()
            page.evaluate("window.printEvents=0;window.addEventListener('beforeprint',()=>window.printEvents++)")
            page.get_by_role('button',name='Print picture').click()
            check(page.evaluate('window.printEvents')>0,'desktop helper invokes browser printing')
            page.emulate_media(media='print');page.screenshot(path=str(output/'desktop-print-layout.png'))
            check(page.get_by_role('button').is_hidden(),'desktop print omits utility button')
            browser.close()
    except Exception as error:errors.append(str(error))
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,initial_status_sha256=hashlib.sha256(status_fixture.read_bytes()).hexdigest() if status_fixture else None,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True)
    p.add_argument('--status-fixture',type=Path)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output,a.fixtures.resolve(),a.status_fixture.resolve() if a.status_fixture else None) else 1)
