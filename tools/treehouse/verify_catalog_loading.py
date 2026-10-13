"""Compare original archive opens with semantic directory/cache ownership."""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,json,struct,zipfile
from playwright.sync_api import sync_playwright
from build_demo import SOURCE_SHA
from memory_catalog import read_files,read_catalogs
from verify_resource_growth import ROOT,DATA,digest,arena_state
from verify_dos_resource_startup import mcbs
from verify_near_heap import parse as parse_near


def verify(output):
    output.mkdir(parents=True,exist_ok=False);folder=DATA/'resource-startup-catalog-a'
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'));assert run['passed'] and len(run['heap'])==14
    source=DATA/'source/The_Treehouse_1991.zip';assert digest(source)==SOURCE_SHA
    cases=[]
    with zipfile.ZipFile(source) as archive:
        for index in range(0,14,2):
            pair=run['heap'][index:index+2];raw=[]
            for f in pair:
                path=folder/f['path'];assert digest(path)==f['sha256'];raw.append(path.read_bytes())
            ss=pair[0]['ss'];files=read_files(raw[1],ss);opened=files[0]
            filename=PureWindowsPath(opened['filename']).name
            data=archive.read('TheTreeh/'+filename)
            before=arena_state(raw[0],ss)[0];after=arena_state(raw[1],ss)[0]
            # Header string slack is uninitialized storage, not loader output.
            # All initialized fields/directory entries are compared separately.
            next(b for b in after['heap']['blocks'] if b.get('handle')==opened['handle']).pop('payload')
            cases.append(dict(name=filename,arena=before,near={**parse_near(raw[0],ss), 'growth':dict(limit=65536,quantum=8192)},dos=mcbs(raw[0]),
                files=read_files(raw[0],ss),lookup=struct.unpack_from('<H',raw[0],16*ss+0x204e)[0],
                metadata={k:opened[k] for k in ['filename','volume','fileHandle']},archive=list(data),
                expected=dict(handle=opened['handle'],arena=after,near=parse_near(raw[1],ss),dos=mcbs(raw[1]),files=files,
                              catalog=read_catalogs(raw[1],ss)[0],lookup=opened['handle'])))
    modules=['heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js','resource-loading.js','catalog-loading.js'];checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        for case in cases:
            try:
                actual=page.evaluate('''a=>{
                  const owner=a.dos.find(b=>b.segment===a.arena.control/16-1).owner;
                  const dos=new OriginalDOSMemory(a.dos,owner),m=new OriginalMemory({heap:a.arena.heap,arena:a.arena,dos,near:a.near});
                  const loader=new OriginalCatalogLoading(m,{files:a.files,lookup:a.lookup});
                  const handle=loader.open({...a.metadata,archive:a.archive}),catalog=loader.catalogs.get(handle);
                  return {handle,arena:{...m.arena,heap:m.heap.snapshot()},near:m.near.snapshot(),dos:dos.snapshot(),files:loader.files,
                    catalog:loader.snapshot(handle),lookup:loader.lookup,payloads:Array.from(catalog.loader.payloads,([id,b])=>[id,Array.from(b)]),operations:catalog.loader.operations};
                }''',case)
                for id,bytes_ in actual.pop('payloads'):
                    block=next(b for b in actual['arena']['heap']['blocks'] if b.get('handle')==id)
                    block['payload']=hashlib.sha256(bytes(bytes_)).hexdigest()
                for field,expected in case['expected'].items():
                    checks.append(dict(name=case['name']+' '+field,passed=actual[field]==expected,expected=expected,actual=actual[field]))
            except Exception as error:errors.append(dict(name=case['name'],error=str(error)))
        browser.close()
    report=dict(passed=not errors and len(checks)==49 and all(c['passed'] for c in checks),checks=checks,errors=errors,
        models={n:digest(ROOT/'treehouse-demo'/n) for n in modules},reference_sha256=digest(folder/'run.json'),source_sha256=SOURCE_SHA,full_game_parity=False,playable_changed=False,
        scope='Seven complete archive opens from separate offline allocator/DOS/file-list fixtures. Allocation sizes, directory tables, cache handles and flagged preloads derive from pinned DAT bytes. File handles and canonical path/volume are explicit platform inputs. Catalog string slack is uninitialized and omitted from payload hashing; all initialized semantic fields and full directory contents are compared separately. Full startup/platform I/O/lifetime integration remains open.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),errors=errors,failed=[c['name'] for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
