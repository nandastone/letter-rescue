"""Replay near-heap allocation/free requests from one explicit RAM fixture."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]

def parse(data,ss):
    start,search,end=struct.unpack_from('<3H',data,16*ss+0x1776)
    blocks=[];address=start
    while address<=end:
        header=struct.unpack_from('<H',data,ss*16+address)[0]
        blocks.append(dict(address=address,size=header&0xfffe,free=bool(header&1)))
        if address==end:break
        address+=2+(header&0xfffe)
    if address!=end:raise ValueError('Near heap chain does not reach its terminator')
    return dict(blocks=blocks,start=start,search=search,end=end)

def verify(trace_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text())
    fixtures=trace['heap'];states=[]
    if len(fixtures)!=104:raise ValueError('Expected all 52 preparation calls in this route')
    for f in fixtures:
        data=(trace_path.parent/f['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Changed RAM fixture')
        states.append(parse(data,f['ss']))
    beginning=fixtures[0]['milliseconds'];ending=fixtures[-1]['milliseconds']
    stream=[dict(type='checkpoint',milliseconds=f['milliseconds'],index=i,state=states[i]) for i,f in enumerate(fixtures)]
    stream.extend(dict(e,type='event') for e in trace['events'] if beginning<=e['milliseconds']<=ending and (e['label'].startswith('memory.near.') or e['label']=='memory.handle.allocate'))
    stream.sort(key=lambda e:e['milliseconds'])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/near-heap.js'))
        report=page.evaluate('''a=>{
          const h=new OriginalNearHeap(a.initial),checks=[],returns=[];
          let allocations=0,frees=0;
          for(const event of a.stream){
            if(event.type==='checkpoint'){
              const actual=h.snapshot();checks.push({index:event.index,passed:JSON.stringify(actual)===JSON.stringify(event.state),expected:event.state,actual});
            }else if(event.label==='memory.handle.allocate'){h.resetSearch();
            }else if(event.label==='memory.near.allocate'){
              returns.push(h.allocate(event.stack[2]));allocations++;
            }else if(event.label==='memory.near.allocate.return'){
              const expected=returns.pop();if(expected!==event.ax)throw new Error(`Near allocation pointer: expected ${expected}, observed ${event.ax}`);
            }else if(event.label==='memory.near.free'){h.free(event.stack[2]);frees++;}
          }
          if(returns.length)throw new Error('Unclosed near allocation call');
          return {allocations,frees,checks};
        }''',dict(initial=states[0],stream=stream));browser.close()
    report.update(passed=report['allocations']==237 and report['frees']==206 and all(c['passed'] for c in report['checks']),model_sha256=hashlib.sha256((ROOT/'treehouse-demo/near-heap.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),scope='Continuous near-heap structure and returned pointers from one explicit initial RAM fixture and observed request sizes/frees. Resource operation requests must still be generated independently by the runtime.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'checks':[{'index':c['index'],'passed':c['passed']} for c in report['checks'] if not c['passed']],'matching_checkpoints':sum(c['passed'] for c in report['checks'])},indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.output) else 1)
