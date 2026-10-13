"""Verify ED3E work generated with continuous handle ownership."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from verify_memory_lifetimes import shape_calls
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False);memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted memory evidence')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated model')
    if any(scene[k]!=trace[k] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    if work['routine']!='resident:ED3E' or len(work['calls'])!=98 or len(memory['handleResizeChecks'])!=83:raise ValueError('Incomplete handle resize coverage')
    counts={c['ordinal']:{} for c in work['calls']};base=trace['location']['main_base']+0xd510;returns={r['call']:r for r in work['results']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    initial=(scene_path.parent/scene['heap'][0]['path']).read_bytes();shapes,_=shape_calls(scene,initial);sounds,_=sound_calls(scene,initial)
    phases={p['milliseconds']:p for p in shapes+sounds};used=set();results=[]
    for generated in memory['handleResizeChecks']:
        phase=phases[generated['contextTime']]
        candidates=[c for c in work['calls'] if phase['milliseconds']<=c['begin'] and c['end']<=phase['end'] and c['ordinal'] not in used]
        if not candidates:raise ValueError('No corresponding native handle resize')
        call=candidates[0];used.add(call['ordinal'])
        actual=counts[call['ordinal']];model=generated['work'];expected=model['entries'];s=call['stack']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=generated['handle']==s[4] and generated['bytes']==s[2]+65536*s[3];return_equal=model['ax']==returns[call['ordinal']]['ax']
        results.append(dict(ordinal=call['ordinal'],handle=generated['handle'],bytes=generated['bytes'],instructions=model['instructions'],differences=differences,input_equal=input_equal,return_equal=return_equal,passed=generated['passed'] and input_equal and return_equal and not differences))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in ['heap.js','near-heap.js','memory.js','handle-resize-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        checks=page.evaluate('''()=>{
          const make=()=>new OriginalMemory({heap:{search:16,blocks:[{address:16,size:16,flags:0xc000,padding:0,handle:102,payload:'kept'},{address:32,size:8,flags:0x8000,padding:0},{address:40,size:128,flags:0,padding:0},{address:168,size:6,flags:0x4000,padding:0}],handles:[{id:102,state:0x51f0,segment:1}]},near:{start:100,search:106,end:208,blocks:[{address:100,size:4,free:false},{address:106,size:100,free:true},{address:208,size:65534,free:false}]}});
          const a=make(),same=OriginalHandleResizeWork.resize(a,102,10);
          const b=make(),moved=OriginalHandleResizeWork.resize(b,102,30);
          const c=make();c.lock(102);const locked=OriginalHandleResizeWork.resize(c,102,30);
          const d=make();d.discard(102);const gone=OriginalHandleResizeWork.resize(d,102,30);
          const e=make(),nullHandle=OriginalHandleResizeWork.resize(e,0,30);
          return [{name:'in-place result preserves handle and data',passed:same.action==='in-place'&&same.ax===0&&a.heap.at(16).payload==='kept'},{name:'unlocked relocation preserves old data and copies old length',passed:moved.action==='moved'&&moved.ax===0&&moved.copy.from===22&&moved.copy.to===46&&moved.copy.bytes===10&&b.heap.at(40).payload==='kept'},{name:'locked handle cannot move after failed growth',passed:locked.action==='locked'&&locked.ax===1&&c.address(102)===22},{name:'discarded handle uses reallocation branch',passed:gone.action==='reallocate'&&gone.ax===0&&d.address(102)===46},{name:'null handle reports failure',passed:nullHandle.action==='reallocate'&&nullHandle.ax===1}];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),calls=results,checks=checks,models=memory['models'],memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='83 native ED3E calls from 79 generated shape loads and two sound preparations, with generated input handles/lengths, intrinsic work and native status returns. Fifteen other calls remain outside generated wrapper coverage. Additional ownership branches have synthetic coverage. Callee costs and full scheduling remain separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
