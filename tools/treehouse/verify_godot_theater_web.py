"""Play the uninstrumented Godot Web export in Edge using real mouse input.

Checks theater entry, sentence choices, visible performance, browser reload
persistence and room return. Native regions are exact; sound waveform and
presentation timestamps are not asserted by this browser check.
"""
import argparse,functools,hashlib,http.server,io,json,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(web,output):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[];errors=[]
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
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
            def matches(name,reference,region,seconds=20):
                expected=reference.crop(region).tobytes();actual=None
                for _ in range(int(seconds*5)):
                    actual=frame()
                    if actual.crop(region).tobytes()==expected:break
                    page.wait_for_timeout(200)
                actual.save(output/(name+'.png'))
                passed=actual.crop(region).tobytes()==expected
                checks.append(dict(name=name,region=region,passed=passed))
                return actual
            room=Image.open(ROOT/'testing/output/treehouse/entry-verified-a/state/after-click.png').convert('RGB')
            options=Image.open(ROOT/'testing/output/treehouse/demo-theater/state/theater.png').convert('RGB')
            editor=Image.open(ROOT/'testing/output/treehouse/theater-edit/state/editor.png').convert('RGB')
            night=Image.open(ROOT/'testing/output/treehouse/theater-night/state/night.png').convert('RGB')
            click(95,145);matches('room-entry',room,(284,0,320,75))
            click(62,134);move(160,195);matches('theater-options',options,(100,75,250,155))
            # The native editor snapshot's pointer is at (200,149); keep this
            # empty-stage assertion away from both original and live cursors.
            click(210,140);move(160,195);matches('editor-open',editor,(100,75,190,140))
            for category,index in enumerate([0,0,1,1]):
                click(35,40+32*category)
                if category==0:x=73+int(assets['shapes']['modules:3981'][0]/2)
                else:
                    count=[8,8,6,4][category];width=221//count;x=73+width*index+width//2
                click(x,28);move(310,190);page.wait_for_timeout(4000)
            final=matches('sentence-and-stage',night,(100,75,259,195))
            click(80,172);move(310,190)
            differences=0
            for _ in range(60):
                candidate=frame()
                differences+=candidate.crop((103,74,259,165)).tobytes()!=final.crop((103,74,259,165)).tobytes()
                page.wait_for_timeout(150)
            checks.append(dict(name='performance animates original stage',observed_changed_frames=differences,passed=differences>3))
            matches('performance-finished',night,(100,75,259,195))
            page.wait_for_timeout(1200)
            page.reload();ready();bounds=canvas.bounding_box()
            click(95,145);matches('reload-room',room,(284,0,320,75))
            click(62,134);move(310,190);matches('reload-options',options,(112,77,240,150))
            click(210,140);move(310,190);matches('saved-play-restored',night,(100,75,259,195))
            click(311,10);move(160,120);matches('return-room',room,(284,0,320,75))
            browser.close()
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output) else 1)
