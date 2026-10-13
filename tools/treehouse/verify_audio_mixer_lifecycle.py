"""Check real worklet output and key replacement from file and HTTP origins."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(html.resolve().parent)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            for origin,url in [('file',html.resolve().as_uri()),('http',f'http://127.0.0.1:{server.server_port}/{html.name}')]:
                page=browser.new_page();page.set_default_timeout(10000);page.add_init_script('requestAnimationFrame=()=>0')
                page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(url)
                def check(name,expression):
                    result=bool(page.evaluate(expression));report['checks'].append(dict(name=origin+': '+name,passed=result));print(origin,name,result,flush=True)
                try:
                    page.evaluate('''()=>{setScene('music');instrument=11;canvas.focus();
                      audio.context=new AudioContext({sampleRate:48000});const w=audio.context.audioWorklet,load=w.addModule.bind(w);
                      w.addModule=url=>new Promise((resolve,reject)=>{window.finishAudioModule=()=>load(url).then(resolve,reject);});}''')
                    page.keyboard.down('n');page.wait_for_function('held.size===1&&typeof finishAudioModule==="function"',polling=20)
                    check('module initialization does not delay note input','held.size===1&&audio.active.size===1&&!audio.renderer')
                    page.keyboard.up('n');check('release cancels note before module is ready','held.size===0&&audio.active.size===0')
                    page.evaluate('finishAudioModule()');page.wait_for_function('!!audio.renderer',polling=20)
                    page.evaluate('''()=>{window.audioProbe=audio.context.createAnalyser();audioProbe.fftSize=256;audio.outputGain.connect(audioProbe);
                      window.audioPeak=()=>{const a=new Float32Array(256);audioProbe.getFloatTimeDomainData(a);return Math.max(...a.map(Math.abs));};}''')
                    page.evaluate('audio.flushCommands()');check('cancelled initial note is not revived','held.size===0&&audio.active.size===0&&audioPeak()===0')
                    page.keyboard.down('n');page.wait_for_function('audio.active.size===1&&!!audio.renderer',polling=20)
                    page.wait_for_function('audioPeak()>.01',polling=20)
                    check('first key initializes worklet and produces audio','audio.context.sampleRate===48000&&held.size===1&&audio.active.size===1&&audioPeak()>.01')
                    page.keyboard.down('m');page.wait_for_function('held.size===1&&[...held.values()][0].pitch===11',polling=20)
                    page.keyboard.up('n');page.wait_for_function('audioPeak()>.01',polling=20)
                    check('old key release leaves replacement sounding','held.size===1&&audio.active.size===1&&[...held.values()][0].pitch===11&&audioPeak()>.01')
                    page.keyboard.up('m');page.wait_for_function('held.size===0&&audio.active.size===0&&audioPeak()===0',polling=20)
                    check('replacement key release decays to silence','audioPeak()===0')
                    page.keyboard.down('n');page.wait_for_function('audio.active.size===1&&audioPeak()>.01',polling=20)
                    page.locator('#sound').uncheck();page.wait_for_function('audio.active.size===0&&audioPeak()===0',polling=20)
                    check('sound toggle stops actual output','!audio.enabled&&audioPeak()===0')
                    page.keyboard.up('n');page.locator('#sound').check();page.locator('#game').focus()
                    page.keyboard.down('n');page.wait_for_function('audio.active.size===1&&audioPeak()>.01',polling=20)
                    page.evaluate("window.dispatchEvent(new Event('blur'))");page.wait_for_function('audio.active.size===0&&audioPeak()===0',polling=20)
                    check('focus loss clears held note and actual output','held.size===0&&audioPeak()===0')
                    page.keyboard.up('n');check('no processor errors','audio.errors.length===0')
                except Exception as e:report['errors'].append(origin+': '+str(e))
                page.close()
            browser.close()
    finally:server.shutdown();server.server_close()
    report['passed']=not report['errors'] and len(report['checks'])==18 and all(c['passed'] for c in report['checks'])
    report['scope']='Actual keyboard, mute and focus handlers with a real 48 kHz AudioContext and analyser. Verifies worklet loading/output on standalone-file and HTTP origins, replacement ownership, stop and recovery. Not native event-time or complete waveform parity.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
