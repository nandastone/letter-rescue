"""Compare continuous resource memory state from one offline initial fixture."""
from pathlib import Path
import argparse, hashlib, json, struct, sys, zipfile
from playwright.sync_api import sync_playwright
from verify_heap import parse as parse_heap
from verify_near_heap import parse as parse_near
from resources import parse_archive
from build_demo import SOURCE_SHA
from memory_catalog import read_catalogs
from scene_memory_calls import scene_calls
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]

def shape_calls(trace,initial_data=None):
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source archive')
    with zipfile.ZipFile(source) as z:archives={name:z.read(f'TheTreeh/{name}.dat') for name in ['th','th64','boy','girl','modules']}
    records={f'{name}:{r["id"]}':r for name,data in archives.items() for r in parse_archive(data) if r['tag']=='SHAP'}
    catalogs=read_catalogs(initial_data,trace['heap'][0]['ss']) if initial_data is not None else []
    initial_sources={};resolved={}
    for catalog in catalogs:
        for entry in catalog['records']:
            if entry['tag']=='SHAP' and entry['id'] not in resolved:
                resolved[entry['id']]=(catalog,entry)
                if entry['handle']:initial_sources[f"{catalog['archive']}:{entry['id']}"]=entry['handle']
    calls=[];pending=None;group=None
    for e in trace['events']:
        label=e['label']
        if label=='wrapper.begin':group=e['stack'][10]
        elif label==('shape.load' if catalogs else 'scr.preload'):
            if pending:raise ValueError('Nested preload')
            pending=dict(type='shape',milliseconds=e['milliseconds'],paletteHandle=e['stack'][3] if catalogs else e['stack'][1],operations=[])
            if not catalogs:
                id=group+e['stack'][0];r=records[f'th:{id}'];data=archives['th']
                pending.update(key=f'th:{id}',payload=list(data[r['payload_offset']:r['payload_offset']+r['size']]),directoryFlags=int(r['flags_hex'][:2],16))
        elif label==('shape.load.return' if catalogs else 'scr.preload.return'):
            if not pending:raise ValueError('Unmatched preload return')
            pending.update(end=e['milliseconds'],expectedHandle=e['ax'])
            if not catalogs or trace['heap'][0]['milliseconds']<=pending['milliseconds'] and pending['end']<=trace['heap'][-1]['milliseconds']:calls.append(pending)
            pending=None
        elif pending:
            if catalogs and label=='resource.handle' and e['stack'][3:5]==[16720,21320]:
                id=e['stack'][2];catalog,entry=resolved[id]
                key=f"{catalog['archive']}:{id}";r=records[key];data=archives[catalog['archive']]
                if entry['length']!=r['size'] or entry['offset']!=r['checksum_offset']:raise ValueError('Loaded catalog differs from pinned DAT')
                pending.update(key=key,payload=list(data[r['payload_offset']:r['payload_offset']+r['size']]),directoryFlags=entry['flags'])
            if label=='memory.catalog.pin.outer':pending['catalogHandle']=e['bp']
            if label=='memory.handle.allocate':pending['operations'].append(dict(kind='handle.allocate',bytes=e['stack'][2]+65536*e['stack'][3]))
            elif label=='memory.reallocate':pending['operations'].append(dict(kind='handle.reallocate',bytes=e['stack'][2]+65536*e['stack'][3]))
            elif label=='resource.read':pending['operations'].append(dict(kind='resource.read',bytes=e['dx']+65536*e['cx']))
            elif label=='memory.near.allocate' and e['stack'][2]!=4:pending['operations'].append(dict(kind='near.allocate',bytes=e['stack'][2]))
            elif label=='memory.near.free':pending['operations'].append(dict(kind='near.free'))
            elif label=='memory.resize':pending['operations'].append(dict(kind='resize',bytes=e['ax']+65536*e['dx']))
    if pending or len(calls)!=(79 if catalogs else 30):raise ValueError('Incomplete shape preload coverage')
    return calls,initial_sources

