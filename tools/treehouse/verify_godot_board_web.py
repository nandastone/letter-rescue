"""Play both board modes in the actual uninstrumented Godot Web export.

Real mouse input, original options/score regions, rendered dice and car sprites,
legal road movement, settings persistence after reload and room return. This is
bounded browser coverage; full endings have separate native/control replays.
Fresh profiles start with a friend opponent. Select the robot through the UI
before comparing the robot reference or locating the first player's blue car.
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
    checks=[];errors=[];assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'));tables=assets['boardgame']
    def ref(path):return Image.open(ROOT/'testing/output/treehouse'/path).convert('RGB')
    room=ref('entry-verified-a/state/after-click.png')
    money_options=ref('research-boardgame/entry-a/state/boardgame.png')
    chip_options=ref('research-boardgame/chip-a/state/chip-options.png')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/');canvas=page.locator('#canvas')
            def ready():page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            ready();bounds=canvas.bounding_box()
            def frame():return Image.open(io.BytesIO(canvas.screenshot())).convert('RGB').resize((320,200),Image.Resampling.NEAREST)
            def move(x,y):page.mouse.move(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
            def click(x,y):move(x,y);page.mouse.down();page.mouse.up()
            def rect_click(r):click((r[1]+r[3])//2,(r[0]+r[2])//2)
            def check(value,name):checks.append(dict(name=name,passed=bool(value)))
            def matches(name,reference,region):
                expected=reference.crop(region).tobytes()
                for _ in range(120):
                    actual=frame()
                    if actual.crop(region).tobytes()==expected:break
                    page.wait_for_timeout(200)
                actual.save(output/(name+'.png'));check(actual.crop(region).tobytes()==expected,name);return actual
            def wait_cursor(name,x=300,y=180):
                data=bytes(assets['cursor']);hx,hy=struct.unpack_from('<hh',data);pixels=[]
                for row in range(16):
                    mask=struct.unpack_from('<H',data,4+row*2)[0];ink=struct.unpack_from('<H',data,36+row*2)[0]
                    for col in range(16):
                        if not mask&(0x8000>>col):pixels.append((x-hx+col,y-hy+row,(255,255,85) if ink&(0x8000>>col) else (0,0,0)))
                move(x,y);page.wait_for_timeout(100)
                for _ in range(150):
                    actual=frame();visible=all(actual.getpixel((px,py))==rgb for px,py,rgb in pixels)
                    if visible:break
                    page.wait_for_timeout(200)
                check(visible,name)
            def shape_pixels(id,palette,mirror=False):
                w,h,data=assets['shapes'][f'modules:{id}'];pixels=base64.b64decode(data);colors=assets['palettes'][f'modules:{palette}']['colors']
                return w,h,[(w-1-j%w if mirror else j%w,j//w,tuple(colors[index])) for j,index in enumerate(pixels) if index]
            def sprite_matches(im,id,palette,rect,mirror=False):
                w,h,pixels=shape_pixels(id,palette,mirror);x=(rect[1]+rect[3])//2-w//2;y=(rect[0]+rect[2])//2-h//2
                return all(im.getpixel((x+dx,y+dy))==rgb for dx,dy,rgb in pixels)
            def car_node(im):
                for i,r in enumerate(tables['node_rects'][:24]):
                    if any(sprite_matches(im,4442+(1 if d==1 else 2 if d==3 else 0),4400,r,d==0) for d in range(4)):return i
                return None
            click(95,145);matches('room-entry',room,(284,0,320,75));wait_cursor('entrance releases input')
            click(180,189);move(310,180)
            matches('board-options-open',money_options,(110,15,285,47))
            rect_click(tables['options_rects'][4]);move(310,180)
            matches('money-options',money_options,(30,50,290,180))
            for mode in [0,1]:
                if mode:
                    click(180,189);move(310,180);matches('board-reentry',money_options,(30,50,290,180))
                    rect_click(tables['options_rects'][2]);move(310,180)
                    matches('chip-options',chip_options,(150,78,285,112))
                    page.wait_for_timeout(1500);page.reload();ready();bounds=canvas.bounding_box()
                    click(95,145);matches('reload-room',room,(284,0,320,75));wait_cursor('reload entrance releases input')
                    click(180,189);move(310,180);matches('chip-mode-restored',chip_options,(150,78,285,112))
                rect_click(tables['options_rects'][17]);move(310,180);page.wait_for_timeout(5000)
                start=frame();start.save(output/f'{mode}-started.png')
                check(sprite_matches(start,4425,4400,tables['game_rects'][2]),f'{mode}: ready roll control uses original icon')
                rect_click(tables['game_rects'][2]);move(310,180);page.wait_for_timeout(4000)
                rolled=frame();rolled.save(output/f'{mode}-rolled.png')
                check(any(sprite_matches(rolled,4007+i,4000,tables['game_rects'][2]) for i in range(1,6)),f'{mode}: dice displays recovered number')
                node=car_node(rolled);check(node is not None,f'{mode}: original car is on a road node')
                if node is not None:
                    target=next(n for n in tables['adjacency'][node] if n>=0)
                    rect_click(tables['node_rects'][target]);move(310,180);page.wait_for_timeout(3500)
                    moved=frame();moved.save(output/f'{mode}-moved.png');check(car_node(moved)==target,f'{mode}: legal road click moves car to destination')
                click(311,10);move(160,120);matches(f'{mode}-return-room',room,(284,0,320,75));wait_cursor(f'{mode}: room return releases input',160,120)
            browser.close()
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output) else 1)
