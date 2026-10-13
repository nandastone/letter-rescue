"""Check that restored nature feedback reaches the production audio output."""
from pathlib import Path
import argparse, hashlib, json, wave
import numpy as np
from scipy.signal import correlate
from playwright.sync_api import sync_playwright

DATA = Path(__file__).resolve().parents[2] / 'testing/output/treehouse'


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    native = DATA / 'nature-edit-audio-native-a'
    run = json.loads((native / 'run.json').read_text())
    rows = json.loads((native / 'sound-observations.json').read_text())['rows']
    with wave.open(str(native / 'state/audio.wav')) as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (48000, 2, 2)
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').reshape(-1, 2)[:, 0].astype(float)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], attacks={})
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for name, samples in [('day-animal', 2000), ('night', 12000)]:
            cp = next(c for c in run['checkpoints'] if c['name'] == name)
            event = next(r for r in rows if r['active'] and cp['inputs'][0]['from_tick'] < r['tick'] <= cp['after']['tick'])
            page = browser.new_page()
            page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            page.evaluate('''async()=>{setScene('nature');nature.mode='explore';naturePanel();
              window.feedbackOrigin=tick;window.feedbackContext=new OfflineAudioContext(1,24000,48000);
              audio.context=new Proxy(feedbackContext,{get(t,k){if(k==='state')return 'running';if(k==='currentTime')return (tick-feedbackOrigin)/TICK_HZ;const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});
              audio.active.clear();audio.buffers.clear();await audio.prepareContext(feedbackContext);
            }''')
            if name == 'night':
                page.get_by_role('button', name='Switch to nighttime', exact=True).click()
            else:
                value = page.locator('#nature-animal option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                page.locator('#nature-animal').select_option(value)
            rendered = page.evaluate('''async()=>{advance(20);await audio.flushCommands();return Array.from((await feedbackContext.startRendering()).getChannelData(0));}''')
            page.close()
            generated = np.rint(np.asarray(rendered) * 32768).astype(int)
            with wave.open(str(output / (name + '.wav')), 'wb') as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(48000)
                wav.writeframes(generated.astype('<i2').tobytes())
            start = max(0, event['audio_sample'] - 4096)
            reference = pcm[start:event['audio_sample'] + 4096 + samples]
            attack = generated[:samples].astype(float)
            cross = correlate(reference, attack, mode='valid', method='fft')
            sums = np.r_[0, np.cumsum(reference ** 2)]
            energy = sums[samples:] - sums[:-samples]
            scores = cross / np.sqrt(np.maximum(1, energy) * max(1, attack @ attack))
            offset = int(np.argmax(scores))
            rmse = float(np.sqrt(np.mean((attack - reference[offset:offset + samples]) ** 2)))
            report['attacks'][name] = dict(samples=samples, native_offset=start + offset, correlation=float(scores[offset]), unscaled_rmse=rmse)
            report['checks'].append(dict(name=name + ' actual control produces original sound attack', passed=rmse == 0 and bool(np.any(attack))))
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Visible animal selection and day/night controls through production output, rendered offline with the game clock. One bounded native alignment per cue, no gain fitting. Checks audible cue attacks; does not establish full waveform or native input latency.'
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.html, args.output) else 1)
