"""Compare semantic near/conventional arena growth with native startup calls."""
from pathlib import Path
import argparse,hashlib,json,struct
from playwright.sync_api import sync_playwright
from build_demo import ROOT
from verify_near_heap import parse as parse_near

DATA=ROOT/'testing/output/treehouse'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def arena_state(raw,ss):
    word=lambda at:struct.unpack_from('<H',raw,at)[0]
    pointer=16*ss+0x203a;control=word(pointer)+16*word(pointer+2)
    words=list(struct.unpack_from('<11H',raw,control));blocks=[];handles=[];address=words[0]+16*words[1]
    for _ in range(10000):
        header=word(address);size=2*(header&7)+16*word(address+2);flags=header&0xffc0;padding=(header>>3)&7
        assert flags in [0,0x4000,0x8000,0xc000]
        block=dict(address=address,size=size,flags=flags,padding=padding)
        if flags==0xc000:
            handle=word(address+4);state=word(16*ss+handle);segment=word(16*ss+handle+2)
            assert (state&15)+16*segment==address
            block.update(handle=handle,payload=hashlib.sha256(raw[address+6:address+size-padding]).hexdigest())
            handles.append(dict(id=handle,state=state,segment=segment))
        blocks.append(block)
        if flags==0x4000:break
        assert size>=6;address+=size
    else:raise ValueError('Unterminated original arena')
    return dict(control=control,paragraphs=words[4],committedParagraphs=words[5],emsSegment=words[6],closed=bool(words[8]),
                heap=dict(blocks=blocks,handles=sorted(handles,key=lambda h:h['id']),search=words[2]+16*words[3])),words


def available_paragraphs(raw,arena):
    # DOS can extend its owned MCB through consecutive unowned MCBs.
    # This parses a platform input for the offline check, not browser state.
    address=arena['control']-16;total=struct.unpack_from('<H',raw,address+3)[0]
    assert raw[address] in [0x4d,0x5a] and total==arena['committedParagraphs']
    for _ in range(10000):
        if raw[address]==0x5a:return total
        address+=16*(struct.unpack_from('<H',raw,address+3)[0]+1)
        assert raw[address] in [0x4d,0x5a]
        if struct.unpack_from('<H',raw,address+1)[0]:return total
        total+=1+struct.unpack_from('<H',raw,address+3)[0]
    raise ValueError('Unterminated DOS allocation chain')


