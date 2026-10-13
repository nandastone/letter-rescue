"""Compose allocation/lock wrappers with generated near and far allocator work."""
from pathlib import Path
import argparse, hashlib, json, sys
from playwright.sync_api import sync_playwright
from verify_memory_lifetimes import shape_calls
from sound_memory_calls import sound_calls

ROOT = Path(__file__).resolve().parents[2]
RANGES = [(0x003d,0x0076),(0x0590,0x060c),(0x6510,0x658a),(0x659e,0x65b2),(0x6d47,0x6ea3),(0x6fd8,0x7011),(0x75c6,0x7668)]


def verify(memory_path, scene_path, trace_path, output):
    output.mkdir(parents=True, exist_ok=False)
    memory, scene, trace = [json.loads(p.read_text()) for p in [memory_path, scene_path, trace_path]]
    if not memory['passed'] or memory['trace_sha256'] != hashlib.sha256(scene_path.read_bytes()).hexdigest():
        raise ValueError('Unaccepted generated memory')
    for f, digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() != digest:
            raise ValueError('Stale generated model')
    if any(scene[k] != trace[k] for k in ['events','boundaries','actions']):
        raise ValueError('Observer runs differ')
    work = trace['work']
    if work['routine'] != 'resident:7A66+all' or len(work['calls']) != 2494:
        raise ValueError('Incomplete full resident profile')
    initial = (scene_path.parent/scene['heap'][0]['path']).read_bytes()
    shapes,_ = shape_calls(scene, initial)
    sounds,_ = sound_calls(scene, initial)
    selected = []
    for phase, check in list(zip(shapes,memory['shapeChecks']))+list(zip(sounds,memory['soundChecks'])):
        if phase['key'] != check['key'] or not check['passed']:
            raise ValueError('Generated source correspondence differs')
        source = check['sourceWork']
        if source['action'] != 'load':
            continue
        if source['promote']:
            raise ValueError('Promotion composition remains separate')
        calls = [c for c in work['calls'] if phase['milliseconds'] <= c['begin'] and c['end'] <= phase['end']]
        near = [c for c in memory['nearChecks'] if c['contextTime'] == phase['milliseconds']]
        far = [c for c in memory['allocationChecks'] if c['contextTime'] == phase['milliseconds']]
        if len(calls) != 1 or not near or near[0]['bytes'] != 4 or not far:
            raise ValueError('Missing generated source allocation')
        if far[0]['bytes'] != check['operations'][0]['bytes']:
            raise ValueError('Source payload size differs')
        selected.append(dict(key=phase['key'],call=calls[0],input=dict(handle=near[0]['pointer'],blockAddress=far[0]['address'],discardable=source['discardable']),near=near[0]['work'],far=far[0]['work']))
    if len(selected) != 29:
        raise ValueError('Incomplete generated source allocation coverage')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        for f in ['memory-work.js','memory-wrapper-work.js']:
            page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        generated = page.evaluate('''rows=>rows.map(row=>{
          const a=OriginalMemoryWrapperWork.allocateHandle(row.input),lock=OriginalMemoryWrapperWork.lock(a),entries={};
          const parts=[a,OriginalMemoryWrapperWork.farAllocation(),lock,lock.addressWork,row.near,row.far];
          if(row.input.discardable)parts.push(OriginalMemoryWrapperWork.discardable({handle:a.handle,state:a.state|0x1000}));
          for(const p of parts)for(const [at,n] of Object.entries(p.entries))entries[at]=(entries[at]||0)+n;
          return {entries,handle:a.handle,instructions:Object.values(entries).reduce((a,b)=>a+b,0)};
        })''',selected)
        checks = page.evaluate('''()=>{
          const nil=OriginalMemoryWrapperWork.lock({handle:0});
          const absent=OriginalMemoryWrapperWork.lock({handle:102,state:0x4000,segment:0});
          const present=OriginalMemoryWrapperWork.lock({handle:102,state:2,segment:16});
          const discard=OriginalMemoryWrapperWork.discardable({handle:0,state:0});
          const a=OriginalMemoryWrapperWork.allocateHandle({handle:102,blockAddress:258});
          let failed=false;try{OriginalMemoryWrapperWork.allocateHandle({handle:0,blockAddress:0});}catch(e){failed=true;}
          return [
            {name:'null lock has no memory write',passed:nil.address===0&&!nil.entries[0x6521]},
            {name:'nonresident lock preserves flags',passed:absent.state===0x4000&&!absent.entries[0x6521]},
            {name:'resident lock refreshes age and lock bit',passed:present.address===264&&present.state===0x81f2&&present.entries[0x6521]===1},
            {name:'null discardable skips memory write',passed:discard.state===0&&!discard.entries[0x65a8]},
            {name:'handle stores segment and low offset',passed:a.state===0x1f2&&a.segment===16&&a.instructions===40},
            {name:'unreconstructed allocation failure is explicit',passed:failed}
          ];
        }''')
        browser.close()
    base = trace['location']['main_base']+0xd510
    counts = {c['ordinal']:{} for c in work['calls']}
    returns = {r['call']:r['ax'] for r in work['results']}
    for c in work['counts']:
        a = c['address']-base
        if any(lo <= a < hi for lo,hi in RANGES):
            counts[c['call']][str(a)] = c['entries']
    results = []
    for selected, model in zip(selected,generated):
        ordinal = selected['call']['ordinal']
        actual,expected = counts[ordinal],model['entries']
        if any(not any(lo <= int(a) < hi for lo,hi in RANGES) for a in expected):
            raise ValueError('Generated instructions outside verified allocation scope')
        differences = {a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0) != expected.get(a,0)}
        return_equal = model['handle'] == returns[ordinal]
        results.append(dict(key=selected['key'],ordinal=ordinal,instructions=model['instructions'],differences=differences,return_equal=return_equal,passed=return_equal and not differences))
    report = dict(passed=all(r['passed'] for r in results+checks),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),calls=results,checks=checks,ranges=RANGES,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/memory-wrapper-work.js').read_bytes()).hexdigest(),memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='29 cold resource source allocations. Wrappers compose with near/far allocator work derived from continuous generated memory, plus lock address and discardable paths. Compares every instruction in listed memory ranges and cache return handles. File reads, cache intrinsic, timer interruptions, other cold calls and full scheduling remain separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2))
    return report['passed']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['memory','scene','trace','output']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
