"""Verify generated polling paths and callback trampolines against native calls."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,itertools,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    path=trace_path.parent/trace['polling']['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['polling']['sha256']:raise ValueError('Polling digest differs')
    cache={};calls=0;instructions=0;failures=[];returns=Counter();callbacks=Counter();counts=Counter();current_state=None;order_checks=0
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/polling-work.js'))
        page.evaluate('labels=>window.pollSlots=Object.fromEntries(labels.map((label,i)=>[label,i]))',trace['polling']['labels'])
        with path.open() as f:
            while True:
                batch=[json.loads(s) for s in itertools.islice(f,1000)]
                if not batch:break
                inputs=[json.dumps([row['before'],row['mouse_buttons']],separators=(',',':')) for row in batch]
                missing=list(dict.fromkeys(key for key in inputs if key not in cache))
                if missing:
                    generated=page.evaluate('''inputs=>inputs.map(([state,buttons])=>{
                      try{
                        const result=OriginalPollingWork.execute(state,{mouseButtons:buttons});let hash=2166136261;
                        for(const address of result.path){
                          if(!(address in pollSlots))throw new Error('Unobserved generated instruction '+address);
                          const word=pollSlots[address];for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((word>>>shift)&255),16777619)>>>0;
                        }
                        delete result.path;return {...result,path_hash:hash};
                      }
                      catch(e){return {error:String(e)};}
                    })''',[json.loads(key) for key in missing]);cache.update(zip(missing,generated))
                for row,key in zip(batch,inputs):
                    if current_state is None:current_state=row['before']
                    if current_state!=row['before']:failures.append(dict(ordinal=row['ordinal'],error='Continuous input state differs',expected=row['before'],actual=current_state));break
                    key=json.dumps([current_state,row['mouse_buttons']],separators=(',',':'))
                    model=cache[key];calls+=1
                    if 'error' in model:failures.append(dict(ordinal=row['ordinal'],error=model['error'],input=json.loads(key)));break
                    differences={}
                    for field,actual,expected in [('counts',model['counts'],row['counts']),('state',model['state'],row['after']),('result',model['result'],row['result'])]:
                        if actual!=expected:differences[field]=dict(expected=expected,actual=actual)
                    if 'path_hash' in row:
                        order_checks+=1
                        if model['path_hash']!=row['path_hash']:differences['path_hash']=dict(expected=row['path_hash'],actual=model['path_hash'])
                    if differences:failures.append(dict(ordinal=row['ordinal'],differences=differences,input=json.loads(key)));break
                    current_state=model['state'];instructions+=model['instructions'];returns[row['result']]+=1;callbacks.update(model['callbacks']);counts.update(model['counts'])
                if failures:break
        checks=page.evaluate('''()=>{
          const make=()=>({mouse_present:1,joystick:0,modifier:0,edges:[0,0],bindings:Array(96).fill(0),keys:Array(96).fill(0),latches:Array(96).fill(0)});
          const a=OriginalPollingWork.execute(make(),{mouseButtons:[0,0]});
          const b=OriginalPollingWork.execute(make(),{mouseButtons:[1]});
          const c=make();c.edges[0]=1;const held=OriginalPollingWork.execute(c,{mouseButtons:[1,0]});
          const right=OriginalPollingWork.execute(make(),{mouseButtons:[0,2]});
          const key=make();key.mouse_present=0;key.keys[30]=1;key.bindings[30]=42;const pressed=OriginalPollingWork.execute(key);
          key.latches[30]=1;const repeated=OriginalPollingWork.execute(key);
          key.keys[30]=0;const released=OriginalPollingWork.execute(key);
          let rejected=false;try{const s=make();s.keys[72]=1;OriginalPollingWork.execute(s);}catch(e){rejected=true;}
          return [
            {name:'keyboard callback includes 320 guest LOOP instructions',passed:a.counts['dos:0b']===320},
            {name:'new left press returns before second mouse poll',passed:b.result===1&&b.callbacks.length===2&&b.state.edges[0]===1},
            {name:'held left button produces no new edge',passed:held.result===0&&held.state.edges[0]===1},
            {name:'right button uses its independent edge state',passed:right.result===1&&right.state.edges[1]===1},
            {name:'mapped key returns its binding and records press',passed:pressed.result===42&&pressed.state.latches[30]===1},
            {name:'held mapped key is suppressed',passed:repeated.result===0},
            {name:'released mapped key clears its latch',passed:released.state.latches[30]===0},
            {name:'unreconstructed cursor movement fails explicitly',passed:rejected}
          ];
        }''');browser.close()
    report=dict(passed=not failures and calls==trace['polling']['calls'] and all(c['passed'] for c in checks),full_cpu_scheduling_parity=False,continuous_input_state=True,order_checks=order_checks,calls=calls,input_variants=len(cache),instructions=instructions,callback_counts=dict(callbacks),return_counts=dict(returns),instruction_counts=dict(counts),partial_final_calls=trace['polling']['partial_final_calls'],checks=checks,failures=failures,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/polling-work.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),polling_sha256=trace['polling']['sha256'],control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Generated resident 58E2 polling instruction paths, mouse/key edge state and DOS/mouse guest trampolines. Every completed native call compares every selected instruction count, return value and input-state memory; captures containing ordered path hashes also compare instruction order. Input state is continuous from one initial fixture without resets. Mouse callback results remain observed inputs. Timer/IRQ work outside selected code, CPU admission, joystick/cursor movement and live integration remain open; final incomplete native call is explicitly excluded.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'instruction_counts':len(counts)},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
