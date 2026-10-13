"""Verify generated direct script-load work and independent allocation ownership."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(memory_path,scene_path,trace_path,output):
    output.mkdir(parents=True,exist_ok=False)
    memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text());trace=json.loads(trace_path.read_text());work=trace['work']
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Memory evidence does not match scene')
    if scene['events']!=trace['events'] or scene['boundaries']!=trace['boundaries'] or scene['actions']!=trace['actions']:raise ValueError('Observers describe different executions')
    for filename,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/filename).read_bytes()).hexdigest()!=digest:raise ValueError('Model changed since memory verification')
    generated=[s for s in memory['sceneChecks'] if s['kind']=='script-load']
    if len(memory['sceneChecks'])!=12 or len(memory['checks'])!=104 or len(generated)!=2 or not work or work['routine']!='resident:7688' or len(work['calls'])!=2:raise ValueError('Incomplete generated direct-load coverage')
    base=trace['location']['main_base']+0xd510;results=[]
    for model,call in zip(generated,work['calls']):
        if model['key']!=f"th:{call['stack'][2]}":raise ValueError('Different script input')
        actual={str(c['address']-base):c['entries'] for c in work['counts'] if c['call']==call['ordinal']};entries=model['work']['entries']
        differences={a:dict(expected=entries.get(a,0),actual=actual.get(a,0)) for a in entries.keys()|actual.keys() if entries.get(a,0)!=actual.get(a,0)}
        results.append(dict(key=model['key'],pointer=model['pointer'],instructions=model['work']['instructions'],differences=differences,passed=not differences))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for filename in ['heap.js','near-heap.js','memory.js','memory-work.js','resource-work.js','direct-loading.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        checks=page.evaluate('''()=>{
          const base=0x30000,source=base+128,free=source+32,end=free+65536;
          const m=new OriginalMemory({heap:{search:free,blocks:[{address:base,size:128,flags:0xc000,padding:0,handle:102},{address:source,size:32,flags:0xc000,padding:2,handle:108},{address:free,size:65536,flags:0,padding:0},{address:end,size:6,flags:0x4000,padding:0}],handles:[{id:102,state:0x11f0,segment:base>>>4},{id:108,state:0x51f0,segment:source>>>4}]},near:{start:100,search:112,end:4208,blocks:[{address:100,size:4,free:false},{address:106,size:4,free:false},{address:112,size:4094,free:true},{address:4208,size:65534,free:false}]}});
          const loader=new OriginalDirectLoading(m),saved=m.handle(102).state;
          const cached=loader.load({payload:[0],catalogHandle:102,cachedHandle:108});
          const copied=loader.operations.at(-1),cachedBlock=m.heap.at(cached-6),independent=cached!==m.address(108)&&cachedBlock.flags===0x8000;
          loader.release(cached);const released=m.heap.at(cached-6).flags===0&&m.address(108)!==0;
          const cold=loader.load({payload:[1,2,3],catalogHandle:102});
          const missed=OriginalResourceWork.direct({found:false}),failed=OriginalResourceWork.direct({allocated:false}),bad=OriginalResourceWork.direct({readError:true});
          return [
            {name:'cached load copies the actual source length into an independent raw block',passed:copied.kind==='resource.copy'&&copied.bytes===24&&independent},
            {name:'release frees only the independent copy',passed:released},
            {name:'uncached load reads without creating a cache handle',passed:loader.operations.at(-1).kind==='resource.read'&&loader.operations.at(-1).bytes===3&&m.heap.handles.size===2&&cold!==0},
            {name:'catalog flags restore after direct allocation',passed:m.handle(102).state===saved},
            {name:'missing lookup skips allocation',passed:missed.action==='none'&&!missed.entries[0x76bf]},
            {name:'failed allocation skips both copy and read',passed:failed.action==='none'&&!failed.entries[0x76d1]},
            {name:'permanent read error releases the temporary block',passed:bad.releaseAfterError&&bad.entries[0x7713]===1}
          ];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),calls=results,checks=checks,models=memory['models'],
        memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        scope='Both uncached SCR direct loads generate their allocations and intrinsic 7688 work from the continuous memory model. The same memory report covers both releases, 12 scene phases, 79 shape loads and 104 checkpoints. Cached copying and error branches have focused checks only. Pixel/payload writes, remaining native callees, startup and full clock integration remain separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.output) else 1)
