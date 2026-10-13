"""Verify sound storage plans against pinned data and focused handle behavior.

This checks memory ownership, not native PCM output or execution timing.
"""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
from playwright.sync_api import sync_playwright
from build_demo import SOURCE_SHA
from resources import parse_archive
from sound import decode_sound_with_info

ROOT=Path(__file__).resolve().parents[2]
MODELS=['heap.js','near-heap.js','memory.js','memory-work.js','resource-work.js','resource-loading.js','sound-loading.js']


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source archive')
    sounds=[]
    with zipfile.ZipFile(source) as z:
        for name in ['digisnd','voices']:
            data=z.read(f'TheTreeh/{name}.dat')
            for r in parse_archive(data):
                if r['tag']!='SND':continue
                payload=data[r['payload_offset']:r['payload_offset']+r['size']]
                info,pcm=decode_sound_with_info(payload)
                sounds.append(dict(key=f'{name}:{r["id"]}',payload=list(payload),codec=info.codec,count=len(pcm)))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in MODELS:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        result=page.evaluate('''sounds=>{
          const make=()=>new OriginalMemory({heap:{search:0x30000,blocks:[{address:0x30000,size:262144,flags:0,padding:0},{address:0x70000,size:6,flags:0x4000,padding:0}],handles:[]},near:{start:100,search:100,end:4200,blocks:[{address:100,size:4098,free:true},{address:4200,size:65534,free:false}]}});
          const bounds={minimumRate:1,maximumRate:65535};
          const inventory=sounds.map(s=>{
            const m=make(),id=m.allocateHandle(s.payload.length),loader=new OriginalSoundLoading(m,0),plan=loader.prepare(id,s.payload,bounds),b=m.heap.at(m.address(id)-6);
            const expected=s.codec===255?s.count+10:s.payload.length;
            return {key:s.key,plan,passed:b.size-6-b.padding===expected&&(s.codec!==255||plan.temporaryBytes===Math.max(s.count,s.payload.length-10)+266)&&!!(m.handle(id).state&0x2000)===(s.codec===255)};
          });
          const fragmented=()=>new OriginalMemory({heap:{search:16,blocks:[{address:16,size:16,flags:0xc000,padding:0,handle:102,payload:'preserved bytes'},{address:32,size:8,flags:0x8000,padding:0},{address:40,size:128,flags:0,padding:0},{address:168,size:6,flags:0x4000,padding:0}],handles:[{id:102,state:0x51f0,segment:1}]},near:{start:100,search:106,end:208,blocks:[{address:100,size:4,free:false},{address:106,size:100,free:true},{address:208,size:65534,free:false}]}});
          const a=fragmented(),moved=a.resizeHandle(102,30),destination=a.heap.at(a.address(102)-6);
          const b=fragmented();b.lock(102);const locked=b.resizeHandle(102,30);
          const c=fragmented();c.discard(102);const reallocated=c.resizeHandle(102,30);
          const m=make(),loader=new OriginalSoundLoading(m,0),compressed=[1,0x40,0x1f,255,99,0,0,0,0,0,2,0,128],id=m.allocateHandle(compressed.length);
          const cold=loader.prepare(id,compressed,bounds),opCount=loader.operations.length,warm=loader.prepare(id,compressed,bounds);
          const raw=[1,0x40,0x1f,8,3,0,0,0,0,0,128,129,130],rawId=m.allocateHandle(raw.length),rawPlan=loader.prepare(rawId,raw,bounds);
          const midi=m.allocateHandle(1),midiPlan=loader.prepare(midi,[0x82],bounds);
          let unsupported=false;try{loader.prepare(rawId,raw,{minimumRate:9000,maximumRate:65535});}catch(e){unsupported=String(e).includes('resampling');}
          const catalog=m.allocateHandle(16),cache=new OriginalSoundLoading(m,catalog),cached=cache.load({key:'raw',payload:raw,directoryFlags:0x20,...bounds});
          const checks=[
            {name:'relocation preserves handle, flags and payload',passed:moved&&destination.address===40&&destination.payload==='preserved bytes'&&destination.handle===102&&(a.handle(102).state&0xf000)===0x5000&&a.heap.at(16).flags===0},
            {name:'locked growth failure preserves old allocation',passed:!locked&&b.address(102)===22&&b.heap.at(16).size===16&&(b.handle(102).state&0x8000)!==0},
            {name:'discarded resize preserves handle and ownership',passed:reallocated&&c.address(102)!==0&&(c.handle(102).state&0xf000)===0x5000},
            {name:'compressed count overrides declared count',passed:cold.count===2&&cold.finalBytes===12&&cold.temporaryBytes===269},
            {name:'prepared source avoids a second resize',passed:warm.action==='prepared'&&opCount===2&&loader.operations.length===opCount},
            {name:'uncompressed source retains original storage and flags',passed:rawPlan.action==='uncompressed'&&rawPlan.bytes===13&&!(m.handle(rawId).state&0x2000)},
            {name:'non-digital source needs no preparation',passed:midiPlan.action==='non-digital'},
            {name:'unreconstructed resampling fails explicitly',passed:unsupported},
            {name:'directory bit 20 does not alter cache ownership',passed:(m.handle(cached).state&0xf000)===0x1000}
          ];
          return {inventory,checks,passed:inventory.length>0&&inventory.every(c=>c.passed)&&checks.every(c=>c.passed)};
        }''',sounds);browser.close()
    report=dict(**result,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in MODELS},source_sha256=SOURCE_SHA,scope='Original digital resource storage plans and nine synthetic ownership cases. Inventory coverage is not native execution coverage. PCM writes, resampling and instruction timing remain separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'inventory':[c for c in result['inventory'] if not c['passed']],'matching_layouts':sum(c['passed'] for c in result['inventory'])},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.output) else 1)
