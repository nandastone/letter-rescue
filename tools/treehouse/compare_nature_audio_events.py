"""Compare observed original nature sound sources with browser dispatch.

Requires unchanged native control media/actions/states and source/rate order
within each ordinary-input interval. Same-source restarts between observations
can be missed, so extra browser starts are reported rather than accepted as
proof of complete event-count parity. Full output and exact timing are separate.
"""
from pathlib import Path
import argparse,base64,hashlib,json

digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def rate(requested):
    q=1000000//requested
    return 1000000//q if 0<q<256 else requested

def compare(html,native,browser,control,output):
    output.mkdir(parents=True,exist_ok=False)
    text=html.read_text(encoding='utf-8');start=text.index('const ORIGINAL = ')+len('const ORIGINAL = ')
    assets=json.loads(text[start:text.index(';</script>',start)])
    hashes={k:hashlib.sha256(base64.b64decode(v['pcm'])).hexdigest() for k,v in assets['pcm'].items()};keys={}
    for k,h in hashes.items():keys.setdefault(h,[]).append(k)
    reference=read(native/'run.json');original=read(control/'run.json');actual=read(browser/'report.json')
    assert reference['passed'] and original['passed'] and actual['passed'] and actual['demo_sha256']==digest(html)
    files=[p.relative_to(control) for p in (control/'state').glob('*.png')]+[Path('state/audio.wav'),Path('frames.jsonl')]
    checks=[dict(path=str(p),passed=(native/p).exists() and digest(control/p)==digest(native/p)) for p in files]
    checks+=[dict(path='actions',passed=reference['actions']==original['actions']),dict(path='checkpoints',passed=reference['checkpoints']==original['checkpoints'])]
    names={c['name'] for c in actual['checkpoints']};checkpoints=[c for c in reference['checkpoints'] if c['name'] in names]
    assert len(checkpoints)==len(names) and checkpoints[0]['name']=='initial'
    rows=read(native/'sound-observations.json')['rows'];prior=checkpoints[0]['after']['tick'];intervals=[];missing=[];overlaps=[]
    for cp in checkpoints:
        end=cp['after']['tick'];observed=[dict(tick=r['tick'],keys=keys.get(r['pcm_sha256'],[]),pcm_sha256=r['pcm_sha256'],rate=rate(r['header'][1])) for r in rows if r['active'] and prior<r['tick']<=end]
        dispatched=[e for e in actual['sound_events'] if e['type']=='start' and e['checkpoint']==cp['name']]
        cursor=0;matches=[];matched=set()
        for event in observed:
            index=next((i for i in range(cursor,len(dispatched)) if hashes[dispatched[i]['key']]==event['pcm_sha256'] and dispatched[i]['rate']==event['rate']),None)
            matches.append(dict(native=event,browser=dispatched[index] if index is not None else None))
            if index is None:missing.append(dict(checkpoint=cp['name'],**event))
            else:cursor=index+1;matched.add(index)
        for a,b in zip(matches,matches[1:]):
            if a['browser'] and b['browser'] and a['browser']['tick']==b['browser']['tick'] and b['native']['tick']-a['native']['tick']>2:
                overlaps.append(dict(checkpoint=cp['name'],first=a,second=b))
        intervals.append(dict(name=cp['name'],native=observed,browser=dispatched,matches=matches,unmatched_browser=[e for i,e in enumerate(dispatched) if i not in matched],passed=all(m['browser'] is not None for m in matches)))
        prior=end
    report=dict(demo_sha256=digest(html),reference=str(native),browser_report=str(browser/'report.json'),browser_report_sha256=digest(browser/'report.json'),control=str(control),control_checks=checks,checkpoints=intervals,missing=missing,suspicious_same_tick_replacements=overlaps,passed=all(c['passed'] for c in checks) and not missing and not overlaps,full_audio_parity=False,scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('control',all(c['passed'] for c in checks),'observed',sum(len(c['native']) for c in intervals),'missing',len(missing),'same-tick replacements',len(overlaps))
    for c in intervals:
        if not c['passed']:print(c['name'],'native',[n['keys'] for n in c['native']],'browser',[e['key'] for e in c['browser']])
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['html','native','browser','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if compare(a.html,a.native,a.browser,a.control,a.output) else 1)
