"""Compare observed original theater sounds with production browser dispatch.

The native observer can miss repeated starts of the same still-active sample.
Consequently this checks that each observed source occurs in order, allowing
additional browser starts. It cannot prove complete event or waveform parity.
"""
from pathlib import Path
import argparse,base64,hashlib,json

digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))

def compare(html,native,browser,control,output):
    output.mkdir(parents=True,exist_ok=False)
    text=html.read_text(encoding='utf-8');start=text.index('const ORIGINAL = ')+len('const ORIGINAL = ')
    assets=json.loads(text[start:text.index(';</script>',start)])
    hashes={k:hashlib.sha256(base64.b64decode(v['pcm'])).hexdigest() for k,v in assets['pcm'].items()}
    keys={}
    for k,v in hashes.items():keys.setdefault(v,[]).append(k)
    reference=read(native/'run.json');original=read(control/'run.json');actual=read(browser/'report.json')
    assert reference['passed'] and original['passed'] and actual['demo_sha256']==digest(html)
    control_files=[p.relative_to(control) for p in (control/'state').glob('*.png')]+[Path('state/audio.wav'),Path('frames.jsonl')]
    control_checks=[dict(path=str(p),passed=digest(control/p)==digest(native/p)) for p in control_files]
    control_checks+=[dict(path='actions',passed=reference['actions']==original['actions']),dict(path='checkpoints',passed=reference['checkpoints']==original['checkpoints'])]
    rows=read(native/'sound-observations.json')['rows'];initial=reference['checkpoints'][0]['after']['tick']
    checkpoints=[];prior=initial;missing=[]
    for cp in reference['checkpoints']:
        end=cp['after']['tick'];observed=[dict(tick=r['tick'],keys=keys.get(r['pcm_sha256'],[]),pcm_sha256=r['pcm_sha256'],rate=r['header'][1]) for r in rows if r['active'] and prior<r['tick']<=end]
        dispatched=[e for e in actual['sound_events'] if e['type']=='start' and e['checkpoint']==cp['name']]
        cursor=0;matches=[]
        for event in observed:
            index=next((i for i in range(cursor,len(dispatched)) if hashes[dispatched[i]['key']]==event['pcm_sha256']),None)
            matches.append(dict(native=event,browser=dispatched[index] if index is not None else None))
            if index is None:missing.append(dict(checkpoint=cp['name'],**event))
            else:cursor=index+1
        checkpoints.append(dict(name=cp['name'],native=observed,browser=dispatched,matches=matches,passed=all(m['browser'] is not None for m in matches)))
        prior=end
    editor=next(c for c in checkpoints if c['name']=='editor')
    starts=editor['browser'];click=next((i for i,e in enumerate(starts) if e['key']=='digisnd:1008'),None)
    sample=assets['pcm']['digisnd:1008'];rate=int(1000000//(1000000//sample['rate']))
    duration=len(base64.b64decode(sample['pcm']))/rate*(1193181/19886)
    gap=starts[click+1]['tick']-starts[click]['tick'] if click is not None and click+1<len(starts) else None
    cue_checks=[dict(name='editor button click finishes before curtain sound replaces it',passed=gap is not None and gap>=duration,click_duration_ticks=duration,next_sound_after_ticks=gap)]
    report=dict(demo_sha256=digest(html),reference=str(native),browser_report=str(browser/'report.json'),
        browser_report_sha256=digest(browser/'report.json'),control=str(control),control_checks=control_checks,
        checkpoints=checkpoints,missing=missing,cue_checks=cue_checks,passed=all(c['passed'] for c in control_checks+cue_checks) and not missing,
        full_audio_parity=False,scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('control',all(c['passed'] for c in control_checks),'missing observed sounds',len(missing))
    print('cue completion',cue_checks)
    for c in checkpoints:
        if not c['passed']:print(c['name'],'native',[n['keys'] for n in c['native']],'browser',[e['key'] for e in c['browser']])
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['html','native','browser','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if compare(a.html,a.native,a.browser,a.control,a.output) else 1)
