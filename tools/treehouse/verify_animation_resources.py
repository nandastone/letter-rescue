"""Verify independent SCR preload planning against native constructor calls.

The trace provides expected resource IDs/order only. Its timestamps are never
fed to the browser. This checks resource semantics, not loading-time parity.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(html, trace_path, output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text())
    if trace.get('profile')!='resources' or trace.get('no_probe'):raise ValueError('Resource trace required')
    expected=[];current=None;wrapper=None
    for event in trace['events']:
        if event['label']=='wrapper.begin':wrapper=event['stack']
        elif event['label']=='scr.allocate':
            if current is not None or wrapper is None:raise ValueError('Unmatched constructor')
            current=dict(archive='th',id=wrapper[9]+wrapper[10],palette=wrapper[10],relative=[])
        elif event['label']=='scr.preload':
            if current is None:raise ValueError('Preload outside constructor')
            current['relative'].append(event['stack'][0])
        elif event['label']=='scr.allocate.return':
            if current is None:raise ValueError('Unmatched constructor return')
            expected.append(current);current=None
    if current is not None or len(expected)!=2:raise ValueError('Incomplete native constructors')
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        for native in expected:
            actual=page.evaluate('''m=>{const fresh=new ResourceStore(ORIGINAL),loads=[],load=fresh.shape.bind(fresh);fresh.shape=(archive,id)=>{loads.push(id);return load(archive,id);};const animation=new Animation(fresh,m.archive,m.id,m.palette);return {relative:animation.resources.map(r=>r.relative),absolute:animation.resources.map(r=>r.id),loads,frames:animation.frameUpdates,immutable:Object.isFrozen(animation.resources)&&animation.resources.every(Object.isFrozen)};}''',native)
            report['checks'].append(dict(name=f"native {native['archive']}:{native['id']} complete preload order",passed=actual['relative']==native['relative'] and actual['absolute']==actual['loads'] and actual['frames']==0 and actual['immutable'],expected=native,actual=actual))
        report['checks'].extend(page.evaluate('''()=>{const data={scripts:{'a:10':{bounds:[0,0,1,1],code:[[0xc0,[3,0,5,0]],[1,[1,0,0,0]],[0xc1,[1,0,4,0]],[0xc2,[0,0,99,0]],[0,[]],[0xc0,[99,0,99,0]]]}},palettes:{'a:10':{first:100,count:5,colors:[[0,0,0]]}}};const s=new ResourceStore(data),plan=s.animationResources('a',10,10);let invalid=false;data.scripts['a:11']={code:[[0xc0,[6,0,6,0]],[0,[]]]};try{s.animationResources('a',11,10);}catch(e){invalid=e.message.includes('outside palette');}return [{name:'deduplicates complete ranges after first display and sorts ascending',passed:JSON.stringify(plan.map(r=>r.relative))==='[1,2,3,4,5]'},{name:'maps palette-relative indices to resource IDs',passed:JSON.stringify(plan.map(r=>r.id))==='[100,101,102,103,104]'},{name:'zero shape and data after terminator do not load',passed:plan.length===5},{name:'rejects range exceeding palette',passed:invalid},{name:'reuses immutable resource plan',passed:s.animationResources('a',10,10)===plan&&Object.isFrozen(plan)}];}'''))
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Resource preload order and availability; CPU time, resource lifetime and scanout integration remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True)
    p.add_argument('--trace',type=Path,default=ROOT/'testing/output/treehouse/nature-resource-trace-b/trace.json')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.html,a.trace,a.output) else 1)