def verify(output):
    output.mkdir(parents=True,exist_ok=False);cases=[];references={}
    for stage in ['near-growth','arena-growth']:
        folder=DATA/f'resource-startup-{stage}-a';run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
        assert run['passed'] and run['fixed_clock'];references[stage]=digest(folder/'run.json')
        fixtures=run['heap'];assert len(fixtures)==(4 if stage=='near-growth' else 14)
        for index in range(0,len(fixtures),2):
            pair=fixtures[index:index+2];raw=[]
            for phase,f in enumerate(pair):
                path=folder/f['path'];assert f['phase']==phase and digest(path)==f['sha256'];raw.append(path.read_bytes())
            begin=next(e for e in run['events'] if e['label']==('near.grow' if stage=='near-growth' else 'arena.grow') and e['milliseconds']==pair[0]['milliseconds'])
            end=next(e for e in run['events'] if e['label']==('near.grow.return' if stage=='near-growth' else 'arena.grow.return') and e['milliseconds']==pair[1]['milliseconds'])
            ss=pair[0]['ss'];assert ss==pair[1]['ss']
            if stage=='near-growth':
                word=lambda at:struct.unpack_from('<H',raw[0],16*ss+at)[0]
                assert word(0x1772)==5 and word(0x1774)==word(0x177a)+2
                cases.append(dict(kind='near',index=index//2,initial=parse_near(raw[0],ss),expected=parse_near(raw[1],ss),
                                  payload=begin['cx'],growth=dict(limit=word(0x176e)+1,quantum=word(0x17da))))
            else:
                initial,before_words=arena_state(raw[0],ss);expected,after_words=arena_state(raw[1],ss)
                # Only total size, committed size and closed flag may change.
                assert all(before_words[i]==after_words[i] for i in [0,1,2,3,6,7,9,10])
                cases.append(dict(kind='arena',index=index//2,initial=initial,expected=expected,payload=pair[0]['requested'],
                                  maximumParagraphs=available_paragraphs(raw[0],initial),expectedBytes=end['ax']+65536*end['dx']))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['heap.js','near-heap.js','memory.js','resource-startup.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        results=page.evaluate('''cases=>cases.map(c=>{
          try{
            let actual,result;
            if(c.kind==='near'){const h=new OriginalNearHeap(c.initial);result=h.grow(c.payload,c.growth);actual=h.snapshot();}
            else{actual=structuredClone(c.initial);result=OriginalResourceStartup.growArena(actual,c.payload,c.maximumParagraphs);}
            const passed=JSON.stringify(actual)===JSON.stringify(c.expected)&&(c.kind==='near'?result===true:result===c.expectedBytes);
            return {...c,actual,result,passed};
          }catch(error){return {...c,passed:false,error:String(error)};}
        })''',cases)
        focused=page.evaluate('''()=>{
          const create=growth=>new OriginalNearHeap({...OriginalResourceStartup.near({stackPointer:2048,stackBias:23072}),growth});
          const auto=create({limit:65536,quantum:1024}),pointer=auto.allocate(58);
          const fallback=create(null),grew=fallback.grow(58,{limit:25200,quantum:8192});
          const failure=create(null),before=JSON.stringify(failure.snapshot()),failed=failure.grow(58,{limit:25136,quantum:8192});
          const arena=OriginalResourceStartup.arena({segment:0x100,paragraphs:3}),partial=OriginalResourceStartup.growArena(arena,33,5),closed=JSON.stringify(arena),again=OriginalResourceStartup.growArena(arena,16,9);
          const fresh=OriginalResourceStartup.arena({segment:0x200,paragraphs:3});
          const memory=new OriginalMemory({heap:fresh.heap,arena:fresh,maximumParagraphs:1024,near:{...OriginalResourceStartup.near({stackPointer:2048,stackBias:23072}),growth:{limit:65536,quantum:1024}}});
          const handle=memory.allocateHandle(1528),block=memory.heap.at(memory.address(handle)-6);
          return [
            {name:'allocation retries after generated near growth',passed:pointer===25118&&auto.end===25598&&auto.at(25116).size===58},
            {name:'near growth falls back to paragraph alignment',passed:grew&&fallback.end===25182},
            {name:'failed near growth preserves state',passed:!failed&&JSON.stringify(failure.snapshot())===before},
            {name:'partial conventional growth closes arena',passed:partial===32&&arena.closed&&arena.paragraphs===5},
            {name:'closed conventional arena does not grow again',passed:again===0&&JSON.stringify(arena)===closed},
            {name:'handle allocation drives both near and conventional growth',passed:handle===25118&&block.size===1534&&block.padding===0&&memory.arena.committedParagraphs===99&&memory.near.end===25598}
          ];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+focused),calls=results,checks=focused,references=references,
                models={name:digest(ROOT/'treehouse-demo'/name) for name in ['heap.js','near-heap.js','memory.js','resource-startup.js']},full_game_parity=False,
                scope='All two near and seven conventional arena growth calls during original startup. Compare complete allocator state, existing payload hashes and returned conventional byte counts; check automatic near allocation retry and exhaustion. Each call starts from an offline fixture. DOS availability is parsed from its MCB chain. Generating DOS state, startup requests, whole resource lifetimes and integration into the playable game remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],calls=[dict(kind=r['kind'],index=r['index'],passed=r['passed'],error=r.get('error')) for r in results],checks=focused),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.output) else 1)
