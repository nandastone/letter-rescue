"""Exercise the shipped Godot logo, automatic exit and ordinary browser input."""
import argparse
import functools
import hashlib
import http.server
import io
import json
from pathlib import Path
import threading
import time

from PIL import Image
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(web, output, frames, headed=False):
    output.mkdir(parents=True, exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(web)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks, errors = [], []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    reference = json.loads((frames / 'godot.json').read_text())
    hashes = {hashlib.sha256(Image.open(frames / f['image']).convert('RGB').tobytes()).hexdigest(): f for f in reference['frames']}
    final_logo = Image.open(frames / reference['frames'][-1]['image']).convert('RGB').tobytes()
    outside = Image.open(ROOT / 'testing/output/treehouse/entry-verified-a/state/title.png').convert('RGB')
    region = (280, 0, 320, 200)
    observed, audio, focus = [], [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge', headless=not headed,
                                                args=['--autoplay-policy=document-user-activation-required'])
            context = browser.new_context(viewport={'width':1280, 'height':800}, has_touch=True)
            page = context.new_page()
            # Playwright enables focus emulation on every page by default.
            # Disable that harness override so tab activation emits real blur.
            page.add_init_script('''
                window.titleAudioTaps=[];
                window.titleFocusEvents=[];
                for(const event of ['focus','blur']) window.addEventListener(event,()=>titleFocusEvents.push(event));
                const connect=AudioNode.prototype.connect;
                AudioNode.prototype.connect=function(destination,...args){
                    const result=connect.call(this,destination,...args);
                    if(destination instanceof AudioDestinationNode){
                        const analyser=this.context.createAnalyser();analyser.fftSize=2048;
                        connect.call(this,analyser);
                        titleAudioTaps.push({analyser,context:this.context});
                    }
                    return result;
                };
            ''')
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            def boot():
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                context.new_cdp_session(page).send('Emulation.setFocusEmulationEnabled',{'enabled':False})
                page.locator('#status').wait_for(state='hidden', timeout=60000)
            def frame():
                return Image.open(io.BytesIO(page.locator('#canvas').screenshot())).convert('RGB').resize((320,200), Image.Resampling.NEAREST)
            def is_outside(value):
                return value.crop(region).tobytes() == outside.crop(region).tobytes()
            def hear(label):
                values=page.evaluate('''()=>titleAudioTaps.map(({analyser,context})=>{
                    const values=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(values);
                    return {state:context.state,peak:Math.max(...values.map(Math.abs)),time:context.currentTime};
                })''')
                audio.append(dict(label=label,taps=values))
                return max((v['peak'] for v in values),default=0)
            def switch_tabs(label):
                other=page.context.new_page()
                other.goto('about:blank')
                context.new_cdp_session(other).send('Emulation.setFocusEmulationEnabled',{'enabled':False})
                # Apply after navigation: Chromium may replace the renderer.
                context.new_cdp_session(page).send('Emulation.setFocusEmulationEnabled',{'enabled':False})
                other.bring_to_front()
                page.wait_for_timeout(250)
                away=page.evaluate('document.hasFocus()')
                page.bring_to_front();page.wait_for_timeout(250)
                returned=page.evaluate('document.hasFocus()')
                focus.append(dict(label=label,away=away,returned=returned,events=page.evaluate('titleFocusEvents')))
                check(label+' really loses and regains browser focus',not away and returned)
                other.close()
            boot()
            hear('fresh autoplay')
            check('fresh browser exposes an audio context',bool(audio[-1]['taps']))
            started = time.monotonic()
            revealed = False
            while time.monotonic() - started < 12:
                value = frame()
                hear('title autoplay')
                raw = value.tobytes()
                sha = hashlib.sha256(raw).hexdigest()
                if sha in hashes and (not observed or observed[-1]['sha256'] != sha):
                    observed.append(dict(sha256=sha, source_frame=hashes[sha]['image'], seconds=time.monotonic()-started))
                revealed |= raw == final_logo
                if is_outside(value):
                    break
                page.wait_for_timeout(80)
            check('browser renders original title frames', len(observed) >= 10)
            check('browser completes the original presents reveal', revealed)
            check('browser automatically reaches selection', is_outside(value))
            autoplay=[tap for observation in audio for tap in observation['taps']]
            check('autoplay produces sound when running or remains suspended',
                  any(t['peak']>0.001 for t in autoplay) or all(t['state']=='suspended' for t in autoplay))
            value.save(output / 'selection.png')
            for kind in ('keyboard', 'mouse', 'touch', 'focus-return'):
                boot()
                initial = frame()
                check(kind + ' route begins at logo', hashlib.sha256(initial.tobytes()).hexdigest() in hashes)
                if kind == 'focus-return':
                    switch_tabs('title')
                    page.keyboard.press('Space')
                elif kind == 'keyboard':
                    page.keyboard.press('Space')
                elif kind == 'mouse':
                    page.mouse.click(640, 400)
                else:
                    page.touchscreen.tap(640, 400)
                page.wait_for_timeout(200)
                check(kind + ' skips to selection', is_outside(frame()))
                peaks=[]
                for _ in range(8):
                    page.wait_for_timeout(100);peaks.append(hear(kind))
                check(kind+' activates audible selection music',max(peaks)>0.001)
            # Normal selection input after the skip must still enter the game.
            page.mouse.click(95 * 4, 145 * 4)
            room = Image.open(ROOT / 'testing/output/treehouse/entry-verified-a/state/after-click.png').convert('RGB')
            room_region = (284, 0, 320, 75)
            for _ in range(100):
                value = frame()
                if value.crop(room_region).tobytes() == room.crop(room_region).tobytes():
                    break
                page.wait_for_timeout(150)
            check('selection after title reaches playable room', value.crop(room_region).tobytes() == room.crop(room_region).tobytes())
            value.save(output / 'room.png')
            # The original room keyboard opens music. Hold a real piano key,
            # change tabs, then verify focus loss released the actual voice.
            page.mouse.click(60*4,185*4)
            piano_reference=Image.open(ROOT/'testing/output/treehouse/godot-music-component-e/song-0-20.png').convert('RGB')
            piano_region=(84,182,244,197)
            for _ in range(80):
                value=frame()
                if value.crop(piano_region).tobytes()==piano_reference.crop(piano_region).tobytes():break
                page.wait_for_timeout(150)
            check('focus route reaches original piano keyboard',value.crop(piano_region).tobytes()==piano_reference.crop(piano_region).tobytes())
            page.keyboard.down('z');page.wait_for_timeout(250)
            check('held physical piano key has audible output',hear('piano-held')>0.001)
            switch_tabs('held piano key')
            page.wait_for_timeout(250)
            check('focus loss releases held piano output',hear('piano-after-focus')==0)
            page.keyboard.up('z');page.keyboard.down('x');page.wait_for_timeout(150)
            check('piano plays again after focus return',hear('piano-replayed')>0.001)
            page.keyboard.up('x');page.wait_for_timeout(250)
            check('released replayed key is silent',hear('piano-released')==0)
            page.screenshot(path=str(output/'piano-after-focus.png'))
            browser.close()
    except Exception as error:
        errors.append(str(error))
    finally:
        server.shutdown()
        server.server_close()
    report = dict(passed=not errors and all(c['passed'] for c in checks), checks=checks, errors=errors,
                  headed=headed, observed=observed, audio_observations=audio, focus_observations=focus,
                  headless_reference_sha256=hashlib.sha256((frames / 'godot.json').read_bytes()).hexdigest(),
                  web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()},
                  limits=['Destination analyser proves audibility/silence and gesture activation, not DOS waveform equivalence.',
                          'Autoplay policy is requested at launch; actual context states and output are recorded. A suspended-context path is covered only if observed.',
                          'Focus checks require observed real blur/focus. OS minimization/mobile background suspension are not covered.',
                          'Sparse wall-clock screenshots do not prove native presentation timing.'])
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(checks), frames=len(observed), failures=[c for c in checks if not c['passed']], errors=errors), indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('web', 'output', 'frames'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--headed',action='store_true',help='Use real Edge tabs; headless Windows may report every tab focused.')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.web.resolve(), args.output, args.frames,args.headed) else 1)
