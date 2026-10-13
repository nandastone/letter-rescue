"""Check the payment formula independently using offline native cursor locations.

This is a dependency audit, not a runtime implementation or continuous game replay.
Each payment reads its own original starting seed and cursor handle location.
"""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile
from build_demo import ROOT,SOURCE_SHA
from executable import unpack
from resources import parse_archive
from verify_board_native_journey import model

DATA=ROOT/'testing/output/treehouse'
VALUES=[100,50,25,10,5,1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(seed,level,balance,mystery,offset,include_second=True):
    draws=[]
    def random(maximum):
        nonlocal seed
        before=seed;seed=(seed*214013+2531011)&0xffffffff
        result=(seed>>16)%(maximum+1)
        draws.append(dict(maximum=maximum,before=before,after=seed,result=result))
        return result
    def coins(amount,randomize=True):
        result=[]
        for i,value in enumerate(VALUES):
            n=amount//value
            if randomize and i<3 and n>0 and random(1):n-=1
            amount-=n*value;result.append(n)
        return result
    if mystery:assert random(1)==0, 'This audit expects a mystery payment'
    start,span,divisor=[[5,8,4],[10,15,4],[50,75,4]][level]
    first=-((start+random(span))//divisor)
    delta=0 if mystery else offset+36
    second=first+(delta if random(1) else -delta)
    if second==0:second=1
    phrase=random(prepare.phrase_count-1)
    first_preparation=coins(abs(first))
    second_preparation=coins(abs(second)) if include_second else None
    paid=min(abs(first),balance)
    return dict(first=first,second=second,delta=delta,phrase=phrase,
                first_preparation=first_preparation,second_preparation=second_preparation,
                displayed_payment=coins(paid,False),paid=paid,seed=seed,draws=draws)


def audit(output,reference):
    output.parent.mkdir(parents=True,exist_ok=True)
    source=DATA/'source/The_Treehouse_1991.zip';assert digest(source)==SOURCE_SHA
    with zipfile.ZipFile(source) as archive:
        image,_=unpack(archive.read('TheTreeh/treehse.exe'))
        phrases=next(r['strings'] for r in parse_archive(archive.read('TheTreeh/modules.dat')) if r['tag']=='STRL' and r['id']==4013)
    prepare.phrase_count=len(phrases)
    original_cursor=image[0x310b0:0x310b0+68]
    run=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert run['complete'] and run['passed'] and run['seek_loss']
    assert run['content_sha256']=='a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c'
    report=dict(passed=False,source_sha256=SOURCE_SHA,reference=str(reference),reference_sha256=digest(reference/'run.json'),payments=[],cursor_locations=[],checks=[],full_game_parity=False)
    def check(name,passed):report['checks'].append(dict(name=name,passed=bool(passed)))
    def cursor(path):
        raw=path.read_bytes();prefix=path.with_name(path.name.replace('.ram-0','.ram-100000')).read_bytes()
        # Embedded resident catalog has FONT 0 then CURS 0. This resource is
        # absent from the separately loaded DAT directory list at DS:204E.
        record=544+0x31660+25
        assert raw[record:record+4]==b'SRUC'
        handle=struct.unpack_from('<H',raw,record+13)[0]
        state,segment=struct.unpack_from('<HH',raw,0x323f0+handle)
        assert not state&0x200, 'EMS cursor needs a separate dependency model'
        offset=(state&15)+6;physical=segment*16+offset
        assert (prefix+raw)[physical:physical+68]==original_cursor
        return dict(handle=handle,offset=offset,segment=segment,physical=physical)
    for index,decision in enumerate(run['decisions']):
        name=decision['name'];path=reference/'state'/f'{name}.ram-0'
        report['cursor_locations'].append(dict(name=name,ram_sha256=digest(path),**cursor(path)))
        before,after=decision['before'],decision['after'];player=before['player']
        if after['balances'][player]>=before['balances'][player]:continue
        previous=run['decisions'][index-1]['name'] if index else 'initial'
        path=reference/'state'/f'{previous}.ram-0';state=model(path);location=cursor(path)
        assert state['mode']==0 and state['seed']==before['seed']
        assert state['balances']==before['balances']
        mystery=before['types'][after['nodes'][player]]==25
        args=dict(seed=before['seed'],level=state['levels'][player],balance=before['balances'][player],mystery=mystery,offset=location['offset'])
        predicted=prepare(**args)
        current=prepare(**args,include_second=mystery)
        fixed=prepare(**{**args,'offset':10})
        expected=dict(seed=after['seed'],coins=after['coins'],paid=before['balances'][player]-after['balances'][player])
        check(name+' paid amount',predicted['paid']==expected['paid'])
        check(name+' displayed payment coins',predicted['displayed_payment']==expected['coins'][0])
        check(name+' unused second coin array',predicted['second_preparation']==expected['coins'][1])
        check(name+' final random state',predicted['seed']==expected['seed'])
        report['payments'].append(dict(name=name,mystery=mystery,initial_ram_sha256=digest(path),cursor=location,
            predicted=predicted,expected=expected,current_behavior_seed_matches=current['seed']==expected['seed'],
            fixed_offset_seed_matches=fixed['seed']==expected['seed'],fixed_offset_second_coins_match=fixed['second_preparation']==expected['coins'][1]))
    assert len(report['payments'])==9
    report['scope']=__doc__.strip()+' The formula, both coin preparations, actual paid amount and final random state are checked for all nine payments. Native images remain separately checked by browser journey verifiers. Cursor offsets are observed fixture inputs here, never browser runtime inputs. The runtime still needs a generated resource-lifetime model; no constant offset or checkpoint seed fix is accepted.'
    report['passed']=all(c['passed'] for c in report['checks'])
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),payments=[dict(name=p['name'],first=p['predicted']['first'],second=p['predicted']['second'],offset=p['cursor']['offset'],current_seed_matches=p['current_behavior_seed_matches'],fixed_coins_match=p['fixed_offset_second_coins_match']) for p in report['payments']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'board-native-loss-a')
    a=p.parse_args();raise SystemExit(0 if audit(a.output,a.reference) else 1)
