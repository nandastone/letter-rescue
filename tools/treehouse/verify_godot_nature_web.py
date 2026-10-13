"""Play nature in the actual uninstrumented Godot Web export in Edge.

Real mouse input checks room entry, collage drag/day/night/save/reload, quiz
options, dealing, a question/answer and return. Pixel regions and decoded icons
are asserted. Full victory is covered separately by production/native replays;
this check does not establish exact timing or output audio waveform equality.
Reference setup is reproduced through ordinary inputs: choose the insect class,
then select the robot for the quiz reference. A fresh
profile starts with no class selected, a friend opponent and help disabled.
"""
import argparse,base64,functools,hashlib,http.server,io,json,struct,threading
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
    checks=[];errors=[];assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
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
            def rect_click(r):click((r[1]+r[3])//2,(r[0]+r[2])//2)
            def check(value,name):checks.append(dict(name=name,passed=bool(value)))
            def wait_cursor(name,x,y):
                # The original hides its pointer while synchronous room actions
                # own input. A static corner alone does not establish readiness.
                data=bytes(assets['cursor']);hx,hy=struct.unpack_from('<hh',data)
                pixels=[]
                for row in range(16):
                    mask=struct.unpack_from('<H',data,4+row*2)[0]
                    ink=struct.unpack_from('<H',data,36+row*2)[0]
                    for col in range(16):
                        if not mask&(0x8000>>col):pixels.append((x-hx+col,y-hy+row,(255,255,85) if ink&(0x8000>>col) else (0,0,0)))
                move(x,y);page.wait_for_timeout(100)
                for _ in range(150):
                    actual=frame()
                    visible=all(actual.getpixel((px,py))==rgb for px,py,rgb in pixels)
                    if visible:break
                    page.wait_for_timeout(200)
                check(visible,name)
            def matches(name,reference,region):
                expected=reference.crop(region).tobytes()
                for _ in range(100):
                    actual=frame()
                    if actual.crop(region).tobytes()==expected:break
                    page.wait_for_timeout(200)
                actual.save(output/(name+'.png'));check(actual.crop(region).tobytes()==expected,name);return actual
            room=Image.open(ROOT/'testing/output/treehouse/entry-verified-a/state/after-click.png').convert('RGB')
            nature=Image.open(ROOT/'testing/output/treehouse/nature-edit-native-a/state/initial.png').convert('RGB')
            night=Image.open(ROOT/'testing/output/treehouse/nature-edit-native-a/state/night.png').convert('RGB')
            options=Image.open(ROOT/'testing/output/treehouse/nature-native-journey-c/state/setup-options.png').convert('RGB')
            ready_ref=Image.open(ROOT/'testing/output/treehouse/nature-native-journey-c/state/initial.png').convert('RGB')
            click(95,145);matches('room-entry',room,(284,0,320,75))
            click(134,109)
            matches('nature-controls-visible',nature,(3,4,126,44))
            wait_cursor('nature entry releases input',300,180)
            rect_click(assets['nature']['rectangles'][17]);move(310,199)
            matches('nature-entry',nature,(3,4,126,165))
            before=frame();move(14,112);page.mouse.down();move(210,110);page.mouse.up();move(310,199)
            page.wait_for_timeout(250);placed=frame();placed.save(output/'placed-animal.png')
            check(placed.crop((180,80,240,140)).tobytes()!=before.crop((180,80,240,140)).tobytes(),'thumbnail drag adds an animal to scene')
            check(placed.crop((3,48,127,91)).tobytes()!=before.crop((3,48,127,91)).tobytes(),'dragged animal displays original facts')
            rect_click(assets['nature']['rectangles'][13]);move(310,199);matches('night-scene',night,(180,80,300,150))
            rect_click(assets['nature']['rectangles'][13]);move(310,199);matches('day-restored',placed,(180,80,240,140))
            page.wait_for_timeout(1500);page.reload();ready();bounds=canvas.bounding_box()
            click(95,145);matches('reload-room',room,(284,0,320,75))
            click(134,109);move(310,199);matches('collage-restored-after-reload',placed,(180,80,240,140))
            click(100,185)
            rect_click(assets['nature']['quiz_options'][4]);move(310,199)
            matches('quiz-options',options,(6,3,165,120))
            # The original ready capture retains the cursor at the Start button.
            # Reproduce that pointer position so the complete panel can match.
            click(45,97);ready_image=matches('quiz-ready',ready_ref,(6,3,165,194))
            click(149,20);move(310,199);page.wait_for_timeout(4000)
            dealt=frame();dealt.save(output/'questions-dealt.png')
            check(dealt.crop((9,144,169,191)).tobytes()!=ready_image.crop((9,144,169,191)).tobytes(),'roll displays candidate hand')
            present=[];palette=assets['palettes']['modules:5650']['colors']
            for i,(y,x) in enumerate(assets['nature']['question_positions']):
                w,h,data=assets['shapes'][f'modules:{5651+i}'];pixels=base64.b64decode(data)
                visible=[(j%w,j//w,tuple(palette[index])) for j,index in enumerate(pixels) if index]
                if all(dealt.getpixel((x+dx,y+dy))==rgb for dx,dy,rgb in visible):present.append(i)
            check(len(present)==3,'exactly three recovered question icons are dealt')
            if present:
                rect_click(assets['nature']['quiz_rectangles'][12+present[0]]);move(310,199);page.wait_for_timeout(16000)
                answered=frame();answered.save(output/'question-answer.png')
                check(answered.crop((30,124,164,136)).tobytes()!=ready_image.crop((30,124,164,136)).tobytes(),'question produces visible answer footer')
            else:check(False,'question produces visible answer footer')
            click(293,8);move(310,199);matches('quiz-back-to-collage',placed,(180,80,240,140))
            click(311,10);move(160,120);matches('return-room',room,(284,0,320,75))
            wait_cursor('room return releases input',160,120)
            click(199,122);move(195,131)
            wait_cursor('telescope animation releases input',195,131)
            # All original view captures place their cursor below this region.
            region=(77,34,243,125)
            refs=[Image.open(ROOT/f'testing/output/treehouse/telescope-views-native-b/state/view-{i}.png').convert('RGB') for i in range(4)]
            selected=None
            for _ in range(150):
                through=frame()
                selected=next((i for i,r in enumerate(refs) if through.crop(region).tobytes()==r.crop(region).tobytes()),None)
                if selected is not None:break
                page.wait_for_timeout(200)
            through.save(output/'telescope.png');check(selected is not None,'room telescope displays an original view')
            if selected is not None:
                # Let any remaining sound/display finish before replay input.
                page.wait_for_timeout(2000)
                click(160,100);move(195,131)
                wait_cursor('telescope replay releases input',195,131)
                matches('telescope-replay',refs[selected],region)
                page.wait_for_timeout(2000)
                click(311,10);move(160,120)
                matches('telescope-return',room,(284,0,320,75))
            browser.close()
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output) else 1)
