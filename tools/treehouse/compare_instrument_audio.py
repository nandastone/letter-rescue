"""Measure native/browser instrument attacks and sustained waveform drift."""
from pathlib import Path
import argparse, hashlib, json, wave
import numpy as np
from scipy.signal import correlate
from playwright.sync_api import sync_playwright


def compare(html, reference, output, mixer_probe=False):
    output.mkdir(parents=True, exist_ok=False)
    native = json.loads((reference/'report.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    with wave.open(str(reference/'state/audio.wav')) as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth()) == (48000,2,2)
        recording=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)[:,0].astype(float)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                reference_sha256=hashlib.sha256((reference/'report.json').read_bytes()).hexdigest(),
                mixer_rate_probe=mixer_probe,complete=False,cases=[],errors=[],full_waveform_parity=False,
                scope='Production playPitch/OriginalAudio graph rendered offline at 48 kHz. '
                      'Attack correlation estimates capture latency only; no gain scaling. '
                      'Later windows retain that one alignment to expose resampling/loop drift. '
                      'Diagnostic measurements, not exact scheduling or waveform acceptance.')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        try:
            for case in native['cases']:
                hold=(case['keyup']['audio_sample']-case['start']['audio_sample'])/48000
                pitch=16 if case['label']=='high' else 9
                rendered=page.evaluate('''async m=>{
                  const offline=new OfflineAudioContext(1,Math.ceil((m.hold+.4)*48000),48000);
                  audio.context=new Proxy(offline,{get(target,key){if(key==='state')return 'running';
                    const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;}});
                  audio.active.clear();audio.buffers.clear();if(audio.prepareContext)await audio.prepareContext(offline);
                  const id=playPitch(m.pitch,m.instrument),v=audio.active.get(id);
                  if(m.mixerProbe){if(audio.renderer)throw new Error('Legacy rate-only probe requires the previous BufferSource renderer');v.source.playbackRate.value=(Math.floor(v.rate*16384/48000)*48000/16384)/ORIGINAL.pcm[v.key].rate;}
                  const result={key:v.key,rate:v.rate,pcmRate:ORIGINAL.pcm[v.key].rate,outputRate:v.source.playbackRate.value*ORIGINAL.pcm[v.key].rate,count:v.source.buffer.length,loop:v.source.loop,
                    loopStart:v.source.loopStart,loopEnd:v.source.loopEnd,gain:v.gain.gain.value};
                  audio.stop(id,m.hold);result.pcm=Array.from((await (async()=>{if(audio.flushCommands)await audio.flushCommands();return offline.startRendering();})()).getChannelData(0));return result;
                }''',dict(hold=hold,pitch=pitch,instrument=case['instrument'],mixerProbe=mixer_probe))
                pcm=np.asarray(rendered.pop('pcm'),dtype=float)*32768
                start=case['start']['audio_sample'];ref=recording[start:case['end']['audio_sample']]
                n=4800;pred=pcm[:n];corr=correlate(ref[:n+2500],pred,mode='valid',method='fft')
                sums=np.r_[0,np.cumsum(ref[:n+2500]**2)];energy=sums[n:]-sums[:-n]
                score=corr/np.sqrt(np.maximum(1,energy)*max(1,pred@pred))
                offset=int(np.argmax(score));windows=[]
                for seconds in [0,.5,1,2]:
                    at=round(seconds*48000)
                    if at+n>hold*48000:continue
                    a=pcm[at:at+n];b=ref[offset+at:offset+at+n]
                    if len(b)!=n:continue
                    windows.append(dict(start_seconds=seconds,correlation=float(np.corrcoef(a,b)[0,1]) if np.std(a)*np.std(b)>0 else None,
                                        level=float(a@b/(b@b)) if b@b else None,
                                        browser_rms=float(np.sqrt(np.mean(a*a))),native_rms=float(np.sqrt(np.mean(b*b))),
                                        unscaled_rmse=float(np.sqrt(np.mean((a-b)**2)))))
                headers=[row['header'] for row in case['rows'] if row['active']]
                result=dict(instrument=case['instrument'],label=case['label'],hold_seconds=hold,
                            offset_samples=offset,rendered=rendered,native_header=headers[0],
                            forced_stop=all(row['release']==0 for row in case['rows']),windows=windows)
                report['cases'].append(result)
                filename=f"{case['instrument']:02}-{case['label']}.wav"
                with wave.open(str(output/filename),'wb') as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
                    w.writeframes(np.clip(np.rint(pcm),-32768,32767).astype('<i2').tobytes())
                print(case['instrument'],case['label'],[(v['start_seconds'],round(v['correlation'],4) if v['correlation'] is not None else None) for v in windows],flush=True)
            report['complete']=not report['errors']
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['complete']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mixer-rate-probe',action='store_true');a=p.parse_args()
    raise SystemExit(0 if compare(a.html,a.reference,a.output,a.mixer_rate_probe) else 1)
