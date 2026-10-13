"""Compare composed cache-hit work with the complete resident native profile."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_memory_lifetimes import shape_calls
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False);memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted generated memory')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    if work['routine']!='resident:7A66+all' or len(work['calls'])!=2494:raise ValueError('Incomplete full resident profile')
    initial=(scene_path.parent/scene['heap'][0]['path']).read_bytes();shapes,_=shape_calls(scene,initial);sounds,_=sound_calls(scene,initial)
    pairs=list(zip(shapes,memory['shapeChecks']))+list(zip(sounds,memory['soundChecks']));selected=[]
    for phase,check in pairs:
        if phase['key']!=check['key'] or not check['passed']:raise ValueError('Generated source correspondence differs')
        source=check['sourceWork']
        if source['action']!='cached':continue
        calls=[c for c in work['calls'] if phase['milliseconds']<=c['begin'] and c['end']<=phase['end']]
        if len(calls)!=1:raise ValueError('Expected one cache-hit call')
        selected.append((phase['key'],source['input'],calls[0]))
    if len(selected)!=2449:raise ValueError('Incomplete generated cache hits')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in ['memory-work.js','resource-work.js','resource-cache-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        models=page.evaluate('inputs=>inputs.map(i=>OriginalResourceCacheWork.resident(i))',[i for _,i,_ in selected]);browser.close()
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']};returns={c['call']:c for c in work['results']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for (key,input,call),model in zip(selected,models):
        actual=counts[call['ordinal']];expected=model['entries'];differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=[input['cachedHandle'],input['state'],input['segment']]==call['header'];return_equal=returns[call['ordinal']]['ax']==model['handle']
        results.append(dict(key=key,ordinal=call['ordinal'],instructions=model['instructions'],differences=differences,input_equal=input_equal,return_equal=return_equal,interrupt_only=bool(differences) and all(0x6447<=int(a)<0x6488 and d['expected']==0 for a,d in differences.items()),passed=input_equal and return_equal and not differences))
    report=dict(passed=all(r['passed'] for r in results),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),timer_interrupted_calls=[r['ordinal'] for r in results if r['interrupt_only']],calls=results,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-cache-work.js').read_bytes()).hexdigest(),memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='2449 generated cache-hit inputs with composed cache/address/length work compared against every observed resident instruction in each call. No instruction-range exclusions in the comparison. Cold loads, other callers, interrupts and CPU/PIC scheduling still need full composition.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
