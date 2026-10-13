"""Check production note-stop decay against the pinned mixer's observed slope."""
from pathlib import Path
import argparse, hashlib, json, wave
import numpy as np
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    reference=ROOT/'testing/output/treehouse/research-audio-note-c/long.wav'
    with wave.open(str(reference)) as w:
        assert w.getframerate()==48000 and w.getsampwidth()==2
        native=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,w.getnchannels())[:,0].astype(int)
    end=np.flatnonzero(native)[-1]+1
    slope=np.diff(native[end-500:end])
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),checks=[dict(name='native final decay steps by four signed-16 units',passed=bool(np.all(slope==-4)))],cases=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        for hold in [.2,.9,2.1]:
            data=page.evaluate('''async hold=>{const c=new OfflineAudioContext(1,Math.ceil((hold+.3)*48000),48000);
              audio.context=new Proxy(c,{get(t,k){if(k==='state')return 'running';const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});
              audio.active.clear();audio.buffers.clear();if(audio.prepareContext)await audio.prepareContext(c);
              const id=playPitch(9,11);audio.stop(id,hold);return Array.from((await (async()=>{if(audio.flushCommands)await audio.flushCommands();return c.startRendering();})()).getChannelData(0));}''',hold)
            pcm=np.rint(np.array(data)*32768).astype(int);tail=pcm[round(hold*48000):];nz=np.flatnonzero(tail)
            count=int(nz[-1]+1) if len(nz) else 0
            decay=tail[:count+1];expected=np.sign(decay[:-1])*np.maximum(0,np.abs(decay[:-1])-4)
            ok=count>16 and count<len(tail)-1 and bool(np.array_equal(decay[1:],expected))
            report['cases'].append(dict(hold=hold,tail_samples=count,first_sample=int(tail[0]),passed=ok))
            report['checks'].append(dict(name=f'Bass stop after {hold}s uses observed decay',passed=ok))
            with wave.open(str(output/f'hold-{hold}.wav'),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm.astype('<i2').tobytes())
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Actual playPitch/OriginalAudio output at 48 kHz. Checks the native observed four-unit decay law at three stop phases; not absolute native input/output scheduling, replacement or full waveform parity.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
