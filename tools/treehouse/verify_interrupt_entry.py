"""Check real-mode hardware entry and outer IRET against pinned native state."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,irq_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());irq=json.loads(irq_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-DLL control')
    if trace['events']!=irq['events']:raise ValueError('IRQ route differs')
    meta=trace['interrupt_entry'];stream=trace_path.parent/meta['path'];imeta=irq['irq'];istream=irq_path.parent/imeta['path']
    for path,digest in [(stream,meta['sha256']),(istream,imeta['sha256'])]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Fixture digest differs')
    rows=[json.loads(s) for s in stream.read_text().splitlines()];admissions=[o for s in istream.read_text().splitlines() if (o:=json.loads(s))['vector']>=0]
    entries=[r for r in rows if r['kind']==1];returns=[r for r in rows if r['kind']==2]
    if len(rows)!=meta['boundaries'] or meta['partial_final_calls'] or len(entries)!=len(admissions) or len(entries)!=len(returns):raise ValueError('Incomplete boundary capture')
    for r,o in zip(entries,admissions):
        if r['vector']!=o['vector'] or r['before']['milliseconds']!=o['milliseconds']:raise ValueError('Admission identity/time differs')
    pending=[]
    for r in rows:
        if r['kind']==1:
            if r['parent']!=(pending[-1]['ordinal'] if pending else 0xffffffff):raise ValueError('Entry nesting differs')
            pending.append(r)
        else:
            if not pending or r['parent']!=pending[-1]['ordinal']:raise ValueError('Return nesting differs')
            e=pending.pop()
            if e['after']['registers'][4]!=r['before']['registers'][4] or e['after']['segments'][2]!=r['before']['segments'][2]:raise ValueError('Return frame differs')
    source=(ROOT/'treehouse-demo/interrupt-entry.js').read_bytes()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(content=source.decode())
        results=page.evaluate('''rows=>rows.map(r=>{
          try{
            const memory=new Uint8Array(0x110000).fill(0xa5),v=new DataView(memory.buffer),put=(a,n)=>v.setUint16(a,n,true);
            if(r.kind===1){put(r.vector_base+4*r.vector,r.vector_ip);put(r.vector_base+4*r.vector+2,r.vector_cs);}
            r.stack_addresses.forEach((a,i)=>put(a,r.stack_before[i]));const before=memory.slice(),state=structuredClone(r.before),model=new OriginalInterruptEntry({memory,state});
            if(r.kind===1)model.enter(r.vector,{tableBase:r.vector_base,returnIp:r.old_eip});else model.iret();
            const differences=Object.keys(r.after).filter(k=>JSON.stringify(state[k])!==JSON.stringify(r.after[k]));
            if(differences.length)throw new Error('Register/CPU state differs '+JSON.stringify(differences.map(k=>({key:k,actual:state[k],expected:r.after[k]}))));
            const expected=before.slice(),ev=new DataView(expected.buffer);r.stack_addresses.forEach((a,i)=>ev.setUint16(a,r.stack_after[i],true));
            if(memory.some((n,i)=>n!==expected[i]))throw new Error('Stack or write extent differs');
            return {ordinal:r.ordinal,passed:true};
          }catch(e){return {ordinal:r.ordinal,passed:false,error:String(e)};}
        })''',rows)
        edges=page.evaluate('''()=>{
          const checks=[];
          for(const esp of [0,1,2,5,6,65535,0x12340000])for(const flags of [2,0xfd7,0x3f7fd7]){
            const memory=new Uint8Array(0x110000).fill(0xcc),v=new DataView(memory.buffer),state={eip:0x56789,flags,registers:[1,2,3,4,esp,6,7,8],segments:[0x1234,0x2345,0x3456,0x4567,0,0],ss_base:0x34560,cs_base:0x23450,stack_mask:65535,stack_notmask:0xffff0000,code_big:1,extflags_toggle:0x240000,direction:(flags&0x400)?-1:1},original=structuredClone(state),m=new OriginalInterruptEntry({memory,state});
            v.setUint16(32,0x1111,true);v.setUint16(34,0x2222,true);const initial=memory.slice();m.enter(8);
            const at=Array.from({length:3},(_,i)=>state.ss_base+((esp-2*(i+1))&65535)),saved=[flags&65535,0x2345,0x6789],writeSet=new Set(at.flatMap(a=>[a,a+1]));
            const entered=at.every((a,i)=>v.getUint16(a,true)===saved[i])&&state.registers[4]===(((esp&0xffff0000)|((esp-6)&65535))>>>0)&&state.flags===(flags&~0x300)&&state.eip===0x1111&&state.cs_base===0x22220&&memory.every((n,i)=>writeSet.has(i)||n===initial[i]);
            m.iret();const mask=0x247fd5,expectedFlags=(((flags&~0x300)&~mask)|((flags&65535)&mask)|2)>>>0;
            checks.push({name:'stack '+esp.toString(16)+' flags '+flags.toString(16),passed:entered&&state.registers[4]===esp&&state.eip===0x6789&&state.segments[1]===original.segments[1]&&state.flags===expectedFlags&&state.code_big===0&&state.direction===original.direction});
          }return checks;
        }''');browser.close()
    passed=all(r['passed'] for r in results+edges)
    report=dict(passed=passed,full_cpu_scheduling_parity=False,boundaries=len(rows),entries=len(entries),returns=len(returns),vectors=dict(Counter(r['vector'] for r in entries)),matching_boundaries=sum(r['passed'] for r in results),failures=[r for r in results if not r['passed']],edge_checks=edges,model_sha256=hashlib.sha256(source).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),irq_trace_sha256=hashlib.sha256(irq_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Every captured hardware IRQ0/7/12 entry after lazy flags materialization and matching outer IRET: all registers, flags, segment bases, stack words, write extent, unchanged CPU/I/O/time. Admission sequence matches the independent IRQ trace. Each boundary uses initial state; continuous guest register/flags propagation and device scheduling remain required.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','irq','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.irq,a.control,a.output) else 1)
