"""Compare resource-entry helpers and generated inputs against native execution."""
from pathlib import Path
import argparse,bisect,hashlib,json,struct,sys,zipfile
from playwright.sync_api import sync_playwright
from memory_catalog import read_catalogs
from verify_memory_lifetimes import shape_calls
from build_demo import SOURCE_SHA
from sound import decode_sound_with_info
from sound_memory_calls import sound_calls

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,catalog_path,memory_path,scene_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if not work or work['routine']!='resident:7A30+memory' or len(work['calls'])!=2496 or len(work['blocks'])!=2496 or len(work['results'])!=2496:raise ValueError('Incomplete entry/helper observations')
    records={};expanded={};source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched archive')
    with zipfile.ZipFile(source) as z:
        for catalog in read_catalogs(catalog_path.read_bytes(),13253):
            data=z.read(f'TheTreeh/{catalog["archive"]}.dat')
            for r in catalog['records']:
                key=(r['tag'],r['id'])
                if key in records:continue
                records[key]=r['length']+((r['flags']&15)<<16)
                payload=data[r['offset']+1:r['offset']+1+records[key]]
                if r['tag']=='SND' and len(payload)>=13 and payload[0] in (1,0x81) and payload[3]==255:
                    info,_=decode_sound_with_info(payload);expanded[key]=info.decoded_samples+10
    executable=(ROOT/'testing/output/treehouse/research-resources/unpacked.bin').read_bytes()
    if hashlib.sha256(executable).hexdigest()!='f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f':raise ValueError('Unresearched executable')
    for offset in [0x3166a,0x31679]:
        tag,id=struct.unpack_from('<IH',executable,offset)
        records.setdefault((tag.to_bytes(4,'big').strip(b'\0').decode('ascii'),id),struct.unpack_from('<H',executable,offset+10)[0]+((executable[offset+12]&15)<<16))
    queries=[e for e in trace['events'] if e['label']=='resource.lookup'];times=[q['milliseconds'] for q in queries]
    native_results={r['call']:r for r in work['results']};blocks={r['call']:r['header'] for r in work['blocks']}
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']};inputs=[];keys=[]
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    for call in work['calls']:
        q=queries[bisect.bisect_right(times,call['begin'])-1];key=((q['ax']+65536*q['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii'),q['cx']);keys.append(key)
        cached,state,segment=call['header'];input=dict(cachedHandle=cached,state=state,segment=segment)
        if cached and ((state&15) or segment):
            h=blocks[call['ordinal']];input.update(blockSize=(h[0]&7)*2+16*h[1],padding=(h[0]>>3)&7)
        inputs.append(input)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for filename in ['memory-work.js','resource-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/filename))
        models=page.evaluate('rows=>rows.map(r=>OriginalResourceWork.entryMemory(r))',inputs)
        checks=page.evaluate('''()=>{
          const a=OriginalMemoryWork.address({handle:10,state:0xc003,segment:200});
          const zero=OriginalMemoryWork.address({handle:0}),gone=OriginalMemoryWork.address({handle:10,state:0x1000,segment:0});
          const length=OriginalMemoryWork.length({handle:10,state:0x1f0,segment:200,blockSize:0x1000e,padding:7});
          const empty=OriginalMemoryWork.length({handle:0}),ems=OriginalMemoryWork.length({handle:10,state:0x200,segment:200});
          let rejected=false;try{OriginalMemoryWork.address({handle:10,state:0x200,segment:200});}catch(e){rejected=true;}
          return [
            {name:'materialized address refreshes age and preserves ownership flags',passed:a.state===0xc1f3&&a.address===3209},
            {name:'null and discarded addresses stay zero',passed:zero.address===0&&gone.address===0&&gone.state===0x1000},
            {name:'payload length subtracts padding across the 16-bit boundary',passed:length.bytes===65537&&length.ax===1&&length.dx===1},
            {name:'null and EMS length queries return zero',passed:empty.bytes===0&&ems.bytes===0},
            {name:'EMS materialization is explicitly unsupported',passed:rejected}
          ];
        }''');browser.close()
    address_returns=[e for e in trace['events'] if e['label']=='memory.address.return']
    def compare(model,call,key):
        ordinal=call['ordinal'];actual=counts[ordinal];native=native_results[ordinal]
        differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in actual.keys()|model['entries'].keys() if actual.get(a,0)!=model['entries'].get(a,0)}
        size=model.get('bytes',records[key]);handle=model['input']['cachedHandle'] if model['resident'] else 0
        # E88E uses the compressed stream's output count; E935 resizes to that
        # count plus the ten-byte sound header, then EC40 sets the 2000 bit.
        prepared=model['resident'] and bool(model['input']['state']&0x2000) and key in expanded
        expected_size=expanded[key] if prepared else records[key]
        returned=native['ax']==handle and native['dx']+65536*native['cx']==size
        addresses=[e for e in address_returns if call['begin']<=e['milliseconds']<=call['end']]
        address_equal=len(addresses)==(1 if model['input']['cachedHandle'] else 0) and all(e['ax']+16*e['dx']==model['address'] for e in addresses)
        return dict(ordinal=ordinal,key=list(key),instructions=model['instructions'],differences=differences,return_equal=returned,address_equal=address_equal,storage_form='decoded sound' if prepared else 'directory payload',storage_length=size,expected_storage_length=expected_size,storage_length_equal=size==expected_size,passed=not differences and returned and address_equal and size==expected_size)
    results=[compare(m,c,k) for m,c,k in zip(models,work['calls'],keys)]
    memory=json.loads(memory_path.read_text());scene=json.loads(scene_path.read_text())
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Memory evidence is not accepted')
    for filename,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/filename).read_bytes()).hexdigest()!=digest:raise ValueError('Generated memory uses an old model')
    if scene['events']!=trace['events'] or scene['boundaries']!=trace['boundaries'] or scene['actions']!=trace['actions']:raise ValueError('Observer runs differ')
    if len(memory['shapeChecks'])!=79 or len(memory['sceneChecks'])!=12 or len(memory['checks'])!=104:raise ValueError('Incomplete generated memory evidence')
    initial=(scene_path.parent/scene['heap'][0]['path']).read_bytes();shapes,_=shape_calls(scene,initial)
    generated=[];selected=set()
    def generated_check(begin,end,model):
        calls=[c for c in work['calls'] if begin<=c['begin'] and c['end']<=end]
        if len(calls)!=1:raise ValueError('Generated operation needs exactly one entry query')
        call=calls[0];ordinal=call['ordinal']
        if ordinal in selected:raise ValueError('Entry query counted twice')
        selected.add(ordinal);row=compare(model,call,keys[ordinal])
        row['input_equal']=all(model['input'].get(k)==v for k,v in inputs[ordinal].items());row['passed']=row['passed'] and row['input_equal'];generated.append(row)
    for shape,model in zip(shapes,memory['shapeChecks']):generated_check(shape['milliseconds'],shape['end'],model['sourceWork']['memoryWork'])
    sounds=[]
    if memory.get('soundChecks'):
        sounds,_=sound_calls(scene,initial)
        if len(sounds)!=2399 or len(memory['soundChecks'])!=2399:raise ValueError('Incomplete generated sound entry coverage')
        for sound,model in zip(sounds,memory['soundChecks']):
            if sound['key']!=model['key'] or not model['passed']:raise ValueError('Generated sound correspondence differs')
            generated_check(sound['milliseconds'],sound['end'],model['sourceWork']['memoryWork'])
    direct_models=iter(s for s in memory['sceneChecks'] if s['kind']=='script-load');begin=None
    for e in trace['events']:
        if e['label']=='resource.find':begin=e['milliseconds']
        elif e['label']=='resource.find.return':
            model=next(direct_models);generated_check(begin,e['milliseconds'],model['work']['entryMemory']);begin=None
    if len(generated)!=81+len(sounds):raise ValueError('Incomplete generated entry queries')
    report=dict(passed=all(r['passed'] for r in results+generated+checks),calls=results,generated=generated,checks=checks,
        exact_calls=sum(r['passed'] for r in results),generated_exact_calls=sum(r['passed'] for r in generated),models=memory['models'],
        memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        source_sha256=SOURCE_SHA,
        scope='All 2496 resource-entry paths, including 75C6 address/age work, EC14 length queries and 6FA9 block arithmetic. Native input fixtures cover the full set; generated queries use shape/script/sound inputs independently supplied by the continuous memory model. Pointer and size returns match native registers. Lengths match directory payload sizes or prepared compressed-sound output counts plus ten bytes. Startup, remaining helpers, payload writes and scheduling remain separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']][:10],'generated':[r for r in generated if not r['passed']][:10]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','catalog','memory','scene','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.catalog,a.memory,a.scene,a.output) else 1)
