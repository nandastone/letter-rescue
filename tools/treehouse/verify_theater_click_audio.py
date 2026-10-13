"""Render the actual editor button and compare its audible click with native PCM."""
from pathlib import Path
import argparse,hashlib,json,wave
import numpy as np
from scipy.signal import correlate
from playwright.sync_api import sync_playwright

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    native=DATA/'theater-audio-native-a';run=json.loads((native/'run.json').read_text())
    checkpoint=next(c for c in run['checkpoints'] if c['name']=='editor')
    rows=json.loads((native/'sound-observations.json').read_text())['rows']
    first=next(r for r in rows if r['active'] and checkpoint['inputs'][0]['from_tick']<r['tick']<=checkpoint['after']['tick'])
    with wave.open(str(native/'state/audio.wav')) as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(48000,2,2)
        pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)[:,0].astype(float)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),errors=[],checks=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        page.evaluate('''async()=>{setScene('theater');theater.options=true;theaterPanel();
          window.theaterAudioOrigin=tick;window.theaterAudioContext=new OfflineAudioContext(1,72000,48000);
          audio.context=new Proxy(theaterAudioContext,{get(t,k){if(k==='state')return 'running';if(k==='currentTime')return (tick-theaterAudioOrigin)/TICK_HZ;const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});
          audio.active.clear();audio.buffers.clear();await audio.prepareContext(theaterAudioContext);
        }''')
        page.get_by_role('button',name='Start the theater',exact=True).click()
        rendered=page.evaluate('''async()=>{advance(70);await audio.flushCommands();return Array.from((await theaterAudioContext.startRendering()).getChannelData(0));}''')
        browser.close()
    generated=np.rint(np.asarray(rendered)*32768).astype(int)
    with wave.open(str(output/'editor.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(generated.astype('<i2').tobytes())
    # One bounded recording offset; no gain fitting or per-window alignment.
    start=max(0,first['audio_sample']-4096);reference=pcm[start:first['audio_sample']+4096]
    n=2000;attack=generated[:n].astype(float);cross=correlate(reference,attack,mode='valid',method='fft')
    sums=np.r_[0,np.cumsum(reference**2)];energy=sums[n:]-sums[:-n]
    scores=cross/np.sqrt(np.maximum(1,energy)*max(1,attack@attack));offset=int(np.argmax(scores))
    expected=reference[offset:offset+n];rmse=float(np.sqrt(np.mean((attack-expected)**2)))
    report['attack']=dict(samples=n,native_offset=start+offset,correlation=float(scores[offset]),unscaled_rmse=rmse)
    report['checks'].append(dict(name='actual editor click reaches output and matches original attack exactly',passed=rmse==0 and bool(np.any(attack))))
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Actual visible Start the theater control and production mixer, rendered offline with game time as its scheduling clock. A 2000-sample click attack is compared against the original journey with one bounded alignment and no gain fit. Does not prove native input latency or complete curtain waveform parity.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
