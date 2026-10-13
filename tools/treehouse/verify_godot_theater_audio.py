"""Compare original observed theater PCM sources/rates with Godot dispatch.

Native observation may miss repeated starts of an already active sample. Each
observed source must occur in order within its recorded input interval; extra
Godot starts are retained. This does not prove exact dispatch/stop timing or
rendered audio waveform equality.
"""
import argparse,base64,hashlib,json
from pathlib import Path
from build_demo import ROOT
from compare_nature_audio_events import rate


def verify(journey,output):
    control=ROOT/'testing/output/treehouse/theater-native-journey-e'
    native=ROOT/'testing/output/treehouse/theater-audio-native-a'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    original=read(control/'run.json');observation=read(native/'run.json')
    current=read(journey/'report.json');actual=read(journey/'godot.json')
    assets=read(ROOT/'treehouse-godot/data/original.json')['pcm']
    hashes={key:hashlib.sha256(base64.b64decode(value['pcm'])).hexdigest() for key,value in assets.items()}
    rows=read(native/'sound-observations.json')['rows']
    controls=[dict(name=str(p),passed=digest(control/p)==digest(native/p)) for p in [Path('frames.jsonl'),Path('state/audio.wav')]+[p.relative_to(control) for p in (control/'state').glob('*.png')]]
    controls.append(dict(name='identical recorded inputs/checkpoints',passed=original['actions']==observation['actions'] and original['checkpoints']==observation['checkpoints']))
    controls.append(dict(name='Godot native journey passes and uses current runtime',passed=current['passed'] and all(digest(ROOT/p)==h for p,h in current['files'].items())))
    intervals=[];previous=original['checkpoints'][0]['after']['tick']
    for c,a in zip(original['checkpoints'],actual):
        assert c['name']==a['name']
        end=c['after']['tick']
        observed=[dict(tick=r['tick'],pcm_sha256=r['pcm_sha256'],rate=rate(r['header'][1])) for r in rows if r['active'] and previous<r['tick']<=end]
        cursor=0;matches=[];used=set()
        for event in observed:
            found=next((i for i in range(cursor,len(a['sounds'])) if hashes[a['sounds'][i]['key']]==event['pcm_sha256'] and a['sounds'][i]['rate']==event['rate']),None)
            matches.append(found)
            if found is not None:used.add(found);cursor=found+1
        intervals.append(dict(name=c['name'],native=observed,godot=a['sounds'],matches=matches,unmatched_godot=[e for i,e in enumerate(a['sounds']) if i not in used],passed=all(i is not None for i in matches)))
        previous=end
    starts=next(c['godot'] for c in intervals if c['name']=='editor')
    click=next((i for i,e in enumerate(starts) if e['key']=='digisnd:1008'),None)
    gap=starts[click+1]['tick']-starts[click]['tick'] if click is not None and click+1<len(starts) else None
    controls.append(dict(name='editor click finishes before curtain cue',passed=gap is not None and gap>=starts[click]['duration'],gap=gap))
    report=dict(passed=all(c['passed'] for c in controls+intervals),checks=controls,intervals=intervals,scope=__doc__,journey_sha256=digest(journey/'report.json'),native_run_sha256=digest(native/'run.json'),full_audio_parity=False)
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(dict(passed=report['passed'],observed=sum(len(i['native']) for i in intervals),failures=[i['name'] for i in controls+intervals if not i['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--journey',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.journey,a.output) else 1)
