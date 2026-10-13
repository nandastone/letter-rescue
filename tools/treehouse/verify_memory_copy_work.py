"""Verify segmented copy instruction paths and generated sound-copy inputs."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]
FILES=['heap-instructions.js','graphics-work.js','memory-copy-work.js']


def verify(trace_path,memory_path,scene_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if work['routine']!='resident:6C18' or len(work['calls'])!=59:raise ValueError('Incomplete copy coverage')
    inputs=[dict(bytes=c['stack'][2]+65536*(c['stack'][3]&15),from_=c['stack'][4]+16*c['stack'][5],to=c['stack'][6]+16*c['stack'][7]) for c in work['calls']]
    for i in inputs:i['from']=i.pop('from_')
    base=trace['location']['main_base']+0xd510;results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in FILES:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        models=page.evaluate('rows=>rows.map(r=>OriginalMemoryCopyWork.copy(r))',inputs)
        for call,input,model in zip(work['calls'],inputs,models):
            slices=[s for s in work['slices'] if s['call']==call['ordinal']];cursor=0
            for repeat in model['repeats']:
                remaining=repeat['iterations'];budgets=[]
                while remaining or not budgets:
                    s=slices[cursor];cursor+=1
                    if s['address']-base!=repeat['address'] or s['remaining']!=remaining:raise ValueError('Invalid REP slice correspondence')
                    budgets.append(s['budget']);remaining-=min(remaining,max(1,s['budget']))
                dispatch=page.evaluate('a=>OriginalGraphicsWork.repeatString(a.iterations,a.budgets)',dict(iterations=repeat['iterations'],budgets=budgets))
                extra=dispatch['dispatches']-1;model['entries'][str(repeat['address'])]+=extra;model['instructions']+=extra;model['cycles']+=extra
            if cursor!=len(slices):raise ValueError('Unconsumed REP slices')
            actual={str(c['address']-base):c['entries'] for c in work['counts'] if c['call']==call['ordinal']};expected=model['entries']
            differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
            native_return=next(r for r in work['results'] if r['call']==call['ordinal']);returned=native_return['ax']+16*native_return['dx']==model['address']
            repetitions=sum(r['repetitions'] for r in work['counts'] if r['call']==call['ordinal']);repeat_equal=repetitions==sum(r['iterations'] for r in model['repeats'])
            results.append(dict(ordinal=call['ordinal'],input=input,instructions=model['instructions'],string_iterations=model['stringIterations'],backward=model['backward'],differences=differences,return_equal=returned,repeat_equal=repeat_equal,passed=not differences and returned and repeat_equal))
        focused=page.evaluate('''()=>{
          const a=OriginalMemoryCopyWork.copy({from:100,to:100,bytes:0}),b=OriginalMemoryCopyWork.copy({from:100,to:200000,bytes:0xfff1}),c=OriginalMemoryCopyWork.copy({from:100,to:102,bytes:0xffe1}),d=OriginalMemoryCopyWork.copy({from:100,to:105,bytes:5});
          let rejected=false;try{OriginalMemoryCopyWork.copy({from:0xfffff,to:100,bytes:2});}catch(e){rejected=true;}
          return [{name:'zero length skips REP',passed:a.repeats.length===0&&a.stringIterations===0},{name:'forward segment boundary preserves odd tail',passed:!b.backward&&b.repeats.map(r=>r.iterations).join(',')==='32760,0'&&b.stringIterations===32761},{name:'overlap uses backward chunks and odd tail',passed:c.backward&&c.repeats.map(r=>r.iterations).join(',')==='32752,0'&&c.stringIterations===32753},{name:'adjacent destination uses forward copy',passed:!d.backward},{name:'unsupported address wrap fails explicitly',passed:rejected}];
        }''');browser.close()
    memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text())
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted memory evidence')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated memory model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    phases,_=sound_calls(scene,(scene_path.parent/scene['heap'][0]['path']).read_bytes());generated=[]
    for phase,check in zip(phases,memory['soundChecks']):
        if phase['key']!=check['key'] or not check['passed']:raise ValueError('Generated sound correspondence differs')
        plan=check['preparation'].get('copy')
        if plan:
            calls=[c for c in work['calls'] if phase['milliseconds']<=c['begin'] and c['end']<=phase['end']]
            if len(calls)!=1:raise ValueError('Expected one sound copy')
            ordinal=calls[0]['ordinal'];generated.append(dict(key=phase['key'],ordinal=ordinal,passed=plan==inputs[ordinal] and results[ordinal]['passed']))
    report=dict(passed=len(generated)==2 and all(r['passed'] for r in results+focused+generated),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),checks=results,focused_checks=focused,generated_checks=generated,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in FILES},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),scope='All 59 native copy paths, returned destinations and REP iterations. Two sound-copy inputs are generated by continuous memory ownership; other copy arguments and CPU residual slice budgets remain explicit offline fixtures. Segmented multi-chunk cases have synthetic coverage; runtime scheduling remains open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'checks':[c for c in results if not c['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.memory,a.scene,a.output) else 1)
