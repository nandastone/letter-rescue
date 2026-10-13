"""Observe Home music in the exported Godot game through ordinary mouse input.

An AnalyserNode branches off the actual destination input. It contributes no
audio and does not change game state, playback rate, or the source schedule.
This proves audible output and controls, not waveform equality with DOS.
"""
import argparse
import functools
import hashlib
import http.server
import json
from pathlib import Path
import threading
import time

from playwright.sync_api import sync_playwright


def verify(web, output):
    output.mkdir(parents=True, exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0), functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks, errors, observations = [], [], []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width':1280,'height':800})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type=='error' else None)
            page.add_init_script('''
                window.treehouseAudioTaps=[];
                const connect=AudioNode.prototype.connect;
                AudioNode.prototype.connect=function(destination,...args){
                    const result=connect.call(this,destination,...args);
                    if(destination instanceof AudioDestinationNode){
                        const analyser=this.context.createAnalyser();analyser.fftSize=2048;
                        connect.call(this,analyser);
                        window.treehouseAudioTaps.push({analyser,context:this.context});
                    }
                    return result;
                };
            ''')
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('#status').wait_for(state='hidden', timeout=60000)
            page.keyboard.press('Space')
            started = time.monotonic()
            def observe(label):
                value = page.evaluate('''()=>window.treehouseAudioTaps.map(({analyser,context})=>{
                    const values=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(values);
                    let peak=0,power=0;for(const value of values){peak=Math.max(peak,Math.abs(value));power+=value*value;}
                    return {state:context.state,peak,rms:Math.sqrt(power/values.length),time:context.currentTime};
                })''')
                observations.append(dict(label=label, elapsed=time.monotonic()-started, taps=value))
                return max((tap['peak'] for tap in value), default=0)
            def click(x,y):
                bounds=page.locator('#canvas').bounding_box()
                page.mouse.click(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
            def peaks(label, count=15):
                values=[]
                for _ in range(count):
                    page.wait_for_timeout(100)
                    values.append(observe(label))
                return values
            click(95,145)
            page.wait_for_timeout(12000)
            page.keyboard.press('Escape')
            page.wait_for_timeout(1000)
            click(215,145)
            page.wait_for_timeout(500)
            page.screenshot(path=str(output/'hollow-before.png'))
            check('hollow is silent before sign input', max(peaks('before'))==0)
            click(180,45)
            check('sign input starts audible Home music', max(peaks('home'))>0.001)
            page.keyboard.press('Control+s')
            page.wait_for_timeout(400)
            check('sound-off mutes actual Home output', max(peaks('muted',4))==0)
            page.keyboard.press('Escape')
            page.keyboard.press('Control+s')
            page.wait_for_timeout(300)
            page.keyboard.press('Escape')
            check('sound-on restores actual Home output', max(peaks('unmuted',6))>0.001)
            click(160,100)
            page.wait_for_timeout(300)
            check('ordinary click interrupts Home output', max(peaks('interrupted',5))==0)
            click(180,45)
            check('sign can replay Home', max(peaks('replayed',8))>0.001)
            page.wait_for_timeout(6500)
            check('Home stops automatically at completion', max(peaks('finished',6))==0)
            page.screenshot(path=str(output/'hollow-after.png'))
            browser.close()
    except Exception as error:
        errors.append(str(error))
    finally:
        server.shutdown()
        server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks), checks=checks, errors=errors, observations=observations,
                web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()},
                limits=['Destination analyser proves output presence/silence, not DOS waveform or timing equivalence.',
                        'Autoplay without user input and focus transitions are not established.'])
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=checks,errors=errors),indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if verify(args.web.resolve(),args.output) else 1)
