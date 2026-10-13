"""Compare source-driven animation preparation with complete native boundaries.

Initial RAM is an explicit offline fixture per call. Script bytes and archive
resources drive all allocations; native allocation events are never inputs.
"""
from pathlib import Path
import argparse, json, struct, zipfile
from playwright.sync_api import sync_playwright
from build_demo import ROOT, SOURCE_SHA
from executable import unpack, disassemble_script
from memory_catalog import read_catalogs
from resources import parse_archive
from verify_heap import parse as parse_heap
from verify_near_heap import parse as parse_near
from verify_resource_growth import DATA, digest


def state(raw,ss):
    heap=parse_heap(raw,ss)
    for block in heap['blocks']:block.pop('payload',None)
    return dict(heap=heap,near=parse_near(raw,ss))


def verify(capture,output):
    output.mkdir(parents=True,exist_ok=False)
    run=json.loads((capture/'run.json').read_text())
    assert run['passed'] and run['stage']=='animation' and run['fixed_clock']
    source=DATA/'source/The_Treehouse_1991.zip';assert digest(source)==SOURCE_SHA
    with zipfile.ZipFile(source) as z:
        image,_=unpack(z.read('TheTreeh/treehse.exe'))
        archives={Path(n).stem.lower():z.read(n) for n in z.namelist() if n.lower().endswith('.dat')}
    scripts=[]
    for name in ['th','boy','girl','modules']:
        data=archives[name]
        for resource in parse_archive(data):
            if resource['tag']=='SCR':
                payload=data[resource['payload_offset']:resource['payload_offset']+resource['size']]
                scripts.append((f"{name}:{resource['id']}",payload))
    entries=[e for e in run['events'] if e['label']=='animation.create']
    returns=[e for e in run['events'] if e['label']=='animation.create.return']
    assert len(entries)==len(returns)==6 and len(run['heap'])==12
    cases=[];resources={}
    for i,(entry,end) in enumerate(zip(entries,returns)):
        fixtures=run['heap'][2*i:2*i+2];raw=[]
        for f in fixtures:
            path=capture/f['path'];assert digest(path)==f['sha256'];raw.append(path.read_bytes())
        assert fixtures[0]['milliseconds']==entry['milliseconds'] and fixtures[1]['milliseconds']==end['milliseconds']
        ss=entry['ss'];word=lambda p:struct.unpack_from('<H',raw[0],p)[0]
        save,last,first,palette,offset,segment=entry['stack'][2:8]
        initial=state(raw[0],ss);expected=state(raw[1],ss)
        catalogs=read_catalogs(raw[0],ss)
        ids={h['id'] for h in initial['heap']['handles']}
        for catalog in catalogs:
            for r in catalog['records']:
                if r['handle'] and r['handle'] not in ids:
                    h=r['handle'];initial['heap']['handles'].append(dict(id=h,state=word(16*ss+h),segment=word(16*ss+h+2)));ids.add(h)
                if r['tag']=='SHAP':
                    key=f"{catalog['archive']}:{r['id']}"
                    r['resourceKey']=key
                    if key not in resources:resources[key]=list(archives[catalog['archive']][r['offset']+1:r['offset']+1+r['length']])
        p=16*segment+offset;block=next(b for b in initial['heap']['blocks'] if b['address']==p-6)
        active_script=raw[0][p:p+block['size']-6-block['padding']]
        matches=[(name,payload) for name,payload in scripts if payload[8:]==active_script[8:]]
        assert matches,'Active animation code is not present in the pinned archives'
        script=disassemble_script(matches[0][1],image)
        # The wrapper may relocate the rectangle before calling the constructor.
        # Instructions always come from the original archive, not captured RAM.
        bounds=list(struct.unpack_from('<4h',active_script))
        palette_address=16*word(16*ss+palette+2)+(word(16*ss+palette)&15)+6
        first_shape=word(palette_address)
        # C596 can acquire a palette conversion slot when not prepared. This
        # capture exercises the wrapper's already-converted SHPL resources.
        assert word(palette_address+4)!=0 and word(16*ss+0x5778)==0
        obj=struct.unpack_from('<H',raw[1],16*ss+end['bp']-8)[0]
        owned=[dict(relative=first+j,handle=struct.unpack_from('<H',raw[1],16*ss+obj+0x29c+2*j)[0]) for j in range(last-first+1)]
        cases.append(dict(initial=initial,expected=expected,catalogs=catalogs,
            scriptIdentities=[name for name,payload in matches],
            arguments=dict(script=dict(bounds=bounds,code=[[op['opcode'],list(bytes.fromhex(op['operand_hex']))] for op in script['instructions']]),
                           first=first,last=last,paletteHandle=palette,saveBackground=bool(save)),
            firstShape=first_shape,expectedObject=obj,expectedImages=[v for v in owned if v['handle']]))
    modules=['heap.js','near-heap.js','memory.js','resource-loading.js','shape-loading.js','animation-memory.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        results=page.evaluate('''({cases,resources})=>cases.map(c=>{
          const m=new OriginalMemory(c.initial),loaders=new Map(),loads=[];
          for(const catalog of c.catalogs){
            const loader=new OriginalShapeLoading(m,catalog.handle,{observeWork:false});
            loader.sources=new Map(catalog.records.filter(r=>r.tag==='SHAP'&&r.handle).map(r=>['SHAP:'+r.id,r.handle]));
            loaders.set(catalog.handle,loader);
          }
          const loadShape=relative=>{
            const id=c.firstShape+relative-1;
            const catalog=c.catalogs.find(c=>c.records.some(r=>r.tag==='SHAP'&&r.id===id));
            if(!catalog)throw new Error('Missing shape '+id);
            const entry=catalog.records.find(r=>r.tag==='SHAP'&&r.id===id),loader=loaders.get(catalog.handle);
            const handle=loader.load({key:'SHAP:'+id,payload:resources[entry.resourceKey],directoryFlags:entry.flags,paletteHandle:c.arguments.paletteHandle});
            loads.push({relative,id,handle});return handle;
          };
          try{
            const scene=OriginalAnimationMemory.prepare(m,{...c.arguments,loadShape});
            const heap=m.heap.snapshot(),active=new Set(heap.blocks.filter(b=>b.flags===0xc000).map(b=>b.handle));
            heap.blocks=heap.blocks.map(({payload,...b})=>b);heap.handles=heap.handles.filter(h=>active.has(h.id));
            return {object:scene.object,images:Array.from(scene.images,([relative,handle])=>({relative,handle})),loads,state:{heap,near:m.near.snapshot()},instructionObserverLoaded:typeof OriginalResourceWork!=='undefined'};
          }catch(error){return {error:String(error),loads};}
        })''',dict(cases=cases,resources=resources))
        browser.close()
    checks=[]
    for i,(c,r) in enumerate(zip(cases,results)):
        for field,expected in [('object',c['expectedObject']),('images',c['expectedImages']),('state',c['expected']),('instructionObserverLoaded',False)]:
            checks.append(dict(name=f'animation {i} {field}',passed=r.get(field)==expected,expected=expected,actual=r.get(field)))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,results=results,
        models={n:digest(ROOT/'treehouse-demo'/n) for n in modules},capture_sha256=digest(capture/'run.json'),source_sha256=SOURCE_SHA,
        script_identities=[c['scriptIdentities'] for c in cases],
        full_game_parity=False,playable_changed=False,
        scope='Six complete native animation constructors from independent offline initial states; parsed scripts generate object, ordered image conversion, surface and backup ownership. Complete near/far heap and live handle state, returned object and image handles compared. No allocation trace or instruction-work model drives construction. Palette conversion, generated startup-to-scene continuity, playback writes, disposal and live integration are not established.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),shapes=sum(len(r['loads']) for r in results),failed=[c['name'] for c in checks if not c['passed']],errors=[r['error'] for r in results if 'error' in r]),indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,default=DATA/'resource-startup-animation-a')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if verify(args.capture,args.output) else 1)
