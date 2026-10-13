"""Verify recovered heap operations against isolated original RAM fixtures.

RAM is an explicit offline initial-state fixture, never browser game input.
"""
from pathlib import Path
import argparse, hashlib, json, struct, sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]

def parse(data,ss):
    def word(p): return struct.unpack_from('<H',data,p)[0]
    def far(p): return word(p)+16*word(p+2)
    control=far(ss*16+0x203a)
    if word(control+0xc) or not word(control+0x10):
        raise ValueError('Fixture needs unsupported arena growth')
    address=far(control); blocks=[]; handles=[]
    for _ in range(10000):
        header=word(address);size=(header&7)*2+word(address+2)*16
        flags=header&0xffc0;padding=(header>>3)&7
        block=dict(address=address,size=size,flags=flags,padding=padding)
        if flags==0xc000:
            handle=word(address+4); hp=ss*16+handle
            if 16*word(hp+2)+(word(hp)&15)!=address:raise ValueError('Broken handle backlink')
            block.update(handle=handle,payload=hashlib.sha256(data[address+6:address+size-padding]).hexdigest())
            handles.append(dict(id=handle,state=word(hp),segment=word(hp+2)))
        blocks.append(block)
        if flags==0x4000:break
        if size<6 or address+size+6>len(data):raise ValueError('Invalid heap chain')
        address+=size
    else:raise ValueError('Unterminated heap')
    return dict(blocks=blocks,handles=sorted(handles,key=lambda h:h['id']),search=far(control+4))

