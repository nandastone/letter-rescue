"""Compare generated sound preparation branches with native instruction paths."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False)
    memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted generated memory evidence')
    for name,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest()!=digest:raise ValueError('Generated memory model changed')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    if work['routine']!='resident:E6E6':raise ValueError('Missing preparation profile')
    initial=(scene_path.parent/scene['heap'][0]['path']).read_bytes();phases,_=sound_calls(scene,initial)
    if len(phases)!=2399 or len(memory['soundChecks'])!=2399:raise ValueError('Incomplete sound coverage')
    inputs=[];native=[]
    for phase,check in zip(phases,memory['soundChecks']):
        if not check['passed'] or phase['key']!=check['key']:raise ValueError('Sound phase correspondence differs')
        calls=[c for c in work['calls'] if phase['milliseconds']<=c['begin'] and c['end']<=phase['end']]
        if len(calls)!=1:raise ValueError('Expected one preparation per load')
        native.append(calls[0]);inputs.append(dict(**check['preparation'],packedBytes=len(phase['payload'])-10))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/sound-work.js'))
        models=page.evaluate('a=>a.map(p=>OriginalSoundWork.preparation(p))',inputs);browser.close()
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']};returns={c['call']:c for c in work['results']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for phase,call,model in zip(phases,native,models):
        actual=counts[call['ordinal']];expected=model['entries'];returned=returns[call['ordinal']]['ax']==phase['expectedHandle']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        results.append(dict(key=phase['key'],ordinal=call['ordinal'],instructions=model['instructions'],differences=differences,return_equal=returned,passed=not differences and returned))
    report=dict(passed=all(c['passed'] for c in results),matching_calls=sum(c['passed'] for c in results),instructions=sum(c['instructions'] for c in results),checks=results,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/sound-work.js').read_bytes()).hexdigest(),memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='2399 intrinsic E6E6 preparation paths selected by the generated memory model, including native return handles. Callee work, payload writes, resampling and elapsed-time integration remain separate components.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'checks':[c for c in results if not c['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
