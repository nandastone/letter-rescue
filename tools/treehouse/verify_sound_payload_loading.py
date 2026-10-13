"""Compare semantic sound cache bytes/ownership with original load boundaries."""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile
from playwright.sync_api import sync_playwright
from build_demo import ROOT, SOURCE_SHA
from resources import parse_archive
from sound import decode_sound_with_info
from memory_catalog import read_catalogs
from verify_resource_growth import arena_state
from verify_near_heap import parse as parse_near

DATA = ROOT/'testing/output/treehouse'
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))


def verify(output, model):
    output.mkdir(parents=True, exist_ok=False)
    folder = DATA/'maze-ending-sound-payload-a'
    control = DATA/'maze-ending-boundaries-control-a'
    observed = read(folder/'run.json'); plain = read(control/'run.json')
    assert observed['passed'] and plain['passed'] and observed['actions'] == plain['actions']
    files = [Path('frames.jsonl')] + [p.relative_to(control) for p in (control/'state').iterdir() if p.suffix != '.state']
    checks = [dict(name='ordinary control '+str(p), passed=digest(folder/p) == digest(control/p)) for p in files]
    source = DATA/'source/The_Treehouse_1991.zip'
    assert digest(source) == SOURCE_SHA
    archives, records, inventory, cases = {}, {}, [], []
    with zipfile.ZipFile(source) as archive:
        for name in ['th','th64','modules','ibm_snd','midisnd','digisnd','voices']:
            data = archives[name] = archive.read('TheTreeh/'+name+'.dat')
            for r in parse_archive(data):
                if r['tag'] != 'SND': continue
                payload = data[r['payload_offset']:r['payload_offset']+r['size']]
                records[name, r['id']] = payload
                if name not in ['digisnd','voices'] or payload[3] != 255: continue
                info, pcm = decode_sound_with_info(payload)
                expected = bytearray(payload[:10])+pcm
                expected[3] = 8
                struct.pack_into('<H', expected, 4, len(pcm))
                inventory.append(dict(key=f'{name}:{r["id"]}', payload=list(payload), expected=digest_bytes(expected)))
        for index in range(0, len(observed['heap']), 2):
            a, b = observed['heap'][index:index+2]
            before, after = [(folder/f['path']).read_bytes() for f in [a,b]]
            assert digest_bytes(before) == a['sha256'] and digest_bytes(after) == b['sha256']
            start = next(e for e in observed['events'] if e['label'] == 'sound.load' and e['milliseconds'] == a['milliseconds'])
            end = next(e for e in observed['events'] if e['label'] == 'sound.load.return' and e['milliseconds'] == b['milliseconds'])
            ss, rid = a['ss'], start['stack'][2]
            catalogs = read_catalogs(before, ss)
            catalog, entry = next((c, e) for c in catalogs for e in c['records'] if e['tag'] == 'SND' and e['id'] == rid)
            initial, _ = arena_state(before, ss); expected, _ = arena_state(after, ss)
            handles = initial['heap']['handles']
            cached = entry['handle']
            if cached and not any(h['id'] == cached for h in handles):
                state, segment = struct.unpack_from('<HH', before, ss*16+cached)
                handles.append(dict(id=cached, state=state, segment=segment))
            cached_bytes = None
            if cached:
                block = next((b for b in initial['heap']['blocks'] if b.get('handle') == cached), None)
                if block:
                    cached_bytes = list(before[block['address']+6:block['address']+block['size']-block['padding']])
            minimum, maximum = struct.unpack_from('<HH', before, ss*16+0x212e)
            catalog_block = next(b for b in initial['heap']['blocks'] if b.get('handle') == catalog['handle'])
            catalog_bytes = before[catalog_block['address']+6:catalog_block['address']+catalog_block['size']-catalog_block['padding']]
            archive_data = archives[catalog['archive']]
            source_entry = next(r for r in parse_archive(archive_data) if r['tag'] == 'SND' and r['id'] == rid)
            cache_offset = 80+source_entry['directory_entry_offset']-struct.unpack_from('<I',archive_data)[0]+9
            cases.append(dict(name=f'{index//2} {catalog["archive"]}:{rid}',
                initial=dict(heap=initial['heap'], near=parse_near(before,ss)), cached=cached,
                cachedBytes=cached_bytes, catalogHandle=catalog['handle'],
                catalogBytes=list(catalog_bytes), cacheOffset=cache_offset, resourceId=rid,
                request=dict(key=f'{catalog["archive"]}:SND:{rid}', payload=list(records[catalog['archive'],rid]),
                    directoryFlags=entry['flags'], minimumRate=minimum, maximumRate=maximum),
                expected=dict(heap=expected['heap'], near=parse_near(after,ss)), expectedHandle=end['ax']))
    modules = ['heap.js','near-heap.js','memory.js','resource-loading.js','catalog-loading.js','startup-resources.js']
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True); page = browser.new_page()
        for name in modules: page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        page.add_script_tag(path=str(model))
        # No instruction accounting module is loaded by this verifier.
        if page.evaluate('typeof OriginalSoundLoading.decodedPayload === "function"'):
            results = page.evaluate('a=>a.map(s=>Array.from(OriginalSoundLoading.decodedPayload(s.payload)))', inventory)
            checks.extend(dict(name='decoded header and PCM '+a['key'], passed=digest_bytes(bytes(b)) == a['expected']) for a,b in zip(inventory,results))
        for case in cases:
            try:
                actual = page.evaluate('''a=>{
                  const m=new OriginalMemory(a.initial),catalogs=new OriginalCatalogLoading(m,{lookup:a.catalogHandle});
                  const loader=new OriginalResourceLoading(m,a.catalogHandle,{observeWork:false});
                  const entry={tag:'SND',id:a.resourceId,payload:a.request.payload,flags:a.request.directoryFlags,handle:a.cached};
                  catalogs.catalogs.set(a.catalogHandle,{handle:a.catalogHandle,previous:0,loader,records:[entry]});
                  if(a.cached)loader.sources.set('SND:'+a.resourceId,a.cached);
                  if(a.cachedBytes)loader.payloads.set(a.cached,Uint8Array.from(a.cachedBytes));
                  const handle=OriginalStartupResources.loadSound({memory:m,catalogs},a.resourceId,a.request),heap=m.heap.snapshot();
                  heap.handles=heap.handles.filter(h=>(h.state&15)||h.segment).sort((a,b)=>a.id-b.id);
                  return {handle,cacheHandle:entry.handle,heap,near:m.near.snapshot(),payloads:Array.from(loader.payloads,([id,b])=>[id,Array.from(b)])};
                }''',case)
                # The catalog model owns semantic directory records. Serialize
                # its changed cache word; all other bytes, including slack,
                # must remain equal to the independently captured result.
                catalog_bytes = bytearray(case['catalogBytes'])
                struct.pack_into('<H',catalog_bytes,case['cacheOffset'],actual.pop('cacheHandle'))
                catalog_block = next(b for b in actual['heap']['blocks'] if b.get('handle') == case['catalogHandle'])
                catalog_block['payload'] = digest_bytes(catalog_bytes)
                for handle, data in actual.pop('payloads'):
                    block = next(b for b in actual['heap']['blocks'] if b.get('handle') == handle)
                    block['payload'] = digest_bytes(bytes(data))
                checks.append(dict(name=case['name']+' returned handle', passed=actual.pop('handle') == case['expectedHandle']))
                for field, expected in case['expected'].items():
                    checks.append(dict(name=case['name']+' '+field, passed=actual[field] == expected,
                        **({} if actual[field] == expected else dict(expected=expected, actual=actual[field]))))
            except Exception as error:
                errors.append(dict(name=case['name'], error=str(error)))
        focused = page.evaluate('''()=>{
          if(typeof OriginalSoundLoading.decodedPayload!=='function')return [];
          const rejects=p=>{try{OriginalSoundLoading.decodedPayload(p);return false;}catch(e){return true;}};
          const h=[1,248,42,255,99,0,1,0,2,0];
          const one=OriginalSoundLoading.decodedPayload([...h,1,0,127]);
          const flip=OriginalSoundLoading.decodedPayload([...h,2,0,127,224]);
          return [{name:'stream count overrides header, codec and loops retained',passed:one[3]===8&&one[4]===1&&one[6]===1&&one[8]===2&&one[10]===127},
            {name:'wrapped delta 128',passed:flip[10]===127&&flip[11]===255},
            {name:'empty/truncated compressed streams rejected',passed:rejects([...h,0,0,127])&&rejects([...h,2,0,127])}];
        }''')
        checks.extend(focused); browser.close()
    report = dict(passed=not errors and all(c['passed'] for c in checks), checks=checks, errors=errors,
        native_loads=len(cases), compressed_assets=len(inventory), source_sha256=SOURCE_SHA,
        reference_sha256=digest(folder/'run.json'), model_sha256=digest(model),
        full_game_parity=False, playable_changed=False, scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),native_loads=len(cases),compressed_assets=len(inventory),
        failed=[c['name'] for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']


def digest_bytes(data): return hashlib.sha256(data).hexdigest()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',type=Path,default=ROOT/'treehouse-demo/sound-loading.js')
    args=parser.parse_args()
    raise SystemExit(0 if verify(args.output,args.model) else 1)