def verify(trace_path,output,expected_calls=2,state_only=False):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text()); fixtures=trace['heap']
    if not fixtures or len(fixtures)!=expected_calls*2:raise ValueError('Incomplete heap fixtures')
    states=[]
    for i,f in enumerate(fixtures):
        if f['phase']!=i%2:raise ValueError('Unpaired heap fixtures')
        data=(trace_path.parent/f['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Changed RAM fixture')
        states.append(parse(data,f['ss']))
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/heap.js'))
        work=None if state_only else trace.get('work')
        if work:
            if work['routine']!='resident:6B06':raise ValueError('Expected heap instruction work')
            for filename in ['graphics-work.js','heap-instructions.js','memory-copy-work.js','heap-work.js']:
                page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        for i in range(0,len(states),2):
            if fixtures[i]['requested']!=fixtures[i+1]['requested'] or fixtures[i]['ss']!=fixtures[i+1]['ss']:raise ValueError('Inconsistent heap call fixture')
            model=page.evaluate('a=>{const h=new OriginalHeap({...a.state,closedArena:true});const available=h.prepare(a.requested);return {state:h.snapshot(),available,moves:h.moves,scans:h.scans,merges:h.merges};}',dict(state=states[i],requested=fixtures[i]['requested']))
            expected=states[i+1];actual=model.pop('state');differences={}
            for key in expected:
                if actual[key]!=expected[key]:differences[key]=dict(expected=expected[key],actual=actual[key])
            if work:
                selected=[c for c in work['calls'] if c['begin']==fixtures[i]['milliseconds'] and c['end']==fixtures[i+1]['milliseconds']]
                if len(selected)!=1:raise ValueError('No unique work call for heap fixture')
                call=selected[0];base=trace['location']['main_base']+0xd510
                observed={str(c['address']-base):c['entries'] for c in work['counts'] if c['call']==call['ordinal']}
                slices=[s for s in work['slices'] if s['call']==call['ordinal']]
                counted=page.evaluate('a=>{const h=new OriginalHeapWork({...a.state,closedArena:true});h.prepare(a.requested);return {state:h.snapshot(),work:h.work()};}',dict(state=states[i],requested=fixtures[i]['requested']))
                if counted['state']!=expected:differences['work_model_state']=dict(expected=expected,actual=counted['state'])
                counts=counted['work'];cursor=0
                for repeat in counts['repeats']:
                    remaining=repeat['iterations'];budgets=[]
                    while remaining or not budgets:
                        s=slices[cursor];cursor+=1
                        if s['address']-base!=repeat['address'] or s['remaining']!=remaining:raise ValueError('Invalid REP continuation fixture')
                        budgets.append(s['budget']);remaining-=min(remaining,max(1,s['budget']))
                    dispatch=page.evaluate('a=>OriginalGraphicsWork.repeatString(a.iterations,a.budgets)',dict(iterations=repeat['iterations'],budgets=budgets))
                    extra=dispatch['dispatches']-1
                    counts['entries'][str(repeat['address'])]+=extra
                    counts['instructions']+=extra;counts['cycles']+=extra
                if cursor!=len(slices):raise ValueError('Unused REP slices')
                mismatch={a:dict(expected=counts['entries'].get(a,0),actual=observed.get(a,0)) for a in counts['entries'].keys()|observed.keys() if counts['entries'].get(a,0)!=observed.get(a,0)}
                if mismatch:differences['instructions']=mismatch
                model['work']=counts;model['rep_slice_fixtures']=slices
            results.append(dict(pair=i//2,requested=fixtures[i]['requested'],observed_ms=fixtures[i+1]['milliseconds']-fixtures[i]['milliseconds'],**model,differences=differences,passed=not differences))
        checks=page.evaluate('''()=>{
          const block=(address,size,flags=0,padding=0)=>({address,size,flags,padding});
          const make=(blocks,handles=[])=>new OriginalHeap({blocks,handles,search:blocks[0].address,closedArena:true});
          const a=make([block(16,20),block(36,6,0x4000)]);a.reserve(a.at(16),11,true);
          const b=make([block(16,40,0,1),block(56,6,0x4000)]);b.reserve(b.at(16),11,true);
          const c=make([block(16,8,0,1),block(24,10),block(34,6,0x4000)]);c.coalesce(c.at(16));
          const d=make([{...block(16,8,0xc000),handle:4,payload:'kept'},block(24,6,0x4000)],[{id:4,state:0x8000,segment:1}]);const locked=d.relocate(d.at(16));
          let growth=false;try{new OriginalHeap({blocks:[block(16,6,0x4000)],handles:[],search:16});}catch(e){growth=true;}
          return [
            {name:'consume remainder smaller than six-byte header',passed:a.blocks.length===2&&a.blocks[0].padding===3},
            {name:'tail split clears free header padding',passed:b.blocks[0].size===22&&b.blocks[0].padding===0&&b.blocks[1].padding===1},
            {name:'coalescing preserves first free padding field',passed:c.blocks.length===2&&c.blocks[0].size===18&&c.blocks[0].padding===1},
            {name:'locked handle is not relocated',passed:!locked&&d.moves.length===0&&d.blocks[0].payload==='kept'},
            {name:'unreconstructed arena growth is rejected',passed:growth}
          ];
        }''')
        browser.close()
    files=['heap.js']+(['heap-instructions.js','memory-copy-work.js','heap-work.js','graphics-work.js'] if work else [])
    report=dict(model_sha256=hashlib.sha256((ROOT/'treehouse-demo/heap.js').read_bytes()).hexdigest(),model_files={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in files},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),calls=results,checks=checks,passed=all(r['passed'] for r in results) and all(c['passed'] for c in checks),scope='Heap state, movable payload preservation, and optional instruction work for recorded closed-arena preparation calls. Initial RAM and REP residual budgets are explicit offline fixtures; runtime lifetimes, growth/eviction and full timing remain separate work.')
    report['instruction_work_checked']=bool(work)
    report['state_only_requested']=state_only
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[{k:v for k,v in r.items() if k not in ['moves','work','rep_slice_fixtures','differences']}|{'differences':list(r['differences'])} for r in results]},indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-calls',type=int,default=2)
    p.add_argument('--state-only',action='store_true',help='Compare complete heap/payload state without the optional CPU instruction-work model.')
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.output,a.expected_calls,a.state_only) else 1)
