"""Compare rendered piano attack level with pinned native audio (not timing parity)."""
from pathlib import Path
import argparse, hashlib, json, sys, wave
import numpy as np
from scipy.signal import correlate
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'testing/output/treehouse/research-audio-note-c'


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    driver = json.loads((REFERENCE / 'driver.json').read_text(encoding='utf-8'))
    with wave.open(str(REFERENCE / 'state/audio.wav')) as wav:
        assert wav.getframerate() == 48000 and wav.getnchannels() == 2 and wav.getsampwidth() == 2
        native = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').reshape(-1, 2)
    report = dict(demo_sha256=digest(html), reference_audio_sha256=digest(REFERENCE / 'state/audio.wav'),
                  reference_driver_sha256=digest(REFERENCE / 'driver.json'), checks=[], errors=[], fits=[],
                  full_waveform_parity=False,
                  scope='Actual OriginalAudio/playPitch Web Audio graph rendered offline at 48 kHz. '
                  'Native short and long Bass A-note attacks compared over 100 ms; normalized correlation '
                  'finds capture latency within 2000 samples, then level is measured without normalizing either signal. '
                  'Acceptance is attack correlation >0.99 and level within 5%; this does not establish exact '
                  'waveforms, output latency, stop decay, long-loop phase, other instruments or host speaker volume.')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        rendered = page.evaluate('''async()=>{
          const offline=new OfflineAudioContext(1,24000,48000);
          // The offline graph is built before rendering. Only the readiness guard
          // is adapted; all buffers, rates, gains and nodes come from production.
          audio.context=new Proxy(offline,{get(target,key){
            if(key==='state')return 'running';
            const value=Reflect.get(target,key,target);
            return typeof value==='function'?value.bind(target):value;
          }});
          audio.buffers.clear();if(audio.prepareContext)await audio.prepareContext(offline);
          const id=playPitch(9,11),voice=audio.active.get(id);
          const result={key:voice.key,rate:voice.rate,gain:voice.gain.gain.value};
          audio.stop(id,.15);
          result.pcm=Array.from((await (async()=>{if(audio.flushCommands)await audio.flushCommands();return offline.startRendering();})()).getChannelData(0));
          return result;
        }''')
        browser.close()
    pcm = np.array(rendered.pop('pcm'), dtype=np.float64)
    report['rendered'] = rendered
    with wave.open(str(output / 'browser.wav'), 'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(48000)
        wav.writeframes(np.clip(np.rint(pcm * 32768), -32768, 32767).astype('<i2').tobytes())
    pred = pcm[:4800] * 32768
    for branch in ['short', 'long']:
        first = next(e['audio_sample'] for e in driver['events'] if e['branch'] == branch)
        ref = native[first:first+12000, 0].astype(float)
        corr = correlate(ref, pred, mode='valid', method='fft')
        sums = np.r_[0, np.cumsum(ref * ref)]
        energy = sums[len(pred):] - sums[:-len(pred)]
        normalized = corr / np.sqrt(np.maximum(1, energy) * (pred @ pred))
        offset = int(np.argmax(normalized[:2000]))
        target = ref[offset:offset+len(pred)]
        # 0.4 means browser is 40% of native level; no fitted scale is applied.
        level = float(pred @ target / (target @ target))
        correlation = float(np.corrcoef(pred, target)[0, 1])
        report['fits'].append(dict(branch=branch, offset_samples=offset,
                                  browser_level_relative_to_native=level, correlation=correlation,
                                  unscaled_rmse=float(np.sqrt(np.mean((target-pred)**2)))))
        report['checks'].append(dict(name=branch+' attack level and shape', passed=abs(level-1)<.05 and correlation>.99))
    report['checks'].extend([
        dict(name='Bass A uses original sample and rounded hardware rate', passed=rendered['key']=='voices:12011' and rendered['rate']==11111),
        # The original forced stop decays its last signed-16 sample by four
        # per output sample. Even full scale is silent within 8192 samples.
        dict(name='forced stop is silent after bounded mixer decay', passed=bool(np.all(pcm[7200+8192:]==0))),
    ])
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report['passed']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.html,a.output) else 1)
