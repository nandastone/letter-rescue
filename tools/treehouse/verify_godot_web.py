"""Run the exported Godot game in Edge, click a character and inspect its canvas."""
import argparse
import base64
import functools
import hashlib
import http.server
import io
import json
import threading
import time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(output: Path, web: Path, editor=False, maze=False, status_fixture=None, hollow_only=False, hollow_stall_ms=0):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    worker = threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    errors = []
    checks = []
    browser_observations = {}
    functional_waits = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge',headless=True)
            page = browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
            if hollow_only:
                # Passive host/input observations. No engine state or input is changed.
                page.add_init_script('''(() => {
                  const p = window.__hollowProbe = {events:[], slowFrames:[], frames:0};
                  let last = 0;
                  const frame = t => {if(last && t-last>50)p.slowFrames.push({at:t,gap:t-last});last=t;p.frames++;requestAnimationFrame(frame);};
                  requestAnimationFrame(frame);
                  for(const type of ['mousedown','mouseup','keydown','keyup','blur','focus'])
                    window.addEventListener(type,e=>p.events.push({type,at:performance.now(),x:e.clientX,y:e.clientY,key:e.key,focused:document.hasFocus()}),true);
                })();''')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            if status_fixture:
                # This legacy route expects the original packaged profile.
                # Import it through the same file control available to players.
                page.keyboard.press('F9')
                with page.expect_file_chooser(timeout=10000) as pending:
                    page.get_by_role('button',name='Load game',exact=True).click()
                pending.value.set_files(status_fixture)
                page.wait_for_timeout(350)
                page.keyboard.press('Escape');page.wait_for_timeout(150)
            canvas = page.locator('#canvas')
            bounds = canvas.bounding_box()
            def frame():
                return Image.open(io.BytesIO(canvas.screenshot())).convert('RGB').resize((320,200),Image.Resampling.NEAREST)
            def wait_region(name, reference, region, timeout=5.0):
                # Functional readiness, not a claim about native elapsed time.
                # A loaded host can pause Godot while a fixed wall-clock sleep
                # expires. Poll the completed image before the next action.
                started = time.monotonic()
                samples = 0
                while True:
                    actual = frame()
                    samples += 1
                    matched = actual.crop(region).tobytes()==reference.crop(region).tobytes()
                    elapsed = time.monotonic()-started
                    if matched or elapsed>=timeout:
                        functional_waits.append(dict(name=name,seconds=elapsed,samples=samples,matched=matched,timeout_seconds=timeout))
                        return actual
                    page.wait_for_timeout(50)
            outside = frame()
            outside.save(output/'outside-web.png')
            page.mouse.click(bounds['x']+95*bounds['width']/320,bounds['y']+145*bounds['height']/200)
            expected = Image.open(ROOT/'testing/output/treehouse/entry-verified-a/state/after-click.png').convert('RGB')
            # Exact static upper-right room region; date, pointer and wall clock
            # remain live. This checks the shipped Web renderer, not audio timing.
            region = (284,0,320,75)
            for attempt in range(80):
                candidate = frame()
                if candidate.crop(region).tobytes()==expected.crop(region).tobytes():
                    break
                page.wait_for_timeout(250)
            candidate.save(output/'inside-web.png')
            checks.append(dict(name='mouse-selected entrance reaches original room backdrop',
                               region=list(region),passed=candidate.crop(region).tobytes()==expected.crop(region).tobytes()))
            checks.append(dict(name='selection differs from room',passed=outside.tobytes()!=candidate.tobytes()))
            def click(x,y):
                page.mouse.click(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
            click(200,30)
            page.wait_for_timeout(400)
            opened = frame()
            opened.save(output/'calendar-web.png')
            checks.append(dict(name='calendar opens from actual mouse input',passed=opened.getpixel((163,45))==(255,255,255)))
            click(200,45)
            page.wait_for_timeout(400)
            closed = frame()
            checks.append(dict(name='calendar closes from actual mouse input',passed=closed.getpixel((163,45))==candidate.getpixel((163,45))))
            click(66,94)
            page.wait_for_timeout(1000)
            page.mouse.move(bounds['x']+70*bounds['width']/320,bounds['y']+60*bounds['height']/200)
            page.mouse.down()
            page.mouse.move(bounds['x']+78*bounds['width']/320,bounds['y']+60*bounds['height']/200,steps=4)
            page.mouse.up()
            page.mouse.move(bounds['x']+160*bounds['width']/320,bounds['y']+120*bounds['height']/200)
            drawing = frame()
            drawing.save(output/'chalk-web.png')
            checks.append(dict(name='held mouse draws white chalk on the board',passed=drawing.getpixel((70,60))==(255,255,255)))
            # Use the same recovered pixels as desktop rendering, checking only
            # opaque object pixels against an actual browser drag and release.
            assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))
            def object_matches(image,kind,left,top):
                table=assets['room']['objects'][kind]
                palette=assets['palettes'][f"th:{table['palette']}"]
                ident=palette['first']+table['states'][1]-1
                width,height,data=assets['shapes'][f'th:{ident}']
                pixels=base64.b64decode(data)
                return all(image.getpixel((left+x,top+y))==tuple(palette['colors'][pixels[y*width+x]]) for y in range(height) for x in range(width) if pixels[y*width+x])
            page.mouse.move(bounds['x']+112*bounds['width']/320,bounds['y']+139*bounds['height']/200)
            page.mouse.down()
            page.wait_for_timeout(400)
            page.mouse.move(bounds['x']+85*bounds['width']/320,bounds['y']+190*bounds['height']/200)
            page.mouse.up()
            page.mouse.move(bounds['x']+160*bounds['width']/320,bounds['y']+120*bounds['height']/200)
            page.wait_for_timeout(600)
            placed=frame()
            placed.save(output/'pillow-drag-web.png')
            checks.append(dict(name='held mouse drags pillow and original fall places it on floor',passed=object_matches(placed,8,79,186)))
            click(295,168)
            page.wait_for_timeout(800)
            bag=frame()
            bag.save(output/'nut-bag-web.png')
            checks.append(dict(name='clicking bag produces original nut at floor position',passed=object_matches(bag,11,232,178)))
            page.keyboard.press('Escape')
            page.wait_for_timeout(150)
            returned = frame()
            yard_reference = Image.open(ROOT/'testing/output/treehouse/yard-native-journey-b/state/initial.png').convert('RGB')
            checks.append(dict(name='Escape returns to the yard without selection previews',region=[80,105,128,184],
                               passed=returned.crop((80,105,128,184)).tobytes()==yard_reference.crop((80,105,128,184)).tobytes()))
            click(220,145)
            page.wait_for_timeout(200)
            hollow = frame()
            hollow.save(output/'hollow-web.png')
            hollow_reference = Image.open(ROOT/'testing/output/treehouse/yard-native-journey-b/state/hollow.png').convert('RGB')
            checks.append(dict(name='yard opens original squirrel hollow',region=[100,80,240,130],
                               passed=hollow.crop((100,80,240,130)).tobytes()==hollow_reference.crop((100,80,240,130)).tobytes()))
            click(234,145)
            if hollow_stall_ms:
                # Explicit host-stall fixture, never native timing evidence.
                page.evaluate('ms => setTimeout(() => {const end=performance.now()+ms; while(performance.now()<end){}},250)',hollow_stall_ms)
            nut_reference = Image.open(ROOT/'testing/output/treehouse/yard-native-journey-b/state/nut-1.png').convert('RGB')
            nut = wait_region('nut flight completes',nut_reference,(212,91,232,110))
            nut.save(output/'nut-web.png')
            checks.append(dict(name='squirrel nut throw reaches original landing picture',region=[212,91,232,110],
                               passed=nut.crop((212,91,232,110)).tobytes()==nut_reference.crop((212,91,232,110)).tobytes()))
            click(308,7)
            wait_region('hollow exit reaches yard',yard_reference,(80,105,128,184))
            click(260,120)
            back = wait_region('ladder reaches room',expected,region)
            checks.append(dict(name='hollow exit and yard ladder return to the room',region=list(region),
                               passed=back.crop(region).tobytes()==expected.crop(region).tobytes()))
            if hollow_only:
                back.save(output/'hollow-return-web.png')
                browser_observations = page.evaluate('window.__hollowProbe')
            if not hollow_only:
                click(60,185)
                music_reference=Image.open(ROOT/'testing/output/treehouse/godot-music-component-e/song-0-20.png').convert('RGB')
                score=(88,27,300,102)
                for attempt in range(100):
                    piano=frame()
                    if piano.crop(score).tobytes()==music_reference.crop(score).tobytes():break
                    page.wait_for_timeout(150)
                piano.save(output/'music-web.png')
                checks.append(dict(name='piano hotspot and teleport reach original music score',region=list(score),passed=piano.crop(score).tobytes()==music_reference.crop(score).tobytes()))
                page.keyboard.down('z')
                pressed=frame()
                key_reference=Image.open(ROOT/'testing/output/treehouse/godot-music-component-e/key-0-0.png').convert('RGB')
                key_region=(86,183,99,188)
                checks.append(dict(name='physical keyboard depresses original piano key',region=list(key_region),passed=pressed.crop(key_region).tobytes()==key_reference.crop(key_region).tobytes() and pressed.crop(key_region).tobytes()!=piano.crop(key_region).tobytes()))
                page.keyboard.up('z')
                released=frame()
                checks.append(dict(name='physical keyboard release restores piano key',region=list(key_region),passed=released.crop(key_region).tobytes()==piano.crop(key_region).tobytes()))
                click(17,125)
                families=frame()
                family_reference=Image.open(ROOT/'testing/output/treehouse/godot-music-component-e/families.png').convert('RGB')
                family_region=(80,26,300,130)
                checks.append(dict(name='instrument button opens original family menu',region=list(family_region),passed=families.crop(family_region).tobytes()==family_reference.crop(family_region).tobytes()))
                click(285,7)
                if editor:
                    native=ROOT/'testing/output/treehouse/music-native-journey-d/state'
                    def native_region(name,filename,region):
                        actual=frame();actual.save(output/(name+'.png'))
                        wanted=Image.open(native/(filename+'.png')).convert('RGB')
                        checks.append(dict(name=name,region=list(region),passed=actual.crop(region).tobytes()==wanted.crop(region).tobytes()))
                    click(274,169)
                    page.keyboard.press('z')
                    page.keyboard.press('c')
                    page.mouse.move(bounds['x']+295*bounds['width']/320,bounds['y']+101*bounds['height']/200)
                    native_region('composing records physical C and E keys','short-ce',(88,27,300,102))
                    click(181,19)
                    page.keyboard.type('tune')
                    page.keyboard.press('Enter')
                    page.mouse.move(bounds['x']+295*bounds['width']/320,bounds['y']+101*bounds['height']/200)
                    native_region('title field accepts physical typing','short-named',(113,14,258,25))
                    click(275,149)
                    native_region('long book opens independently','long-blank',(88,27,300,102))
                    click(275,149)
                    native_region('short notes survive score-size changes','short-ce',(88,27,300,102))
                    click(298,125)
                    click(23,70)
                    printed=frame();printed.save(output/'editor-print-web.png')
                    checks.append(dict(name='print confirmation opens score sheet',passed=printed.getpixel((60,80))==(255,255,255) and printed.getpixel((60,81))==(0,0,0)))
                    page.keyboard.press('Escape')
                    # Godot syncs user:// to IndexedDB asynchronously in Web exports.
                    page.wait_for_timeout(6500)
                    page.reload()
                    page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
                    click(95,145)
                    for attempt in range(100):
                        if frame().crop(region).tobytes()==expected.crop(region).tobytes():break
                        page.wait_for_timeout(150)
                    click(60,185)
                    for attempt in range(100):
                        if frame().crop(score).tobytes()==music_reference.crop(score).tobytes():break
                        page.wait_for_timeout(150)
                    click(274,169)
                    page.mouse.move(bounds['x']+295*bounds['width']/320,bounds['y']+101*bounds['height']/200)
                    native_region('browser reload restores saved notes','short-ce',(88,27,300,102))
                    native_region('browser reload restores saved title','short-named',(113,14,258,25))
                if maze:
                    click(30,155)
                    intro=Image.open(ROOT/'testing/output/treehouse/godot-maze-entry-skip-a/intro-03.png').convert('RGB')
                    intro_region=(30,37,242,112)
                    for attempt in range(100):
                        candidate=frame()
                        if candidate.crop(intro_region).tobytes()==intro.crop(intro_region).tobytes():break
                        page.wait_for_timeout(150)
                    candidate.save(output/'maze-intro-web.png')
                    checks.append(dict(name='maze button and bucket transfer reach original tutorial',region=list(intro_region),passed=candidate.crop(intro_region).tobytes()==intro.crop(intro_region).tobytes()))
                    click(210,180)
                    machine=Image.open(ROOT/'testing/output/treehouse/godot-maze-native-a/settled.png').convert('RGB')
                    machine_region=(55,107,187,154)
                    for attempt in range(100):
                        candidate=frame()
                        if candidate.crop(machine_region).tobytes()==machine.crop(machine_region).tobytes():break
                        page.wait_for_timeout(150)
                    page.wait_for_timeout(7000)
                    candidate=frame();candidate.save(output/'maze-play-web.png')
                    checks.append(dict(name='tutorial skip reaches original note machine',region=list(machine_region),passed=candidate.crop(machine_region).tobytes()==machine.crop(machine_region).tobytes()))
                    # Match the background against source sprites to locate signs;
                    # no game state is injected or exposed by the exported runtime.
                    backgrounds=[]
                    palette=assets['palettes']['modules:2340']['colors']
                    for node in range(9):
                        w,h,data=assets['shapes'][f'modules:{2341+node}']
                        pixels=base64.b64decode(data)
                        background=Image.new('RGB',(w,h));background.putdata([tuple(palette[p]) for p in pixels])
                        score_=sum(a==b for a,b in zip(candidate.getdata(),background.getdata()))
                        backgrounds.append((score_,node))
                    similarity,node=max(backgrounds)
                    checks.append(dict(name='maze draws one of the nine recovered scene backgrounds',matching_background_pixels=similarity,node=node,passed=similarity>40000))
                    y,x=assets['music']['maze']['sign_positions'][node][0]
                    click(x+14,y+13)
                    page.wait_for_timeout(13000)
                    answered=frame();answered.save(output/'maze-answer-web.png')
                    checks.append(dict(name='sign click changes challenge or collected score',passed=answered.crop((0,25,320,154)).tobytes()!=candidate.crop((0,25,320,154)).tobytes()))
                    click(291,10)
                    # Composition is retained when returning from the maze.
                    return_reference=Image.open(ROOT/'testing/output/treehouse/music-native-journey-d/state/short-ce.png').convert('RGB') if editor else music_reference
                    for attempt in range(100):
                        candidate=frame()
                        if candidate.crop(score).tobytes()==return_reference.crop(score).tobytes():break
                        page.wait_for_timeout(150)
                    candidate.save(output/'maze-return-web.png')
                    checks.append(dict(name='maze back arrow and reverse bucket return to retained score',region=list(score),passed=candidate.crop(score).tobytes()==return_reference.crop(score).tobytes()))
                    portrait_region=(0,0,79,99)
                    portrait=Image.open(ROOT/'testing/output/treehouse/music-native-journey-d/state/short-ce.png').convert('RGB') if editor else music_reference
                    for attempt in range(100):
                        candidate=frame()
                        if candidate.crop(portrait_region).tobytes()==portrait.crop(portrait_region).tobytes():break
                        page.wait_for_timeout(150)
                    checks.append(dict(name='reverse bucket finishes and restores instrument portrait',region=list(portrait_region),passed=candidate.crop(portrait_region).tobytes()==portrait.crop(portrait_region).tobytes()))
                    page.wait_for_timeout(150)
                page.keyboard.press('Escape')
                page.mouse.move(bounds['x']+160*bounds['width']/320,bounds['y']+120*bounds['height']/200)
                for attempt in range(100):
                    back=frame()
                    if back.crop(region).tobytes()==expected.crop(region).tobytes():
                        # The room backing is visible throughout the return effect.
                        page.wait_for_timeout(7000)
                        back=frame()
                        break
                    page.wait_for_timeout(150)
                back.save(output/'music-return-web.png')
                checks.append(dict(name='music exit returns to original room backdrop',region=list(region),passed=back.crop(region).tobytes()==expected.crop(region).tobytes()))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    report = dict(checks=checks,errors=errors,browser_observations=browser_observations,host_stall_fixture_ms=hollow_stall_ms,functional_waits=functional_waits,initial_status_sha256=hashlib.sha256(status_fixture.read_bytes()).hexdigest() if status_fixture else None,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in web.iterdir() if p.is_file()},
                  scope=('Exported Godot Web boot, entrance, calendar, chalk, pillow drag/fall, nut bag, yard/hollow and room return. Passive browser event/frame observations only. ' if hollow_only else 'Exported Godot Web boot, entrance, calendar, chalk, pillow drag/fall, nut bag, yard/hollow, music transition, physical piano keys, family menu and room return. ')+('Also composing, title typing, independent books, print preview and actual browser reload persistence. ' if editor else '')+('Also maze entry, skipped tutorial, background rendering, a sign interaction and retained-score return. This browser check does not prove victory. ' if maze else '')+'Explicit region/pixel assertions only; full screenshots retained. Audio activation runs normally but waveform parity is not asserted.',
                  passed=not errors and all(c['passed'] for c in checks) and all(w['matched'] for w in functional_waits))
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--web',type=Path,default=ROOT/'treehouse-godot/build/web')
    parser.add_argument('--editor',action='store_true')
    parser.add_argument('--maze',action='store_true')
    parser.add_argument('--status-fixture',type=Path)
    parser.add_argument('--hollow-only',action='store_true',help='Stop after the original squirrel throw/room-return route and retain passive host/input observations.')
    parser.add_argument('--hollow-stall-ms',type=int,default=0,help='Explicit main-thread stall fixture during nut flight; diagnosis only, never native timing evidence.')
    args=parser.parse_args()
    if args.hollow_only and (args.editor or args.maze):parser.error('--hollow-only cannot be combined with --editor or --maze')
    if args.hollow_stall_ms and not args.hollow_only:parser.error('--hollow-stall-ms requires --hollow-only')
    raise SystemExit(0 if verify(args.output,args.web.resolve(),args.editor,args.maze,args.status_fixture.resolve() if args.status_fixture else None,args.hollow_only,args.hollow_stall_ms) else 1)
