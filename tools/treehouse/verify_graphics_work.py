"""Compare recovered graphics work with original per-instruction observations.

Expected work is computed in JavaScript from independently decoded DAT pixels.
No native timestamps, framebuffer images or instruction counts feed the model.
"""
from pathlib import Path
from collections import defaultdict
import argparse, hashlib, json, struct, sys, zipfile
from playwright.sync_api import sync_playwright
from images import decode_shape
from resources import parse_archive
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def verify(trace_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());work=trace['work']
    methods={'resident:DE10':None,'resident:DF85':3,'resident:E03E':4}
    if not work or work['routine'] not in methods:raise ValueError('Graphics work observations required')
    method=methods[work['routine']]
    source=DATA/'source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched original archive')
    with zipfile.ZipFile(source) as z:archive=z.read('TheTreeh/th.dat')
    raw={r['id']:archive[r['payload_offset']:r['payload_offset']+r['size']] for r in parse_archive(archive) if r['tag']=='SHAP'}
    shapes={rid:decode_shape(payload) for rid,payload in raw.items()}
    calls={c['ordinal']:c for c in work['calls']}
    if len(calls)!=len(work['calls']):raise ValueError('Duplicate work call')
    counts=defaultdict(dict);base=trace['location']['main_base']+0xd510
    for row in work['counts']:
        address=str(row['address']-base)
        if address in counts[row['call']]:raise ValueError('Duplicate instruction count')
        counts[row['call']][address]=row['entries']
    preloads=[];pending=None;group=None
    for event in trace['events']:
        if event['label']=='wrapper.begin':group=event['stack'][10]
        elif event['label']=='scr.preload':
            if pending is not None:raise ValueError('Nested preload')
            pending=dict(id=group+event['stack'][0],begin=event['milliseconds'])
        elif event['label']=='scr.preload.return':
            if pending is None:raise ValueError('Unmatched preload return')
            preloads.append({**pending,'end':event['milliseconds']});pending=None
    if pending is not None or len(preloads)!=30:raise ValueError('Incomplete preload fixture')
    results=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)));page.add_script_tag(path=str(ROOT/'treehouse-demo/graphics-work.js'))
        for preload in preloads:
            flags=struct.unpack_from('<H',raw[preload['id']],4)[0]
            selected=[c for c in calls.values() if preload['begin']<=c['begin'] and c['end']<=preload['end']]
            if method is not None and (flags>>8)&15!=method:
                if selected:raise ValueError('Wrong decompressor selected')
                continue
            if len(selected)!=1:raise ValueError('Preload does not contain one selected expansion')
            call=selected[0];w,h,pixels=shapes[preload['id']]
            actual=counts[call['ordinal']]
            if method is None:
                model=page.evaluate('s=>OriginalGraphicsWork.nibbleExpansion(s)',dict(w=w,h=h,pixels=list(pixels)))
                header_matches=call['header']==[h,w,(w+1)//2]
            else:
                stride=(w*(((flags>>12)&7)+1)+7)//8
                model=page.evaluate('s=>OriginalGraphicsWork.lzExpansion(s)',dict(method=method,height=h,stride=stride,compressed=list(raw[preload['id']][6:])))
                header_matches=call['stack'][2:5]==[h,stride,h*stride] if method==4 else call['stack'][2]==h*stride
                slices=[s for s in work.get('slices',[]) if s['call']==call['ordinal']]
                if slices:
                    dispatch=page.evaluate('s=>OriginalGraphicsWork.repeatString(512,s)',[s['budget'] for s in slices])
                    extra=dispatch['dispatches']-1
                    model['entries'][str(model['repAddress'])]+=extra
                    model['instructions']+=extra;model['cycles']+=extra
                    header_matches=header_matches and dispatch['entries']==[s['remaining'] for s in slices]
            differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in set(actual)|set(model['entries']) if actual.get(a,0)!=model['entries'].get(a,0)}
            if method is not None:
                repetitions=sum(r['repetitions'] for r in work['counts'] if r['call']==call['ordinal'])
                if repetitions!=model['repIterations']:differences['REP iterations']=dict(expected=model['repIterations'],actual=repetitions)
            results.append(dict(id=preload['id'],ordinal=call['ordinal'],header=call['header'],header_matches=header_matches,instructions=model['instructions'],cycles=model['cycles'],observed_instructions=sum(actual.values()),differences=differences,passed=not differences and header_matches,
                                rep_slice_fixtures=slices if method is not None else []))
        checks=page.evaluate('''()=>{let rejected=false;try{OriginalGraphicsWork.nibbleExpansion({w:1,h:1,pixels:[16]});}catch(e){rejected=true;}const a=OriginalGraphicsWork.nibbleExpansion({w:1,h:1,pixels:[0]}),b=OriginalGraphicsWork.nibbleExpansion({w:1,h:1,pixels:[7]}),c=OriginalGraphicsWork.nibbleExpansion({w:2,h:1,pixels:[0,0]});return [{name:'nonzero nibble adds exactly its original conditional instruction',passed:b.instructions===a.instructions+1&&b.cycles===a.cycles+1},{name:'odd-width row excludes padded low nibble',passed:!a.entries[0xde51]&&a.entries[0xde5d]===1&&c.entries[0xde51]===1},{name:'rejects non-nibble image data',passed:rejected}];}''')
        checks.extend(page.evaluate('''()=>{const interrupted=OriginalGraphicsWork.repeatString(512,[200,1000]),zero=OriginalGraphicsWork.repeatString(2,[0,1]);let unfinished=false,extra=false,truncated=false;try{OriginalGraphicsWork.repeatString(512,[200]);}catch(e){unfinished=true;}try{OriginalGraphicsWork.repeatString(1,[10,10]);}catch(e){extra=true;}try{OriginalGraphicsWork.lzExpansion({method:3,height:1,stride:4,compressed:[255,1]});}catch(e){truncated=true;}return [{name:'REP continuation retains remaining iterations and charges redispatch',passed:JSON.stringify(interrupted.entries)==='[512,312]'&&interrupted.cycles===514},{name:'zero remaining budget still permits first DoString iteration',passed:JSON.stringify(zero.entries)==='[2,1]'}, {name:'rejects incomplete or extra REP dispatch budgets',passed:unfinished&&extra},{name:'rejects truncated compressed input',passed:truncated}];}'''))
        browser.close()
    expected_calls={None:30,3:6,4:24}[method]
    if len(results)!=expected_calls:raise ValueError('Selected routine coverage is incomplete')
    report=dict(routine=work['routine'],model_sha256=hashlib.sha256((ROOT/'treehouse-demo/graphics-work.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),source_sha256=SOURCE_SHA,
                calls=results,checks=checks,errors=errors,passed=not errors and all(r['passed'] for r in results) and all(c['passed'] for c in checks),
                scope='Selected-routine instruction paths derive from original DAT contents. REP redispatch uses explicitly supplied native residual-budget fixtures; the complete runtime clock must derive those budgets independently. External interrupt/callee work and presentation scheduling are not included.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']],'exact_calls':sum(r['passed'] for r in results),'total_calls':len(results)},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.output) else 1)
