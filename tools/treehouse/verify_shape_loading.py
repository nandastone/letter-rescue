"""Validate VGA allocation layouts and focused source-cache ownership behavior.

Inventory coverage is not native execution coverage. Native state comparisons
are reported separately by verify_memory_lifetimes.py --all-shapes.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,struct,sys,zipfile
from playwright.sync_api import sync_playwright
from resources import parse_archive
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]

def verify(output,without_work=False):
    output.mkdir(parents=True,exist_ok=False)
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source archive')
    shapes=[]
    with zipfile.ZipFile(source) as archive:
        for name in ['th','th64','boy','girl','modules','digisnd','voices']:
            data=archive.read(f'TheTreeh/{name}.dat')
            for r in parse_archive(data):
                if r['tag']=='SHAP':
                    payload=data[r['payload_offset']:r['payload_offset']+r['size']]
                    height,width,flags=struct.unpack_from('<3H',payload)
                    shapes.append(dict(key=f'{name}:{r["id"]}',header=list(payload[:6]),width=width,height=height,flags=flags,size=len(payload)))
    if len(shapes)!=2337:raise ValueError('Incomplete original shape inventory')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        filenames=['heap.js','near-heap.js','memory.js']+([] if without_work else ['memory-work.js','resource-work.js'])+['resource-loading.js','shape-loading.js']
        for filename in filenames:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        inventory=page.evaluate('a=>a.map(s=>{const bytes=new Uint8Array(s.size);bytes.set(s.header);const plan=OriginalShapeLoading.plan(bytes);return {key:s.key,plan,passed:plan.width===s.width&&plan.height===s.height&&plan.convertedBytes===s.width*s.height+6&&plan.sourceBytes===s.size};})',shapes)
        checks=page.evaluate('''withoutWork=>{
          const base=0x30000,palette=base+128,free=palette+268,end=free+65536;
          const m=new OriginalMemory({heap:{search:free,blocks:[{address:base,size:128,flags:0xc000,padding:0,handle:102},{address:palette,size:268,flags:0xc000,padding:0,handle:108},{address:free,size:65536,flags:0,padding:0},{address:end,size:6,flags:0x4000,padding:0}],handles:[{id:102,state:0x11f0,segment:base>>>4},{id:108,state:0x11f0,segment:palette>>>4}]},near:{start:100,search:112,end:4208,blocks:[{address:100,size:4,free:false},{address:106,size:4,free:false},{address:112,size:4094,free:true},{address:4208,size:65534,free:false}]}});
          const loader=new OriginalShapeLoading(m,102,{observeWork:!withoutWork}),shape={key:'synthetic:1',payload:[2,0,3,0,0,0xb0,0,0,0,0],paletteHandle:108,directoryFlags:0x40};
          const first=loader.load(shape),source=loader.sources.get(shape.key),firstOps=loader.operations.slice();
          const begin=loader.operations.length,second=loader.load(shape),warmOps=loader.operations.slice(begin);
          m.discard(source);const before=loader.operations.length,third=loader.load(shape),reloadOps=loader.operations.slice(before);
          const reloadSource=loader.sources.get(shape.key);
          m.freeHandle(first);m.freeHandle(second);m.freeHandle(third);
          const releasedIndependently=!m.heap.handles.has(first)&&!m.heap.handles.has(second)&&!m.heap.handles.has(third)&&m.address(source)!==0;
          const mono=OriginalShapeLoading.plan([2,0,9,0,0,0]),eight=OriginalShapeLoading.plan([1,0,3,0,0,0xf3]);
          const promoted=loader.source('synthetic:promoted',[1,2],0xc0),promotedLocked=!!(m.handle(promoted).state&0x8000);
          m.unlock(promoted);m.retain(promoted);m.discard(promoted);
          let promotions=0;const promote=m.promote.bind(m);m.promote=id=>{promotions++;return promote(id);};
          loader.source('synthetic:promoted',[1,2],0xc0);
          const reloadFlags=m.handle(promoted).state&0xe000;
          let rejected=false;try{OriginalShapeLoading.plan([1,0,3,0,0,0xb5]);}catch(e){rejected=true;}
          return [
            {name:'cold load allocates source and converted image',passed:firstOps.filter(o=>o.kind==='handle.allocate').map(o=>o.bytes).join(',')==='10,12'&&firstOps.filter(o=>o.kind==='resource.read').length===1},
            {name:'warm load allocates a distinct converted image without rereading source',passed:second!==first&&warmOps.length===2&&warmOps[0].kind==='handle.allocate'&&warmOps[1].kind==='resize'},
            {name:'discarded source reload preserves its handle slot',passed:reloadSource===source&&reloadOps[0].kind==='handle.reallocate'&&reloadOps[1].kind==='resource.read'},
            {name:'converted images release independently of cached source',passed:releasedIndependently},
            {name:'palette and catalog locks restore while cache remains discardable',passed:(m.handle(102).state&0xe000)===0&&(m.handle(108).state&0xe000)===0&&(m.handle(source).state&0xe000)===0x4000},
            {name:'one-bit packed stride and eight-bit LZ storage follow their headers',passed:mono.stride===2&&mono.convertedBytes===24&&mono.scratchBytes===0&&eight.stride===3&&eight.convertedBytes===9&&eight.scratchBytes===1024},
            {name:'newly promoted source remains locked',passed:promotedLocked},
            {name:'reload preserves current flags without repeating directory actions',passed:promotions===0&&reloadFlags===0},
            {name:'unknown compression is rejected',passed:rejected}
          ];
        }''',without_work);browser.close()
    report=dict(source_sha256=SOURCE_SHA,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in ['heap.js','near-heap.js','memory.js','memory-work.js','resource-work.js','resource-loading.js','shape-loading.js']},inventory=inventory,formats=dict(Counter(hex(s['flags']) for s in shapes)),checks=checks,passed=all(i['passed'] for i in inventory) and all(c['passed'] for c in checks),scope='All 2337 original shape headers are compatible with the recovered VGA memory layout; nine synthetic ownership/layout checks. This is not native execution coverage for all assets.')
    report['without_instruction_work']=without_work
    report['loaded_modules']=filenames
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'inventory':[i for i in inventory if not i['passed']],'matching_layouts':sum(i['passed'] for i in inventory)},indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--without-work',action='store_true');a=p.parse_args();sys.exit(0 if verify(a.output,a.without_work) else 1)
