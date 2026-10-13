"""Exercise F1/F2, saved switches and notebook help in an unmodified Web export.

Uses real Edge mouse/keyboard input and original DOS modal pixels. Native cursor
boxes are excluded from browser region comparisons; separate headless native
comparisons include those cursors. No runtime instrumentation or state injection.
"""
import argparse,functools,hashlib,http.server,io,json,struct,threading
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
from build_demo import ROOT

def verify(web,output):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[];errors=[];base=ROOT/'testing/output/treehouse'
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text())
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            canvas=page.locator('#canvas')
            def ready():page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            ready();bounds=canvas.bounding_box()
            def frame():return Image.open(io.BytesIO(canvas.screenshot())).convert('RGB').resize((320,200),Image.Resampling.NEAREST)
            def move(x,y):page.mouse.move(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
            def click(x,y):move(x,y);page.mouse.down();page.mouse.up()
            def check(value,name):checks.append(dict(name=name,passed=bool(value)))
            def matches(name,source,rect):
                reference=Image.open(str(source)+'.png').convert('RGB')
                ram=Path(str(source)+'.ram-0').read_bytes()
                y,x=struct.unpack_from('<hh',ram,0x34454)
                def crop(im):
                    im=im.copy();ImageDraw.Draw(im).rectangle((x,y,x+17,y+17),fill='black');return im.crop(rect).tobytes()
                expected=crop(reference)
                move(5,5)
                for _ in range(100):
                    actual=frame()
                    if crop(actual)==expected:break
                    page.wait_for_timeout(100)
                actual.save(output/(name+'.png'))
                check(crop(actual)==expected,name)
            def help_match(name,label,rect):matches(name,base/'research-help/native/state'/(label+'-help'),rect)
            def wait_cursor(name):
                data=bytes(assets['cursor']);hx,hy=struct.unpack_from('<hh',data);pixels=[]
                for y in range(16):
                    mask=struct.unpack_from('<H',data,4+y*2)[0];ink=struct.unpack_from('<H',data,36+y*2)[0]
                    for x in range(16):
                        if not mask&(0x8000>>x):pixels.append((300-hx+x,180-hy+y,(255,255,85) if ink&(0x8000>>x) else (0,0,0)))
                move(300,180)
                for _ in range(150):
                    im=frame();visible=all(im.getpixel((x,y))==rgb for x,y,rgb in pixels)
                    if visible:break
                    page.wait_for_timeout(200)
                check(visible,name)
            move(160,100);page.keyboard.press('F1')
            help_match('welcome-help','outdoor',(32,66,288,134))
            page.keyboard.press('Escape')
            help_match('outside-escape-keeps-help','outdoor',(32,66,288,134))
            click(160,100);page.wait_for_timeout(450)
            page.keyboard.press('F2')
            matches('preferences-default',base/'research-settings/native/state/preferences',(32,43,288,152))
            for row in range(5):
                click(160,64+14*row);page.wait_for_timeout(250)
                matches('toggle-'+str(row),base/'research-settings/native/state'/('row-'+str(row)),(32,43,288,152))
            click(260,141);page.wait_for_timeout(1500)
            page.reload();ready();bounds=canvas.bounding_box();move(160,100)
            page.keyboard.press('F2')
            matches('preferences-after-reload',base/'research-settings/native/state/row-4',(32,43,288,152))
            page.keyboard.press('Control+v')
            matches('version-over-preferences',base/'research-help/native/state/version',(108,176,212,192))
            page.keyboard.press('Space')
            matches('status-restores-preferences',base/'research-settings/native/state/row-4',(32,43,288,152))
            page.keyboard.press('Escape')
            page.keyboard.press('Control+s');page.keyboard.press('Space')
            page.keyboard.press('Control+s')
            matches('sound-off-status',base/'research-help/native/state/sound-off',(108,176,212,192))
            page.keyboard.press('Space')
            click(95,145);page.wait_for_timeout(1000);wait_cursor('room entrance releases input')
            page.keyboard.press('F1')
            help_match('room-context','room',(32,66,288,134))
            click(160,100);page.wait_for_timeout(450)
            click(65,139);page.wait_for_timeout(1500);wait_cursor('theater options release input')
            # The original entry shows a pointer during its final 60-tick pause.
            # F1 is intentionally blocked until that transfer has returned.
            page.wait_for_timeout(1200)
            page.keyboard.press('F1')
            matches('theater-options-help',base/'research-help/extra/state/theater-both-help',(32,31,288,169))
            click(160,100);page.wait_for_timeout(450)
            # Original PLAY control, followed by a notebook help tab.
            click(210,140);page.wait_for_timeout(1500)
            r=assets['theater']['ui_rects'][12]
            click((r[1]+r[3])//2,(r[0]+r[2])//2)
            help_match('theater-notebook-help','theater',(32,51,288,149))
            browser.close()
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output) else 1)
