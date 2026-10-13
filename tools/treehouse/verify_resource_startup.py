"""Compare generated startup arena headers with the pinned original.

Executable stack parameters generate the initial near heap. The conventional
arena takes a DOS allocation result as a platform input; generating that DOS
allocation and subsequent arena growth remain separate work.
"""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile
from playwright.sync_api import sync_playwright
from executable import unpack
from build_demo import SOURCE_SHA,ROOT
from verify_near_heap import parse as parse_near

DATA=ROOT/'testing/output/treehouse'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output,reference_suffix='d'):
    output.mkdir(parents=True,exist_ok=False)
    source=DATA/'source/The_Treehouse_1991.zip';assert digest(source)==SOURCE_SHA
    with zipfile.ZipFile(source) as z:
        exe=z.read('TheTreeh/treehse.exe');image,meta=unpack(exe)
        mz=struct.unpack_from('<14H',exe)
        packed=struct.unpack_from('<9H',exe,16*(mz[4]+mz[11]))
    # Validate the original runtime's ADD SP,imm16 before extracting its bias.
    assert image[0xd5a8:0xd5aa]==b'\x81\xc4'
    stack=dict(stackPointer=packed[4],stackBias=struct.unpack_from('<H',image,0xd5aa)[0])
    fixtures={};reports={}
    for stage in ['near','heap']:
        folder=DATA/f'resource-startup-{stage}-{reference_suffix}';run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
        assert run['passed'] and len(run['heap'])==2
        f=run['heap'][1];path=folder/f['path'];assert digest(path)==f['sha256']
        fixtures[stage]=(path.read_bytes(),f);reports[stage]=run
    raw,f=fixtures['near'];expected_near=parse_near(raw,f['ss'])
    raw,f=fixtures['heap'];word=lambda p:struct.unpack_from('<H',raw,p)[0]
    offset,segment=struct.unpack_from('<2H',raw,16*f['ss']+0x203a);assert offset==0
    control=16*segment;words=list(struct.unpack_from('<11H',raw,control))
    allocated=[e for e in reports['heap']['events'] if e['label']=='arena.allocated' and e['ax']>e['ds']]
    assert len(allocated)==1 and allocated[0]['ax']==segment
    platform=dict(segment=allocated[0]['ax'],paragraphs=allocated[0]['bx'])
    expected_heap=dict(blocks=[],handles=[],search=words[2]+16*words[3]);address=words[0]+16*words[1]
    for _ in range(3):
        header=word(address);size=2*(header&7)+16*word(address+2);flags=header&0xffc0
        expected_heap['blocks'].append(dict(address=address,size=size,flags=flags,padding=(header>>3)&7))
        if flags==0x4000:break
        address+=size
    assert len(expected_heap['blocks'])==2 and flags==0x4000
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-startup.js'))
        actual=page.evaluate('a=>({near:OriginalResourceStartup.near(a.stack),arena:OriginalResourceStartup.arena(a.platform)})',dict(stack=stack,platform=platform))
        rejected=page.evaluate('''()=>{
          const cases=[()=>OriginalResourceStartup.near({stackPointer:65535,stackBias:1}),()=>OriginalResourceStartup.near({stackPointer:2,stackBias:0}),()=>OriginalResourceStartup.arena({segment:0x100,paragraphs:2}),()=>OriginalResourceStartup.arena({segment:0x9fff,paragraphs:3})];
          return cases.map(run=>{try{run();return false;}catch(error){return true;}});
        }''')
        browser.close()
    arena=actual['arena'];generated_control=[6,platform['segment']+1,6,platform['segment']+1,arena['paragraphs'],arena['committedParagraphs'],arena['emsSegment'],0,int(arena['closed']),0,0]
    checks=[dict(name='near heap from executable stack parameters',passed=actual['near']==expected_near,expected=expected_near,actual=actual['near']),
            dict(name='conventional arena free chain',passed=arena['heap']==expected_heap,expected=expected_heap,actual=arena['heap']),
            dict(name='complete arena control record',passed=generated_control==words,expected=words,actual=generated_control),
            dict(name='invalid arena extents rejected',passed=all(rejected),results=rejected)]
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,source_sha256=SOURCE_SHA,model_sha256=digest(ROOT/'treehouse-demo/resource-startup.js'),
                inputs=dict(executable_stack=stack,dos_allocation=platform),full_game_parity=False,scope=__doc__.strip(),
                references={stage:digest(DATA/f'resource-startup-{stage}-{reference_suffix}/run.json') for stage in ['near','heap']},reference_suffix=reference_suffix)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-suffix',default='d')
    a=p.parse_args();raise SystemExit(0 if verify(a.output,a.reference_suffix) else 1)
