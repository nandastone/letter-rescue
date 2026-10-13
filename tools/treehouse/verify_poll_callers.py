"""Compare generated uninterrupted wait/idle continuations between input polls."""
from pathlib import Path
from collections import Counter
import argparse,bisect,hashlib,itertools,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    for group in ['polling','irq']:
        with (trace_path.parent/trace[group]['path']).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=trace[group]['sha256']:raise ValueError('Input digest differs')
    interrupts=[]
    for line in (trace_path.parent/trace['irq']['path']).read_text().splitlines():
        r=json.loads(line)
        if r['vector']>=0:interrupts.append(r['context'][0])
    def classify(prev,row):
        if prev is None:return None,'initial incomplete context'
        c=prev['cpu_after'];n=row['cpu_before'];lo=c['context'][0]+1;hi=n['context'][0]
        if row['gap_count']!=hi-lo:raise ValueError('Gap instruction count differs from CPU counter')
        start=bisect.bisect_left(interrupts,lo)
        if start<len(interrupts) and interrupts[start]<=hi:return None,'interrupt within continuation'
        if c['stack'][:2]!=n['stack'][:2]:return None,'caller transition'
        if prev['result']:return None,'input action'
        caller=c['stack'][0];s=c['caller'];index=((c['bp']+6-c['sp'])&65535)//2
        if caller==0x569e:
            if index>=16:raise ValueError('Timer argument outside observed stack')
            timer=c['stack'][index]
            if timer>3:raise ValueError('Invalid timer index')
            if not s[timer]:return None,'timer expiry transition'
            return dict(kind='timer',index=timer,countdowns=s[:4]),None
        if caller==0x5787:
            if index>=16:raise ValueError('Sound argument outside observed stack')
            sound=c['stack'][index]
            if sound:return None,'specific sound resource lookup'
            if not any(s[10:13]):return None,'sound completion transition'
            return dict(kind='sound',id=0,active=s[10:13]),None
        if caller==0x1a68:
            keys=prev['after']['keys'];modifier=prev['after']['modifier']
            if s[4] or s[5] or not s[7] or not s[2] or keys[59] or keys[60] or modifier&4:return None,'nature action branch'
            return dict(kind='nature',input=0,keys=keys,modifier=modifier,specialMode=s[4],pendingTask=s[5],rollState=s[7],countdown=s[2],mask=s[8],goalExponent=s[9]),None
        raise ValueError('Unknown polling caller')
    bases={'main':trace['location']['main_base'],'resident':trace['location']['main_base']+0xd510,'nature':trace['location']['overlay_base']}
    cache={};skipped=Counter();matching=Counter();failures=[];calls=0;instructions=0;previous=None
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in ['wait-work.js','nature-idle-work.js']:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        page.evaluate('bases=>window.callerBases=bases',bases)
        with (trace_path.parent/trace['polling']['path']).open() as f:
            while True:
                batch=[json.loads(line) for line in itertools.islice(f,1000)]
                if not batch:break
                selected=[]
                for row in batch:
                    calls+=1;params,reason=classify(previous,row);previous=row
                    if reason:skipped[reason]+=1;continue
                    key=json.dumps(params,separators=(',',':'));selected.append((row,key,params))
                missing={key:params for row,key,params in selected if key not in cache}
                if missing:
                    generated=page.evaluate('''inputs=>inputs.map(params=>{
                      try{
                        let generator,next,result,path=[];
                        if(params.kind==='nature'){
                          generator=OriginalNatureIdleWork.run(params);next=generator.next();
                        }else{
                          generator=params.kind==='timer'?OriginalWaitWork.timer({...params,readCountdown:i=>params.countdowns[i]}):OriginalWaitWork.sound({...params,readChannels:()=>params.active.map(active=>({active,segment:0,offset:0}))});
                          next=generator.next();
                          while(!next.done&&typeof next.value==='string')next=generator.next();
                          if(next.done||next.value.call!=='input-poll')throw new Error('Caller did not reach its input poll');
                          next=generator.next(0);
                        }
                        while(!next.done&&typeof next.value==='string'){
                          const [region,offset]=next.value.split(':');path.push(callerBases[region]+parseInt(offset,16));next=generator.next();
                        }
                        if(params.kind!=='nature'&&(next.done||next.value.call!=='input-poll'))throw new Error('Caller did not repeat polling');
                        let hash=2166136261;for(const word of path)for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((word>>>shift)&255),16777619)>>>0;
                        return {path,hash,result:next.value};
                      }catch(e){return {error:String(e)};}
                    })''',list(missing.values()));cache.update(zip(missing,generated))
                for row,key,params in selected:
                    actual=cache[key]
                    if 'error' in actual:failures.append(dict(ordinal=row['ordinal'],params=params,actual=actual));break
                    if len(actual['path'])!=row['gap_count'] or actual['path']!=row['gap_addresses'] or actual['hash']!=row['gap_hash']:
                        failures.append(dict(ordinal=row['ordinal'],params=params,actual=actual,expected=dict(count=row['gap_count'],hash=row['gap_hash'],path=row['gap_addresses'])));break
                    if params['kind']=='nature' and actual['result']['complete']!=row['cpu_before']['caller'][14]:
                        failures.append(dict(ordinal=row['ordinal'],error='Nature completion flag differs'));break
                    matching[params['kind']]+=1;instructions+=len(actual['path'])
                if failures:break
        checks=page.evaluate('''()=>{
          const drive=(g,answer=()=>0)=>{let next=g.next(),instructions=[],calls=[];for(let guard=0;!next.done&&guard<10000;guard++){
            if(typeof next.value==='string'){instructions.push(next.value);next=g.next();}
            else {calls.push(next.value);next=g.next(answer(next.value));}
          }if(!next.done)throw new Error('Focused execution did not finish');return {result:next.value,instructions,calls};};
          const a=drive(OriginalWaitWork.timer({index:0,readCountdown:()=>0}));
          const b=drive(OriginalWaitWork.timer({index:0,readCountdown:()=>5}),call=>call.call==='input-poll'?1:0);
          const c=drive(OriginalWaitWork.timer({index:0,readCountdown:()=>0,interruptible:false}),()=>7);
          const timer={countdowns:[0,0,0,0],setCountdown(i,n){this.countdowns[i]=n;}};let set=false;
          const d=drive(OriginalWaitWork.setTimer({index:2,ticks:3,timer}),call=>{if(call.call==='input-poll'){set=timer.countdowns[2]===3;timer.countdowns[2]=0;}return 0;});
          const channels=[{offset:10,segment:1,active:1},{offset:10,segment:2,active:2},{offset:20,segment:3,active:4}];
          const status=pointer=>drive(OriginalWaitWork.channelStatus({pointer,readChannels:()=>channels}));
          const e=status({offset:10,segment:2}),f=status({offset:20,segment:3}),g=status({offset:0,segment:0}),h=status({offset:10,segment:9});
          const stopped=drive(OriginalWaitWork.sound({id:0,readChannels:()=>channels.map(c=>({...c,active:0}))}));
          const interrupted=drive(OriginalWaitWork.sound({id:0,readChannels:()=>channels}),call=>call.call==='input-poll'?1:0);
          return [
            {name:'expired interruptible wait returns zero',passed:a.result===0&&a.calls.length===1},
            {name:'interruptible wait clears input and returns one',passed:b.result===1&&b.calls.at(-1).call==='clear-input'},
            {name:'non-aborting wait preserves last poll AX on expiry',passed:c.result===7&&c.calls.length===1},
            {name:'timer wrapper writes selected shared countdown',passed:set&&d.result===0},
            {name:'sound pointer compares both offset and segment',passed:e.result===2},
            {name:'third sound channel is checked',passed:f.result===4},
            {name:'null sound pointer ORs all active channels',passed:g.result===7},
            {name:'unmatched sound pointer returns zero',passed:h.result===0},
            {name:'inactive sound finishes without polling',passed:stopped.result===0&&stopped.calls.length===0},
            {name:'input aborts sound wait through clear-input call',passed:interrupted.result===1&&interrupted.calls.at(-1).call==='clear-input'}
          ];
        }''');browser.close()
    report=dict(passed=not failures and calls==trace['polling']['calls'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,polls=calls,matching=dict(matching),instructions=instructions,skipped=dict(skipped),generated_variants=len(cache),checks=checks,failures=failures,models={name:hashlib.sha256((ROOT/'treehouse-demo'/name).read_bytes()).hexdigest() for name in ['wait-work.js','nature-idle-work.js']},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Uninterrupted timer waits, sound ID zero waits, and nature idle continuations chosen from observed arguments/global state, never from path length/hash. Full generated ordered instructions and gap hashes compared. IRQ admission counters identify interrupted intervals independently; all uncomposed resource/transition/interruption paths are reported, not claimed as passing execution. Initial caller state remains an offline fixture; no live timing integration.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
