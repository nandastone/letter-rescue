"""Observe real Godot Web audio after input, mute/unmute and a full music loop.

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
            peaks=[]
            for _ in range(30):
                page.wait_for_timeout(100)
                peaks.append(observe('activated'))
            check('ordinary key input enables audible selection music', max(peaks)>0.001)
            check('browser audio context is running', any(t['state']=='running' for t in observations[-1]['taps']))
            page.keyboard.press('Control+s')
            page.wait_for_timeout(500)
            muted=[observe('muted')]
            for _ in range(4):
                page.wait_for_timeout(100)
                muted.append(observe('muted'))
            check('sound-off mutes actual mixed output', max(muted)==0)
            page.keyboard.press('Escape')
            page.keyboard.press('Control+s')
            page.wait_for_timeout(400)
            page.keyboard.press('Escape')
            peaks=[]
            for _ in range(20):
                page.wait_for_timeout(100)
                peaks.append(observe('unmuted'))
            check('sound-on restores actual output', max(peaks)>0.001)
            # Let the unmodified exported game run beyond the full 151.782s
            # authored PCM. Do not seek or modify its time to force a repeat.
            milestone=30
            while time.monotonic()-started < 155:
                page.wait_for_timeout(1000)
                observe('full-loop-wait')
                if time.monotonic()-started >= milestone:
                    print(f'Observed {milestone}s of real selection playback', flush=True)
                    milestone+=30
            peaks=[]
            for _ in range(20):
                page.wait_for_timeout(100)
                peaks.append(observe('after-loop'))
            check('audible selection music repeats beyond full asset duration', max(peaks)>0.001)
            page.screenshot(path=str(output/'selection-after-loop.png'))
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
