"""Check audible car movement through real canvas input and production output."""
from pathlib import Path
import argparse, hashlib, json, wave
import numpy as np
from scipy.signal import correlate
from playwright.sync_api import sync_playwright
from verify_board_native_journey import model, ROOT
import browser_audio_observation as observation

DATA = ROOT / 'testing/output/treehouse'


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], attacks={})
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for kind, sound in [('money', 1020), ('chips', 1021)]:
            native = DATA / f'board-{kind}-audio-native-a'
            run = json.loads((native / 'run.json').read_text())
            point = run['decisions'][1]['point']
            initial = model(native / 'state/step-00.ram-0')
            initial.update(options=False, played=True, phase='move', hintRed=False)
            page = browser.new_page(viewport=dict(width=1360, height=960))
            page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            page.evaluate('''async m=>{setScene('boardgame');boardgame.motion.cancel();Object.assign(boardgame,m);boardgamePanel();render();
              window.moveOrigin=tick;window.moveContext=new OfflineAudioContext(1,96000,48000);
              audio.context=new Proxy(moveContext,{get(t,k){if(k==='state')return 'running';if(k==='currentTime')return (tick-moveOrigin)/TICK_HZ;const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});
              audio.active.clear();audio.buffers.clear();await audio.prepareContext(moveContext);
            }''', initial)
            observation.install(page)
            box = page.locator('#game').bounding_box()
            page.mouse.click(box['x'] + (point[0] + .1) * box['width'] / 320, box['y'] + (point[1] + .1) * box['height'] / 200)
            rendered = page.evaluate('''async()=>{advance(110);await audio.flushCommands();return {pcm:Array.from((await moveContext.startRendering()).getChannelData(0)),events:soundEvents,origin:moveOrigin,tickHz:TICK_HZ};}''')
            page.close()
            generated = np.rint(np.asarray(rendered['pcm']) * 32768).astype(int)
            with wave.open(str(output / (kind + '.wav')), 'wb') as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(48000); wav.writeframes(generated.astype('<i2').tobytes())
            events = [e for e in rendered['events'] if e['type'] == 'start' and e['key'] == f'digisnd:{sound}']
            if not events:
                report['checks'].append(dict(name=kind + ' car movement is audible', passed=False))
                report['attacks'][kind] = dict(missing_source=True)
                continue
            sample = round((events[0]['tick'] - rendered['origin']) / rendered['tickHz'] * 48000)
            rows = json.loads((native / 'sound-observations.json').read_text())['rows']
            # The first source in step-01 is the car effect; earlier rolling is
            # excluded by the saved preceding checkpoint tick.
            import struct
            prior = struct.unpack_from('<I', (native / 'state/step-00.ram-0').read_bytes(), 0x323f0 + 0x201e)[0]
            event = next(r for r in rows if r['active'] and r['tick'] > prior)
            with wave.open(str(native / 'state/audio.wav')) as wav:
                assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (48000, 2, 2)
                pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').reshape(-1, 2)[:, 0].astype(float)
            n = 2000; start = max(0, event['audio_sample'] - 4096)
            reference = pcm[start:event['audio_sample'] + 4096 + n]
            attack = generated[sample:sample + n].astype(float)
            cross = correlate(reference, attack, mode='valid', method='fft')
            sums = np.r_[0, np.cumsum(reference ** 2)]; energy = sums[n:] - sums[:-n]
            scores = cross / np.sqrt(np.maximum(1, energy) * max(1, attack @ attack))
            offset = int(np.argmax(scores)); rmse = float(np.sqrt(np.mean((attack - reference[offset:offset + n]) ** 2)))
            report['attacks'][kind] = dict(samples=n, native_offset=start + offset, generated_offset=sample, correlation=float(scores[offset]), unscaled_rmse=rmse)
            report['checks'].append(dict(name=kind + ' car movement output matches original attack', passed=rmse == 0 and bool(np.any(attack))))
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'One saved board snapshot per player, followed by an actual canvas road click and production audio rendering. 2000 attack samples matched after one bounded alignment per effect without gain fitting. Does not prove complete movement waveform, stop timing or native input latency.'
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2)); return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); raise SystemExit(0 if verify(args.html, args.output) else 1)
