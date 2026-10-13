"""Isolate scanout from CPU timing using original clock fixtures and clone pixels.

This does not certify gameplay timing: framebuffer commit times are supplied by
the original trace. It verifies the reusable JS presenter against every callback
in one complete question-animation window, including mixed old/new displays.
"""
from pathlib import Path
import argparse, base64, hashlib, json, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(html,trace_folder,generated,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads((trace_folder/'trace.json').read_text())
    report=json.loads((generated/'report.json').read_text())
    digest=hashlib.sha256(html.read_bytes()).hexdigest()
    if report['demo_sha256']!=digest or not report['passed']:raise ValueError('Generated frame provenance differs')
    states=report['sequences']['robot-turn']['states'];targets={s['actorFrame']:s for s in states if s['actorFrame'] is not None}
    commits=[];ends=[e for e in trace['events'] if e['label']=='scr.copy.end'][1:]
    if len(ends)!=24 or sorted(targets)!=list(range(1,24)):raise ValueError('Question display count differs')
    for index,event in enumerate(ends,1):
        state=targets[min(index,23)];im=Image.open(generated/state['image']).convert('RGBA')
        if hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()!=state['hash']:raise ValueError('Corrupt generated frame')
        commits.append(dict(milliseconds=event['milliseconds'],rgba=base64.b64encode(im.tobytes()).decode()))
    rows={r['run']:r for r in map(json.loads,(trace_folder/'frames.jsonl').read_text().splitlines())}
    boundaries=[b for b in trace['boundaries'] if 2115<=b['run']<=2420]
    meta=boundaries[0]['video_timing'];parts=meta[9];part_ms=meta[8]
    if parts!=4 or meta[10]!=50 or meta[1]!=0:raise ValueError('Reference is not the researched four-part mode')
    frames=[dict(run=b['run'],start=b['video_timing'][5],callback=b['milliseconds']) for b in boundaries]
    source=ROOT/'treehouse-demo/presentation.js';errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:errors.append(str(e)));page.goto(html.resolve().as_uri());page.add_script_tag(path=str(source))
        results=page.evaluate('''async m=>{
          const presenter=new OriginalScanout({partMilliseconds:m.part_ms}),out=[];
          const commits=m.commits.map(c=>({...c,pixels:new Uint32Array(Uint8Array.from(atob(c.rgba),c=>c.charCodeAt(0)).buffer)}));
          for(const c of commits)presenter.commit(c.milliseconds,c.pixels);
          const hash=async pixels=>{const rgba=new Uint8Array(pixels.buffer,pixels.byteOffset,pixels.byteLength),rgb=new Uint8Array(192000);for(let i=0;i<64000;i++)rgb.set(rgba.subarray(i*4,i*4+3),i*3);return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');};
          for(const f of m.frames){const pixels=presenter.present(f.start),atomic=commits.findLast(c=>c.milliseconds<=f.callback).pixels;out.push({run:f.run,hash:await hash(pixels),atomic_hash:await hash(atomic)});}
          const probe=new OriginalScanout({width:1,height:4,parts:4,partMilliseconds:1}),a=new Uint32Array([1,1,1,1]),b=new Uint32Array([2,2,2,2]);probe.commit(0,a);probe.commit(2.5,b);a.fill(9);const mixed=JSON.stringify([...probe.present(0)])==='[1,1,2,2]';let reversed=false,late=false,infinite=false;try{probe.present(-1);}catch(e){reversed=true;}try{probe.commit(3,b);}catch(e){late=true;}try{new OriginalScanout({partMilliseconds:Infinity});}catch(e){infinite=true;}
          const later=JSON.stringify([...probe.present(5)])==='[2,2,2,2]'&&probe.commits.length===1;
          return {frames:out,checks:[{name:'commit snapshots survive caller mutation and mix at exact part boundaries',passed:mixed},{name:'backward presentation clocks are rejected',passed:reversed},{name:'writes to an already presented interval are rejected',passed:late},{name:'invalid clock periods are rejected',passed:infinite},{name:'later frames retain the latest commit and release obsolete history',passed:later}]};
        }''',dict(part_ms=part_ms,commits=commits,frames=frames));browser.close()
    comparisons=[dict(**r,exact=r['hash']==rows[r['run']]['rgb_sha256'],atomic_exact=r['atomic_hash']==rows[r['run']]['rgb_sha256']) for r in results['frames']]
    result=dict(demo_sha256=digest,presenter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),trace=str(trace_folder),generated=str(generated),scope=__doc__,window=[2115,2420],comparisons=comparisons,checks=results['checks'],errors=errors,
        exact=sum(c['exact'] for c in comparisons),atomic_exact=sum(c['atomic_exact'] for c in comparisons),total=len(comparisons),
        passed=not errors and len(comparisons)==306 and all(c['exact'] for c in comparisons) and all(c['passed'] for c in results['checks']))
    (output/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2));return result['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.html,a.trace,a.generated,a.output) else 1)
