"""Compare cache entry work using explicit native handle-state input fixtures."""
from pathlib import Path
import argparse,bisect,collections,hashlib,json,struct,sys
from playwright.sync_api import sync_playwright
from memory_catalog import read_catalogs

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,catalog_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if not work or work['routine']!='resident:7A66' or len(work['calls'])!=2494:raise ValueError('Incomplete cache coverage')
    records={}
    for catalog in read_catalogs(catalog_path.read_bytes(),13253):
        for record in catalog['records']:records.setdefault((record['tag'],record['id']),record)
    executable=(ROOT/'testing/output/treehouse/research-resources/unpacked.bin').read_bytes()
    if hashlib.sha256(executable).hexdigest()!='f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f':raise ValueError('Unresearched executable')
    for offset in [0x3166a,0x31679]:
        tag,id=struct.unpack_from('<IH',executable,offset)
        records.setdefault((tag.to_bytes(4,'big').strip(b'\0').decode('ascii'),id),dict(flags=executable[offset+12]))
    queries=[e for e in trace['events'] if e['label']=='resource.lookup'];times=[q['milliseconds'] for q in queries]
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']};inputs=[]
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    for call in work['calls']:
        index=bisect.bisect_right(times,call['begin'])-1
        if index<0:raise ValueError('Cache work has no lookup')
        q=queries[index];tag=(q['ax']+65536*q['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii');record=records[tag,q['cx']]
        inputs.append(dict(tag=tag,id=q['cx'],cachedHandle=call['header'][0],state=call['header'][1],segment=call['header'][2],directoryFlags=record['flags']))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
        models=page.evaluate('rows=>rows.map(q=>OriginalResourceWork.cache(q))',inputs)
        checks=page.evaluate('''()=>{
          const hot=OriginalResourceWork.cache({cachedHandle:10,state:0x11f0,segment:100});
          const cold=OriginalResourceWork.cache({directoryFlags:0xc0});
          const reload=OriginalResourceWork.cache({cachedHandle:10,state:0x1000,segment:0,directoryFlags:0xc0});
          let rejected=false;try{OriginalResourceWork.cache({cachedHandle:10,state:0x200,segment:1});}catch(e){rejected=true;}
          return [
            {name:'resident source skips allocation and reading',passed:hot.action==='cached'&&!hot.entries[0x7aab]&&!hot.entries[0x7a90]},
            {name:'new source applies promotion, lock and discardable actions',passed:cold.action==='load'&&cold.promote&&cold.discardable&&cold.entries[0x7ad1]===1},
            {name:'discarded source reallocates its existing handle',passed:reload.action==='reload'&&reload.entries[0x7a85]===1&&!reload.entries[0x7a90]},
            {name:'reload skips first-load flag actions',passed:!reload.promote&&!reload.discardable&&!reload.entries[0x7ac4]},
            {name:'unreconstructed EMS path rejects explicitly',passed:rejected}
          ];
        }''');browser.close()
    results=[]
    for input,call,model in zip(inputs,work['calls'],models):
        actual=counts[call['ordinal']];differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in actual.keys()|model['entries'].keys() if actual.get(a,0)!=model['entries'].get(a,0)}
        results.append(dict(input=input,ordinal=call['ordinal'],**model,differences=differences,passed=not differences))
    actions=dict(collections.Counter(r['action'] for r in results));reads=[e['milliseconds'] for e in trace['events'] if e['label']=='resource.read']
    covered=set();matched=True
    for call,result in zip(work['calls'],results):
        indices={i for i,t in enumerate(reads) if call['begin']<=t<=call['end']}
        matched=matched and len(indices)==(0 if result['action']=='cached' else 1);covered|=indices
    direct=[];begin=None
    for e in trace['events']:
        if e['label']=='resource.find':begin=e['milliseconds']
        elif e['label']=='resource.find.return':
            if begin is None:raise ValueError('Unpaired direct resource loader')
            direct.append([begin,e['milliseconds']]);begin=None
    outside={i for i in range(len(reads)) if i not in covered}
    checks.append(dict(name='every generated cache action matches its native read count',passed=matched and len(covered)==31))
    checks.append(dict(name='two remaining reads belong to separate direct SCR loads',passed=begin is None and len(direct)==2 and len(outside)==2 and len(reads)==33 and all(sum(a<=reads[i]<=b for i in outside)==1 for a,b in direct)))
    report=dict(passed=all(r['passed'] for r in results+checks),calls=results,checks=checks,actions=actions,
        exact_calls=sum(r['passed'] for r in results),total_calls=len(results),
        model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-work.js').read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),catalog_fixture_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        scope='Intrinsic 7A66/7A30 cache instruction work: 31 cached-loader reads; two direct SCR reads use a separate loader. Incoming handle states are explicit offline observations, not independently generated runtime state. External allocation/address/read/promote/flag callees and scheduling are excluded. Failed allocation/read recovery and EMS are not covered.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']][:10]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.catalog,a.output) else 1)
