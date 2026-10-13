"""Compare generated font activation and initial cursor resource ownership."""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile
from playwright.sync_api import sync_playwright
from executable import unpack
from verify_dos_resource_startup import startup_inputs,mcbs
from verify_resource_growth import ROOT,DATA,digest,arena_state
from verify_near_heap import parse as parse_near
from memory_catalog import read_catalogs,read_files


def resource_inputs():
    startup,_=startup_inputs()
    with zipfile.ZipFile(DATA/'source/The_Treehouse_1991.zip') as archive:
        image,_=unpack(archive.read('TheTreeh/treehse.exe'))
        archive_bytes=list(archive.read('TheTreeh/th.dat'))
        ibm_archive=list(archive.read('TheTreeh/ibm_snd.dat'))
        remaining_archives=[]
        for offset in [0x155,0x161,0x16c,0x184,0x18d]:
            name=image[0x321d0+offset:].split(b'\0',1)[0].decode('ascii')
            remaining_archives.append(dict(archive=list(archive.read('TheTreeh/'+name)),filename='C:\\THETREEH\\'+name))
    assets={}
    for index,tag in enumerate(['FONT','CURS']):
        entry=image[0x31660+10+15*index:0x31660+25+15*index]
        assert entry[:4]==tag.encode()[::-1] and entry[4:6]==b'\0\0'
        offset,segment,length=struct.unpack_from('<HHH',entry,6)
        assets[tag]=dict(payload=list(image[16*segment+offset:16*segment+offset+length]),flags=entry[12])
    # Mode 5's function/format descriptor is separate from the VGA surface.
    descriptor=struct.unpack_from('<H',image,0x321d0+0x20b4+2*5)[0]
    pixel_packing=image[0xd510+descriptor+6];assert pixel_packing==1
    # Pinned Sound Blaster backend query (21C10) returns its supported range;
    # resident 19888/1988C stores it for subsequent sound preparation.
    assert image[0x21c10]==0xb9 and image[0x21c13]==0xba
    sound_rates=dict(minimumRate=struct.unpack_from('<H',image,0x21c11)[0],maximumRate=struct.unpack_from('<H',image,0x21c14)[0])
    return dict(startup=startup,builtins=assets,pixelsPerByte=pixel_packing,
                soundRateLimits=sound_rates,
                archives=[dict(archive=archive_bytes,filename='C:\\THETREEH\\th.dat'),dict(archive=ibm_archive,filename='C:\\THETREEH\\ibm_snd.dat')]+remaining_archives,
                volume='REFERENCE-S',savedRectangle=list(struct.unpack_from('<4h',image,0x2e8f0+0x140)))


def verify(output):
    output.mkdir(parents=True,exist_ok=False);inputs=resource_inputs()
    fixtures={};references={}
    for stage in ['font-activation','cursor-source','cursor-activation','catalog','startup-sound']:
        folder=DATA/('resource-startup-sound-a' if stage=='startup-sound' else f'resource-startup-{stage}-a');run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
        assert run['passed'] and run['fixed_clock']
        references[stage]=digest(folder/'run.json');pair=[]
        for f in run['heap'][:14 if stage=='catalog' else 2]:
            p=folder/f['path'];assert digest(p)==f['sha256'];raw=p.read_bytes()
            state=dict(arena=arena_state(raw,f['ss'])[0],near=parse_near(raw,f['ss']),dos=mcbs(raw))
            if stage in ['catalog','startup-sound']:
                state['files']=read_files(raw,f['ss']);state['catalogs']=read_catalogs(raw,f['ss'])
                if state['catalogs']:
                    for catalog in state['catalogs']:
                        next(b for b in state['arena']['heap']['blocks'] if b.get('handle')==catalog['handle']).pop('payload')
            pair.append(state)
        fixtures[stage]=pair
    modules=['heap.js','near-heap.js','memory.js','dos-memory.js','resource-startup.js','resource-loading.js','font-loading.js','cursor-loading.js','saved-surface.js','catalog-loading.js','direct-loading.js','sound-loading.js','startup-resources.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        actual=page.evaluate('''a=>{
          const boundaries={};
          const snapshot=state=>structuredClone({arena:{...state.memory.arena,heap:state.memory.heap.snapshot()},near:state.memory.near.snapshot(),dos:state.dos.snapshot(),
            payloads:Array.from(state.memory.resourcePayloads,([id,b])=>[id,Array.from(b)]),files:state.catalogs.files,catalogs:state.catalogs.files.map(f=>state.catalogs.snapshot(f.handle))});
          const state=OriginalStartupResources.create(a,(stage,phase,state)=>{
            boundaries[stage]??=[];
            if(stage==='catalog'||boundaries[stage].length<2)boundaries[stage].push(snapshot(state));
          });
          const before=JSON.stringify(snapshot(state));OriginalFontLoading.activate(state.builtins,state.font);
          const fontStable=JSON.stringify(snapshot(state))===before,m=state.memory;
          const discarded=state.builtins.sources.get('builtin:CURS:0'),locked=state.cursor.image,lockedAddress=m.address(locked);
          m.discardable(discarded);m.discardable(locked);const available=m.available();
          return {boundaries,focused:[
            {name:'active font is not converted twice',passed:fontStable},
            {name:'cursor background dimensions derive from pixel packing',passed:state.cursor.stride===16&&state.memory.heap.at(state.cursor.background-6).size-6===256},
            {name:'no instruction-work dependency',passed:typeof OriginalResourceWork==='undefined'&&state.direct.work.length===0&&state.builtins.sourceWork.length===0},
            {name:'maximal query discards eligible cache payload while retaining handle',passed:m.handle(discarded).segment===0&&!m.resourcePayloads.has(discarded)&&available>0},
            {name:'maximal query preserves locked resource address and bytes',passed:m.address(locked)===lockedAddress&&m.resourcePayloads.has(locked)},
            {name:'memory search clamps oversized requests',passed:m.heap.searchSize(0xffffff)===0xfffff&&m.heap.searchSize(0xffffffff)===0xfffff}
          ]};
        }''',inputs);browser.close()
    checks=[]
    for stage,pair in actual['boundaries'].items():
        for phase,state in enumerate(pair):
            payloads={i:hashlib.sha256(bytes(b)).hexdigest() for i,b in state['payloads']}
            for block in state['arena']['heap']['blocks']:
                if block.get('handle') in payloads:block['payload']=payloads[block['handle']]
            for field in fixtures[stage][phase]:
                expected=fixtures[stage][phase][field];value=state[field]
                checks.append(dict(name=f'{stage} {phase} {field}',passed=value==expected,expected=expected,actual=value))
    report=dict(passed=all(c['passed'] for c in checks+actual['focused']),checks=checks,focused=actual['focused'],
        models={n:digest(ROOT/'treehouse-demo'/n) for n in modules},references=references,full_game_parity=False,playable_changed=False,
        scope='Continuous generation from executable/platform inputs through first font conversion, cursor activation, original saved rectangle, th archive, CURS 1/FONT 1 activation, free-memory query, sound configuration copy and all seven startup archives plus retained SND 0; all native boundaries are comparison outputs. Includes complete active payload hashes, allocator and DOS state. Catalogs compare initialized semantic fields and directory entries, excluding uninitialized string slack from hashing. Later archive/resource lifetimes remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],native_checks=len(checks),focused=actual['focused'],failed=[c['name'] for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