def verify(trace_path,output,generated_shapes=False,all_shapes=False,generated_scenes=False,generated_scripts=False,generated_sounds=False,allocation_work=False,resize_work=False,handle_resize_work=False,near_work=False):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());fixtures=trace['heap'];states=[]
    if len(fixtures)!=104:raise ValueError('Expected all 52 preparation calls in this route')
    initial_data=(trace_path.parent/fixtures[0]['path']).read_bytes()
    near_start=parse_near(initial_data,fixtures[0]['ss'])['start'];static_ids=set()
    for event in trace['events']:
        if event['label'].startswith('memory.catalog.pin'):
            id=event['bx'] if event['label'].endswith('.find') else event['bp']
            if 0<id<near_start:static_ids.add(id)
    for f in fixtures:
        data=(trace_path.parent/f['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Changed RAM fixture')
        h=parse_heap(data,f['ss'])
        h['handles'].extend(dict(id=id,state=struct.unpack_from('<H',data,16*f['ss']+id)[0],segment=struct.unpack_from('<H',data,16*f['ss']+id+2)[0]) for id in sorted(static_ids))
        h['handles'].sort(key=lambda h:h['id'])
        for b in h['blocks']:b.pop('payload',None)
        states.append(dict(heap=h,near=parse_near(data,f['ss'])))
    beginning=fixtures[0]['milliseconds'];ending=fixtures[-1]['milliseconds']
    stream=[dict(type='checkpoint',milliseconds=f['milliseconds'],index=i,requested=f['requested'],state=states[i]) for i,f in enumerate(fixtures)]
    stream.extend(dict(e,type='event') for e in trace['events'] if beginning<=e['milliseconds']<=ending and e['label'].startswith('memory.'))
    shapes,initial_sources=shape_calls(trace,initial_data if all_shapes else None) if generated_shapes else ([],{})
    if shapes:
        if any(c['milliseconds']<beginning or c['end']>ending for c in shapes):raise ValueError('Preload outside memory fixture coverage')
        if any(e['type']=='checkpoint' and any(c['milliseconds']<=e['milliseconds']<=c['end'] for c in shapes) for e in stream):raise ValueError('Cannot skip native checkpoint inside generated operation')
        stream=[e for e in stream if not any(c['milliseconds']<=e['milliseconds']<=c['end'] for c in shapes)]
        stream.extend(shapes)
    sounds,initial_sound_sources=sound_calls(trace,initial_data) if generated_sounds else ([],{})
    sound_resources={}
    if generated_sounds and len(sounds)!=2399:raise ValueError('Incomplete generated sound route')
    for sound in sounds:
        inside=[e for e in stream if sound['milliseconds']<=e['milliseconds']<=sound['end']]
        if any(e['type']=='shape' for e in inside):raise ValueError('Overlapping sound and shape loads')
        sound['checkpoints']=[e for e in inside if e['type']=='checkpoint']
        sound_resources[sound['key']]=sound.pop('payload')
        stream=[e for e in stream if not sound['milliseconds']<=e['milliseconds']<=sound['end']]
        stream.append(sound)
    scenes=scene_calls(trace,shapes,read_catalogs(initial_data,fixtures[0]['ss']) if generated_scripts else False) if generated_scenes else []
    for scene in scenes:
        if scene['milliseconds']<beginning or scene['end']>ending:raise ValueError('Scene phase outside memory fixture coverage')
        inside=[e for e in stream if scene['milliseconds']<=e['milliseconds']<=scene['end']]
        if any(e['type'] in ('shape','sound') for e in inside):raise ValueError('Overlapping generated scene and resource operations')
        scene['checkpoints']=[e for e in inside if e['type']=='checkpoint']
        stream=[e for e in stream if not scene['milliseconds']<=e['milliseconds']<=scene['end']]
        stream.append(scene)
    stream.sort(key=lambda e:e['milliseconds'])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for filename in ['heap.js','near-heap.js','memory.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        if generated_shapes:
            page.add_script_tag(path=str(ROOT/'treehouse-demo/memory-work.js'))
            page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
            page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-loading.js'))
            page.add_script_tag(path=str(ROOT/'treehouse-demo/shape-loading.js'))
        if generated_scenes:page.add_script_tag(path=str(ROOT/'treehouse-demo/animation-memory.js'))
        if generated_scripts:page.add_script_tag(path=str(ROOT/'treehouse-demo/direct-loading.js'))
        if generated_sounds:page.add_script_tag(path=str(ROOT/'treehouse-demo/sound-loading.js'))
        if allocation_work:
            for filename in ['heap-instructions.js','memory-copy-work.js','heap-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        if resize_work:page.add_script_tag(path=str(ROOT/'treehouse-demo/memory-resize-work.js'))
        if handle_resize_work:page.add_script_tag(path=str(ROOT/'treehouse-demo/handle-resize-work.js'))
        if near_work:page.add_script_tag(path=str(ROOT/'treehouse-demo/near-heap-work.js'))
        report=page.evaluate('''a=>{
          const m=new OriginalMemory(a.initial),checks=[],far=[],near=[],owners=[],resizes=[];let allocations=0,frees=0;
          const loaders=new Map(),shapeChecks=[],scenes=new Map(),sceneChecks=[];
          const direct=a.generatedScripts?new OriginalDirectLoading(m):null,directPointers=new Map(),soundLoaders=new Map(),soundChecks=[];
          const snapshot=()=>{const heap=m.heap.snapshot();heap.blocks=heap.blocks.map(({payload,...b})=>b);const active=new Set([...heap.blocks.filter(b=>b.flags===0xc000).map(b=>b.handle),...a.staticIds]);heap.handles=heap.handles.filter(h=>active.has(h.id));return {heap,near:m.near.snapshot()};};
          const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
          let error=null,last=null;const allocationChecks=[],resizeChecks=[],handleResizeChecks=[],nearChecks=[];
          if(a.nearWork){
            const allocate=m.near.allocate.bind(m.near);
            m.near.allocate=bytes=>{
              const model=new OriginalNearHeapWork(m.near.snapshot()),expected=model.allocate(bytes),actual=allocate(bytes);
              const passed=expected===actual&&equal(model.snapshot(),m.near.snapshot());
              nearChecks.push({bytes,pointer:actual,contextTime:last.milliseconds,work:model.work(),passed});
              if(!passed)throw new Error('Near allocation work changed heap state');return actual;
            };
          }
          if(a.handleResizeWork){
            const resizeHandle=m.resizeHandle.bind(m);
            m.resizeHandle=(handle,bytes)=>{
              const model=new OriginalMemory({heap:m.heap.snapshot(),near:m.near.snapshot()});
              const work=OriginalHandleResizeWork.resize(model,handle,bytes),actual=resizeHandle(handle,bytes);
              const passed=actual===work.result&&equal(model.heap.snapshot(),m.heap.snapshot())&&equal(model.near.snapshot(),m.near.snapshot());
              handleResizeChecks.push({handle,bytes,contextTime:last.milliseconds,work,passed});
              if(!passed)throw new Error('Handle resize work changed allocation state');return actual;
            };
          }
          if(a.resizeWork){
            const resize=m.resize.bind(m);
            m.resize=(block,bytes)=>{
              const model={heap:new OriginalHeap({...m.heap.snapshot(),closedArena:true})},address=block.address;
              const work=OriginalMemoryResizeWork.resize(model,model.heap.at(address),bytes),actual=resize(block,bytes);
              const passed=actual!==null&&equal(model.heap.snapshot(),m.heap.snapshot());
              resizeChecks.push({bytes,address,contextTime:last.milliseconds,contextType:last.type,work,passed});
              if(!passed)throw new Error('Resize work model changed block state');return actual;
            };
          }
          if(a.allocationWork){
            const firstFit=m.heap.firstFit.bind(m.heap);
            m.heap.firstFit=bytes=>{
              const model=new OriginalHeapWork({...m.heap.snapshot(),closedArena:true}),expected=model.firstFit(bytes),actual=firstFit(bytes);
              const passed=expected.address===actual.address&&equal(model.snapshot(),m.heap.snapshot());
              allocationChecks.push({bytes,address:actual.address,contextTime:last.milliseconds,contextType:last.type,work:model.work(),passed});
              if(!passed)throw new Error('First-fit work model changed allocation state');return actual;
            };
          }
          try{for(const e of a.stream){last=e;const label=e.label,s=e.stack;
            if(e.type==='shape'){
              if(!loaders.has(e.catalogHandle)){const loader=new OriginalShapeLoading(m,e.catalogHandle);loader.sources=new Map(Object.entries(a.initialSources));loaders.set(e.catalogHandle,loader);}
              const loader=loaders.get(e.catalogHandle);
              const start=loader.operations.length,handle=loader.load(e),operations=loader.operations.slice(start);
              const passed=handle===e.expectedHandle&&equal(operations,e.operations);shapeChecks.push({key:e.key,handle,expectedHandle:e.expectedHandle,operations,expectedOperations:e.operations,sourceWork:loader.sourceWork.at(-1),passed});
              if(e.sceneObject)scenes.get(e.sceneObject).own(e.relative,handle);
              allocations+=operations.filter(op=>op.kind==='handle.allocate'||op.kind==='handle.reallocate').length;
              if(!passed)break;
            }else if(e.type==='sound'){
              if(!soundLoaders.has(e.catalogHandle)){const loader=new OriginalSoundLoading(m,e.catalogHandle);loader.sources=new Map(Object.entries(a.initialSoundSources));soundLoaders.set(e.catalogHandle,loader);}
              const loader=soundLoaders.get(e.catalogHandle),prepare=m.heap.prepare.bind(m.heap),firstFit=m.heap.firstFit.bind(m.heap);let cursor=0,farCount=0;
              const checkpoint=payload=>{const expected=e.checkpoints[cursor++];if(!expected||expected.requested!==payload)throw new Error('Generated sound preparation differs');const actual=snapshot(),passed=equal(actual,expected.state);checks.push({index:expected.index,passed,expected:expected.state,actual});if(!passed)throw new Error('Generated sound heap checkpoint differs');};
              m.heap.prepare=payload=>{checkpoint(payload);const value=prepare(payload);checkpoint(payload);return value;};
              m.heap.firstFit=payload=>{farCount++;return firstFit(payload);};
              const start=loader.operations.length;let handle;
              try{handle=loader.load({...e,payload:a.soundResources[e.key]});}finally{m.heap.prepare=prepare;m.heap.firstFit=firstFit;}
              const operations=loader.operations.slice(start),passed=cursor===e.checkpoints.length&&handle===e.expectedHandle&&farCount===e.farAllocations&&equal(operations,e.operations);
              soundChecks.push({key:e.key,handle,expectedHandle:e.expectedHandle,operations,expectedOperations:e.operations,farAllocations:farCount,preparation:loader.preparations.at(-1),sourceWork:loader.sourceWork.at(-1),passed});
              allocations+=farCount;if(!passed)break;
            }else if(e.type==='scene'){
              const prepare=m.heap.prepare.bind(m.heap);let cursor=0;
              const checkpoint=payload=>{const expected=e.checkpoints[cursor++];if(!expected||expected.requested!==payload)throw new Error('Generated surface preparation differs from native request');const actual=snapshot(),passed=equal(actual,expected.state);checks.push({index:expected.index,passed,expected:expected.state,actual});if(!passed)throw new Error('Generated surface heap checkpoint differs');};
              m.heap.prepare=payload=>{checkpoint(payload);const value=prepare(payload);checkpoint(payload);return value;};
              let pointer=0,rows=0,owned=0,work=null;
              try{
                if(e.kind==='script-load'){pointer=direct.load(e.arguments);directPointers.set(e.key,pointer);work=direct.work.at(-1);allocations++;}
                else if(e.kind==='script-free'){const owned=directPointers.get(e.key);if(owned!==e.pointer)throw new Error('Generated script ownership differs');direct.release(owned);directPointers.delete(e.key);frees++;}
                else if(e.kind==='object'){const scene=new OriginalAnimationMemory(m,e.arguments);scenes.set(scene.object,scene);pointer=scene.object;}
                else{const scene=scenes.get(e.object);if(!scene)throw new Error('Missing generated animation object');
                  if(e.kind==='surface'){pointer=scene.createSurface();rows=scene.rowTable;allocations++;}
                  else if(e.kind==='backup'){pointer=scene.createBackup();allocations++;}
                  else if(e.kind==='dispose'){owned=scene.images.size;scene.dispose();scenes.delete(e.object);frees+=2;}
                }
              }finally{m.heap.prepare=prepare;}
              const passed=cursor===e.checkpoints.length&&(e.kind==='object'?pointer===e.object:e.kind==='dispose'?owned===15:e.kind==='script-free'?true:pointer===e.expectedPointer&&(e.kind!=='surface'||rows===e.expectedRows));
              sceneChecks.push({kind:e.kind,key:e.key,object:e.object,pointer,rows,owned,work,passed});if(!passed)break;
            }else if(e.type==='checkpoint'){
              const actual=snapshot();checks.push({index:e.index,passed:equal(actual,e.state),expected:e.state,actual});
              if(!equal(actual,e.state))break;
              if(e.index%2===0)m.heap.prepare(e.requested);
            }else if(label==='memory.handle.allocate'){m.near.resetSearch();owners.push({kind:'handle'});
            }else if(label==='memory.raw.allocate'){owners.push({kind:'raw'});
            }else if(label==='memory.near.allocate'){const pointer=m.near.allocate(s[2]);near.push(pointer);if(owners.at(-1)?.kind==='handle'&&!owners.at(-1).id)owners.at(-1).id=pointer;
            }else if(label==='memory.near.allocate.return'){if(near.pop()!==e.ax)throw new Error('Near allocation return mismatch');
            }else if(label==='memory.near.free'){m.near.free(s[2]);m.heap.handles.delete(s[2]);
            }else if(label==='memory.far.allocate'){const b=m.heap.firstFit(e.ax+65536*e.dx);far.push(b);if(owners.length)owners.at(-1).block=b;allocations++;
            }else if(label==='memory.far.allocate.return'){if(far.pop()?.address!==16*e.ds+e.si)throw new Error('Far allocation return mismatch');
            }else if(label==='memory.resize'){resizes.push(resizes.length?null:m.resize(m.heap.at(16*e.ds+e.si),e.ax+65536*e.dx));
            }else if(label==='memory.resize.return'){resizes.pop();
            }else if(label==='memory.promote.move'){m.moveHandleTo(e.di,m.heap.at(16*e.ds+e.si));
            }else if(label==='memory.grow.pin'){m.handle(e.di).state|=0x8000;
            }else if(label==='memory.grow.unpin'){m.unlock(e.di);
            }else if(label==='memory.grow.move'){m.moveHandleTo(e.di,m.heap.at(16*e.es+e.bx));
            }else if(label==='memory.reallocate'){owners.push({kind:'reallocate',id:s[4]});
            }else if(label==='memory.reallocate.return'){const o=owners.pop();if(o?.kind!=='reallocate')throw new Error('Unpaired handle reallocation');if(e.ax===0){const old=m.handle(o.id).state;m.claimHandle(o.block,o.id);m.handle(o.id).state|=old&0xfdf0;}
            }else if(label==='memory.handle.allocate.return'){const o=owners.pop();if(o?.kind!=='handle'||o.id!==e.ax)throw new Error('Handle allocation return mismatch');m.claimHandle(o.block,o.id);
            }else if(label==='memory.raw.allocate.return'){const o=owners.pop();if(o?.kind!=='raw'||m.claimRaw(o.block)!==16*e.dx+e.ax)throw new Error('Raw allocation return mismatch');
            }else if(label==='memory.raw.free'){m.freeRaw(s[2]+16*s[3]);frees++;
            }else if(label==='memory.handle.free'){m.unlock(s[2]);
            }else if(label==='memory.discard'){m.discard(s[2]);
            }else if(label==='memory.lock'){m.lock(s[2]);
            }else if(label==='memory.unlock'){m.unlock(s[2]);
            }else if(label==='memory.retain'){m.retain(s[2]);
            }else if(label==='memory.keep.resident'){m.keepResident(s[2]);
            }else if(label==='memory.discardable'){m.discardable(s[2]);
            }else if(label==='memory.flags'){m.flags(s[3],s[2]);
            }else if(label==='memory.address'){m.address(s[2]);
            }else if(label.startsWith('memory.catalog.pin')){m.handle(label.endsWith('.find')?e.bx:e.bp).state|=0x8000;
            }else if(label.startsWith('memory.catalog.restore')){m.handle(label.endsWith('.outer')||label.endsWith('.find')?e.bx:e.bp).state=s[0];
            }else if(label==='memory.resource.restore'){m.handle(e.bp).state=s[0];
            }else if(label==='memory.resource.cached'){m.handle(e.bp).state|=0x1000;}
          }}catch(e){error={message:String(e),last};}
          return {allocations,frees,checks,error,shapeChecks,sceneChecks,soundChecks,allocationChecks,resizeChecks,handleResizeChecks,nearChecks};
        }''',dict(initial=states[0],stream=stream,allocationWork=allocation_work,resizeWork=resize_work,handleResizeWork=handle_resize_work,nearWork=near_work,staticIds=sorted(static_ids),catalog=shapes[0]['catalogHandle'] if shapes else None,initialSources=initial_sources,generatedScripts=generated_scripts,initialSoundSources=initial_sound_sources,soundResources=sound_resources))
        report['focused_checks']=page.evaluate('''()=>{
          const make=()=>new OriginalMemory({heap:{search:16,blocks:[{address:16,size:16,flags:0xc000,padding:0,handle:102},{address:32,size:8,flags:0,padding:0},{address:40,size:8,flags:0x8000,padding:0},{address:48,size:6,flags:0x4000,padding:0}],handles:[{id:102,state:0x7000,segment:1}]},near:{start:100,search:100,end:202,blocks:[{address:100,size:100,free:true},{address:202,size:65534,free:false}]}});
          const a=make(),grown=a.resize(a.heap.at(16),17);
          const b=make(),failed=b.resize(b.heap.at(16),19);
          const c=make();c.lock(102);const locked=c.discard(102);c.unlock(102);const discarded=c.discard(102);
          const d=make();d.flags(102,0x8000);d.retain(102);d.discardable(102);d.keepResident(102);
          return [
            {name:'growth to exact rounded size recalculates padding',passed:grown.size===24&&grown.padding===1&&grown.flags===0xc000},
            {name:'failed growth restores old payload and returns absorbed hole',passed:failed===null&&b.heap.at(16).size===16&&b.heap.at(32).size===8&&b.heap.search===16},
            {name:'discard obeys lock and preserves ownership flags',passed:!locked&&discarded&&c.heap.at(16).flags===0&&c.handle(102).segment===0&&c.handle(102).state===0x5000},
            {name:'ownership flag operations preserve independent bits',passed:d.handle(102).state===0xf000}
          ];
        }''')
        browser.close()
    report.update(passed=not report['error'] and len(report['checks'])==len(fixtures) and len(report['shapeChecks'])==len(shapes) and len(report['sceneChecks'])==len(scenes) and len(report['soundChecks'])==len(sounds) and report['allocations']==159 and report['frees']==43 and all(c['passed'] for c in report['checks']+report['focused_checks']+report['shapeChecks']+report['sceneChecks']+report['soundChecks']+report['allocationChecks']+report['resizeChecks']+report['handleResizeChecks']+report['nearChecks']) and (not allocation_work or len(report['allocationChecks'])==159) and (not resize_work or len(report['resizeChecks'])==97) and (not handle_resize_work or len(report['handleResizeChecks'])==83) and (not near_work or len(report['nearChecks'])==237),models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in ['heap.js','near-heap.js','memory.js']+(['memory-work.js','resource-work.js','resource-loading.js','shape-loading.js'] if generated_shapes else [])+(['animation-memory.js'] if generated_scenes else [])+(['direct-loading.js'] if generated_scripts else [])+(['sound-loading.js'] if generated_sounds else [])+(['heap-instructions.js','memory-copy-work.js','heap-work.js'] if allocation_work else [])+(['memory-resize-work.js'] if resize_work else [])+(['handle-resize-work.js'] if handle_resize_work else [])+(['near-heap-work.js'] if near_work else [])},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),source_sha256=SOURCE_SHA if generated_shapes else None,generated_shape_count=len(shapes),scope='Continuous memory structure and active handle state from one explicit initial RAM fixture. Optional shape loads, scene object/surface lifetimes, direct script lifetimes and sound preparation generate memory requests from pinned DAT contents. Native source-cache state is parsed from the starting fixture. Remaining logical memory requests/source mutation boundaries are observed inputs; startup, full scene composition, payload writes and runtime clock integration remain separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'nearChecks':[c for c in report['nearChecks'] if not c['passed']],'matching_near_allocations':sum(c['passed'] for c in report['nearChecks']),'handleResizeChecks':[c for c in report['handleResizeChecks'] if not c['passed']],'matching_handle_resizes':sum(c['passed'] for c in report['handleResizeChecks']),'resizeChecks':[c for c in report['resizeChecks'] if not c['passed']],'matching_resizes':sum(c['passed'] for c in report['resizeChecks']),'allocationChecks':[c for c in report['allocationChecks'] if not c['passed']],'matching_allocations':sum(c['passed'] for c in report['allocationChecks']),'soundChecks':[c for c in report['soundChecks'] if not c['passed']],'matching_sound_loads':sum(c['passed'] for c in report['soundChecks']),'sceneChecks':[c for c in report['sceneChecks'] if not c['passed']],'matching_scene_phases':sum(c['passed'] for c in report['sceneChecks']),'shapeChecks':[c for c in report['shapeChecks'] if not c['passed']],'matching_shapes':sum(c['passed'] for c in report['shapeChecks']),'checks':[{'index':c['index'],'passed':c['passed']} for c in report['checks'] if not c['passed']],'matching_checkpoints':sum(c['passed'] for c in report['checks'])},indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--generated-shapes',action='store_true');p.add_argument('--all-shapes',action='store_true');p.add_argument('--generated-scenes',action='store_true');p.add_argument('--generated-scripts',action='store_true');p.add_argument('--generated-sounds',action='store_true');p.add_argument('--allocation-work',action='store_true');p.add_argument('--resize-work',action='store_true');p.add_argument('--handle-resize-work',action='store_true');p.add_argument('--near-work',action='store_true');a=p.parse_args();sys.exit(0 if verify(a.trace,a.output,a.generated_shapes or a.all_shapes or a.generated_scenes or a.generated_scripts or a.generated_sounds,a.all_shapes or a.generated_scenes or a.generated_scripts or a.generated_sounds,a.generated_scenes or a.generated_scripts or a.generated_sounds,a.generated_scripts or a.generated_sounds,a.generated_sounds,a.allocation_work,a.resize_work,a.handle_resize_work,a.near_work) else 1)
