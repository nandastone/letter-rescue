"""Generate DOS allocation state from source-defined platform and EXE parameters."""
from pathlib import Path
import argparse,json,struct,zipfile
from playwright.sync_api import sync_playwright
from build_demo import SOURCE_SHA,ROOT
from executable import unpack
from verify_resource_growth import DATA,digest,arena_state


def executable_layout():
    path=DATA/'source/The_Treehouse_1991.zip';assert digest(path)==SOURCE_SHA
    with zipfile.ZipFile(path) as z:
        exe=z.read('TheTreeh/treehse.exe');image,_=unpack(exe)
    assert struct.unpack_from('<H',exe,12)[0]==65535
    assert image[0xd593]==0xbf
    return dict(dataSegmentRelative=struct.unpack_from('<H',image,0xd594)[0])


def startup_inputs():
    path=DATA/'source/The_Treehouse_1991.zip';assert digest(path)==SOURCE_SHA
    with zipfile.ZipFile(path) as z:
        exe=z.read('TheTreeh/treehse.exe');image,_=unpack(exe);mz=struct.unpack_from('<14H',exe)
        packed=struct.unpack_from('<9H',exe,16*(mz[4]+mz[11]))
        config_name=image[0x321d0+0x89:].split(b'\0',1)[0].decode().lower()
        config=z.read('TheTreeh/'+config_name)
    assert image[0xd5a8:0xd5aa]==b'\x81\xc4'
    font=image[0x31660+10:0x31660+25];assert font[:6]==b'TNOF\0\0'
    # Pinned core default shell and Sound Blaster environment, not RAM inputs.
    return dict(**executable_layout(),stackPointer=packed[4],stackBias=struct.unpack_from('<H',image,0xd5aa)[0],
                configurationBytes=len(config),screenHeight=struct.unpack_from('<H',image,0xd510+0x9ce4+8)[0],
                environment=['PATH=Z:\\','COMSPEC=Z:\\COMMAND.COM','BLASTER=A220 I7 D1 H5 T6']),struct.unpack_from('<H',font,10)[0]


def mcbs(raw):
    blocks=[];segment=0x16f
    for _ in range(10000):
        offset=16*segment;kind=raw[offset];owner,paragraphs=struct.unpack_from('<HH',raw,offset+1)
        assert kind in [0x4d,0x5a]
        blocks.append(dict(segment=segment,paragraphs=paragraphs,owner=owner,type=kind))
        if kind==0x5a:return blocks
        segment+=paragraphs+1
    raise ValueError('Unterminated DOS conventional chain')


def fixtures(folder):
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'));assert run['passed'] and run['fixed_clock']
    data=[]
    for f in run['heap']:
        p=folder/f['path'];assert digest(p)==f['sha256'];data.append(p.read_bytes())
    return run,data


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    boot,boot_raw=fixtures(DATA/'resource-startup-heap-d')
    growth,growth_raw=fixtures(DATA/'resource-startup-arena-growth-a')
    calls=[]
    for index in range(0,len(growth['heap']),2):
        a,b=growth['heap'][index:index+2]
        calls.append(dict(bytes=a['requested'],arena=arena_state(growth_raw[index],a['ss'])[0],expectedArena=arena_state(growth_raw[index+1],b['ss'])[0],
                          before=mcbs(growth_raw[index]),after=mcbs(growth_raw[index+1])))
    original_attempts=[dict(requested=e['bx'],segment=e['ax']) for e in boot['events'] if e['label']=='arena.allocated']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['dos-memory.js','resource-startup.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        actual=page.evaluate('''a=>{
          const platform=OriginalDOSMemory.treehouse(a.layout),dos=platform.dos,before=dos.snapshot(),attempts=[];
          const allocate=dos.allocate.bind(dos);dos.allocate=paragraphs=>{const result=allocate(paragraphs);attempts.push({requested:paragraphs,segment:result.segment});return result;};
          const arena=OriginalResourceStartup.allocateArena(dos,platform.dataSegment),after=dos.snapshot();
          const growth=a.calls.map(c=>{
            const before=dos.snapshot(),state=structuredClone(c.arena),bytes=OriginalResourceStartup.growWithDOS(state,c.bytes,dos);
            return {before,after:dos.snapshot(),arena:state,bytes};
          });
          return {dataSegment:platform.dataSegment,processSegment:platform.processSegment,before,arena,after,attempts,growth};
        }''',dict(layout=executable_layout(),calls=calls))
        focused=page.evaluate('''()=>{
          const d=new OriginalDOSMemory([{segment:0x200,paragraphs:8,owner:0,type:0x5a}],0x300);
          const a=d.allocate(3),b=d.allocate(4),exhausted=d.allocate(1);d.free(a.segment);d.free(b.segment);const merged=d.allocate(8);
          const shrink=d.resize(merged.segment,2),partial=d.resize(merged.segment,20),resized=d.block(merged.segment);
          return [
            {name:'first-fit split and exact fit',passed:a.segment===0x201&&b.segment===0x205},
            {name:'allocation exhaustion reports largest free block',passed:!exhausted.ok&&exhausted.error===8&&exhausted.paragraphs===0},
            {name:'free blocks coalesce before allocation',passed:merged.ok&&merged.segment===0x201},
            {name:'shrink releases space and failed expansion claims available space',passed:shrink.ok&&!partial.ok&&partial.paragraphs===8&&resized.paragraphs===8&&resized.owner===0x300},
            {name:'invalid free is rejected',passed:d.free(0x100).error===9}
          ];
        }''');browser.close()
    checks=[dict(name='generated data segment',passed=actual['dataSegment']==boot['heap'][0]['ss']),
            dict(name='DOS chain before resource initialization',passed=actual['before']==mcbs(boot_raw[0]),expected=mcbs(boot_raw[0]),actual=actual['before']),
            dict(name='generated arena allocation retries',passed=actual['attempts']==original_attempts,expected=original_attempts,actual=actual['attempts']),
            dict(name='generated initial arena',passed=actual['arena']==arena_state(boot_raw[1],boot['heap'][1]['ss'])[0]),
            dict(name='DOS chain after resource initialization',passed=actual['after']==mcbs(boot_raw[1]),expected=mcbs(boot_raw[1]),actual=actual['after'])]
    for index,(case,result) in enumerate(zip(calls,actual['growth'])):
        for field,expected in [('before',case['before']),('after',case['after']),('arena',case['expectedArena'])]:
            checks.append(dict(name=f'growth {index} {field}',passed=result[field]==expected,expected=expected,actual=result[field]))
    report=dict(passed=all(c['passed'] for c in checks+focused),checks=checks,focused=focused,inputs=executable_layout(),
                models={n:digest(ROOT/'treehouse-demo'/n) for n in ['dos-memory.js','resource-startup.js']},
                sources={n:digest(DATA/'capture-core'/n) for n in ['src/dos/dos_memory.cpp','src/dos/dos_execute.cpp','include/dos_inc.h','include/config.h']},
                reference_sha256={n:digest(DATA/n/'run.json') for n in ['resource-startup-heap-d','resource-startup-arena-growth-a']},full_game_parity=False,
                scope='Source-defined conventional DOS map and executable data-segment parameter generate process allocation, resource arena location and retries. DOS ownership/type/size state advances continuously through all seven startup arena growth calls; no native DOS state or available-size results initialize the model. Resource-arena state and growth requests for each later call remain offline inputs; full startup resource requests, complete payload bytes and playable integration remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),focused=focused,failures=[c for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
