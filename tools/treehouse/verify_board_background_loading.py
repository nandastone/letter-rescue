"""Generate complete board-background resource ownership from the pinned shape."""
from pathlib import Path
import argparse,hashlib,json,zipfile
from playwright.sync_api import sync_playwright
from verify_heap import parse as heap_state,ROOT
from verify_near_heap import parse as near_state
from memory_catalog import read_catalogs
from resources import parse_archive
from build_demo import SOURCE_SHA


def verify(reference,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads((reference/'run.json').read_text(encoding='utf-8'));fixtures=trace['heap']
    assert trace['passed'] and len(fixtures)==2 and trace['snapshot_operation']=='shape'
    raw=[];states=[]
    for f in fixtures:
        data=(reference/f['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==f['sha256']
        raw.append(data);states.append(dict(heap=heap_state(data,f['ss']),near=near_state(data,f['ss'])))
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
    with zipfile.ZipFile(source) as archive:
        data=archive.read('TheTreeh/modules.dat')
        record=next(r for r in parse_archive(data) if r['tag']=='SHAP' and r['id']==4001)
        payload=list(data[record['payload_offset']:record['payload_offset']+record['size']])
    catalog=next(c for c in read_catalogs(raw[0],fixtures[0]['ss']) if c['archive']=='modules')
    entry=next(e for e in catalog['records'] if e['tag']=='SHAP' and e['id']==4001)
    assert entry['length']==record['size'] and entry['offset']==record['checksum_offset']
    begin=next(e for e in trace['events'] if e['label']=='shape.load' and e['milliseconds']==fixtures[0]['milliseconds'])
    end=next(e for e in trace['events'] if e['label']=='shape.load.return' and e['milliseconds']==fixtures[1]['milliseconds'])
    assert begin['stack'][2]==1
    expected=states[1];converted=next(b for b in expected['heap']['blocks'] if b.get('handle')==end['ax'])
    converted.pop('payload')  # Pixel decoding is a separate renderer comparison.
    report=dict(passed=False,reference=str(reference),source_sha256=SOURCE_SHA,checks=[],errors=[],full_game_parity=False)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['heap.js','near-heap.js','memory.js','resource-loading.js','shape-loading.js']:
            page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        try:
            actual=page.evaluate('''a=>{
                const memory=new OriginalMemory(a.state),loader=new OriginalShapeLoading(memory,a.catalog,{observeWork:false});
                if(a.cached)loader.sources.set('modules:4001',a.cached);
                const handle=loader.load({key:'modules:4001',payload:a.payload,paletteHandle:a.palette,directoryFlags:a.flags});
                return {handle,heap:memory.heap.snapshot(),near:memory.near.snapshot(),operations:loader.operations,moves:memory.heap.moves,workRecords:loader.sourceWork.length};
            }''',dict(state=states[0],catalog=catalog['handle'],cached=entry['handle'],payload=payload,palette=begin['stack'][3],flags=entry['flags']))
            report['checks'].append(dict(name='converted handle',passed=actual['handle']==end['ax'],expected=end['ax'],actual=actual['handle']))
            for kind in ['heap','near']:
                differences={k:dict(expected=expected[kind][k],actual=actual[kind][k]) for k in expected[kind] if expected[kind][k]!=actual[kind][k]}
                report['checks'].append(dict(name=kind+' complete state',passed=not differences,differences=differences))
            report.update(operations=actual['operations'],moves=actual['moves'])
            report['checks'].append(dict(name='no instruction accounting dependency',passed=actual['workRecords']==0))
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and len(report['checks'])==4 and all(c['passed'] for c in report['checks'])
    report['models']={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in ['heap.js','near-heap.js','memory.js','resource-loading.js','shape-loading.js']}
    report['scope']='One complete SHAP 4001 load: generate cache ownership, storage sizes, scratch allocation, packing, resizing and flag restoration from pinned resource bytes and one offline starting allocator fixture. Compare all allocator/handle metadata and existing resource payload preservation. Newly converted pixel bytes are checked separately by renderer tests. Does not establish generated startup/whole-scene resource lifetimes or fix the served game.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],errors=report['errors'],checks=[dict(name=c['name'],passed=c['passed'],different_fields=list(c.get('differences',{}))) for c in report['checks']],operations=report.get('operations')),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/board-background-loading-a')
    a=p.parse_args();raise SystemExit(0 if verify(a.reference,a.output) else 1)
