"""Compose cursor helpers with copies/masks and compare nested native state/work."""
from pathlib import Path
from collections import Counter
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    streams={}
    for kind in ['cursors','blits','sprites']:
        meta=trace[kind];path=trace_path.parent/meta['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Observation digest differs: '+kind)
        if meta['partial_final_calls']:raise ValueError('Incomplete final call: '+kind)
        rows=[json.loads(s) for s in path.read_text().splitlines()]
        if len(rows)!=meta['calls']:raise ValueError('Call count differs')
        for row in rows:
            if 'pixels' in row:
                payload=gzip.decompress((trace_path.parent/row['pixels']['path']).read_bytes())
                if hashlib.sha256(payload).hexdigest()!=row['pixels']['sha256']:raise ValueError('Pixel digest differs')
                row['payload']=base64.b64encode(payload).decode()
        streams[kind]=sorted(rows,key=lambda r:r['ordinal'])
    modules=['cursor-work.js','surface-copy-work.js','mono-sprite-work.js']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for name in modules:page.add_script_tag(path=str(ROOT/'treehouse-demo'/name))
        result=page.evaluate('''streams=>{
          const results=[],graphics=[],usedGraphics={blits:new Set(),sprites:new Set()},children=new Map();
          for(const row of streams.cursors){if(!children.has(row.parent))children.set(row.parent,[]);children.get(row.parent).push(row);}
          const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),u16=a=>Array.from(a,v=>v&65535);
          function assert(test,message){if(!test)throw new Error(message);}
          function record(g,onCall){
            const counts={};let hash=2166136261,next=g.next();
            while(!next.done){let answer;const step=next.value;
              if(typeof step==='string'){const at=parseInt(step.split(':')[1],16);counts[at]=(counts[at]||0)+1;for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((at>>>shift)&255),16777619)>>>0;}
              else answer=onCall(step);
              next=g.next(answer);
            }
            return {counts,hash,value:next.value};
          }
          function checkWork(actual,row){
            assert(actual.hash===row.path_hash,'Ordered instruction hash differs');
            const keys=new Set([...Object.keys(actual.counts),...Object.keys(row.counts)]);
            for(const k of keys)assert((actual.counts[k]||0)===(row.counts[k]||0),'Instruction count differs at '+(+k).toString(16));
          }
          function cursor(row,state,input){
            const pending=(children.get(row.ordinal)||[]).slice();
            assert(equal(Array.from(state),row.before),'Cursor '+row.ordinal+' entry state differs');
            if(row.kind===0){assert(equal(u16(input.pointer),row.pointer),'Cursor pointer differs');assert(equal(u16(input.rect),row.rect),'Cursor rectangle differs');}
            function child(action,edge){
              const next=pending.shift();assert(next&&next.edge===edge,'Missing or reordered cursor child at '+edge.toString(16));
              const kind={'cursor-prepare':0,'cursor-hide':1,'cursor-restore':2}[action.call];assert(next.kind===kind,'Cursor child kind differs');
              return cursor(next,state,kind===0?{pointer:action.surface.slice(0,2),rect:action.rect}:{});
            }
            function graphic(action){
              const kind=action.call==='surface-copy'?'blits':'sprites';
              const native=streams[kind].filter(r=>r.begin>=row.begin&&r.end<=row.end&&!usedGraphics[kind].has(r.ordinal)).sort((a,b)=>a.begin-b.begin)[0];
              assert(native,'Missing '+kind+' callee');usedGraphics[kind].add(native.ordinal);
              assert(native.context===state[1]&&native.mode===action.mode,'Graphics context/mode differs');
              let model,input;
              const bytes=Uint8Array.from(atob(native.payload||''),c=>c.charCodeAt(0));
              const sourcePixels=bytes.slice(0,native.source_size),beforePixels=bytes.slice(native.source_size,native.source_size+native.destination_size),expected=bytes.slice(native.source_size+native.destination_size);
              if(kind==='blits'){
                assert(native.source_id===action.source&&native.destination_id===action.destination,'Cursor copy surfaces differ');
                assert(equal(u16(action.sourceRect),native.source_rect)&&equal(u16(action.destinationRect),native.destination_rect),'Cursor copy rectangles differ');
                const header=id=>Array.from(state.slice(id===0x2088?10:26,id===0x2088?26:42));
                const source=header(action.source),destination=header(action.destination);
                assert(equal(source,native.source)&&equal(destination,native.destination),'Cursor copy headers differ');
                input={...native,source,destination,sourcePixels,beforePixels};model=OriginalSurfaceCopyWork;
              }else{
                assert(native.kind===1&&native.x===(action.x&65535)&&native.y===(action.y&65535)&&native.color===action.color,'Cursor mask operands differ');
                const surface=Array.from(state.slice(10,26));assert(equal(surface,native.surface),'Cursor mask header differs');
                input={...native,surface,sourcePixels,beforePixels};model=OriginalMonoSpriteWork;
              }
              let dispatch=0;
              const actual=record(model.run(input),step=>{
                if(step.call==='rep-move-words'){
                  const sample=native.slices[dispatch++];assert(sample&&sample.address===step.address&&sample.remaining===step.remaining,'Cursor copy REP operands differ');
                  return Math.min(step.remaining,Math.max(1,sample.budget));
                }
                return child(step,action.address);
              });
              if(kind==='blits')assert(dispatch===native.slices.length,'Unused copy REP samples');
              checkWork(actual,native);
              if(native.copied||native.drawn)assert(actual.value.pixels.length===expected.length&&actual.value.pixels.every((v,i)=>v===expected[i]),'Cursor callee pixels differ');
              graphics.push({kind,ordinal:native.ordinal,instructions:Object.values(actual.counts).reduce((a,b)=>a+b,0),writes:actual.value.writes});
            }
            const gen=row.kind===0?OriginalCursorWork.prepare(state,input):row.kind===1?OriginalCursorWork.hide(state):OriginalCursorWork.restore(state);
            const actual=record(gen,action=>{
              if(action.call==='cursor-hide')return child(action,action.address);
              if(action.call==='surface-copy'||action.call==='mask-sprite')return graphic(action);
              assert(action.call==='handle-address','Unsupported cursor callee');
            });
            assert(!pending.length,'Unused nested cursor calls');checkWork(actual,row);
            assert(equal(Array.from(state),row.after),'Cursor '+row.ordinal+' return state differs');
            results.push({ordinal:row.ordinal,kind:row.kind,instructions:Object.values(actual.counts).reduce((a,b)=>a+b,0)});
          }
          const failures=[];
          for(const row of children.get(-1)||[]){
            try{cursor(row,Uint16Array.from(row.before),{pointer:row.pointer,rect:row.rect});}
            catch(e){failures.push({ordinal:row.ordinal,error:String(e)});break;}
          }
          const checks=[];
          function fresh(count=0){const s=new Uint16Array(42);s[0]=count&65535;s[1]=123;s[3]=20;s[4]=30;s[5]=2;s[6]=3;s[10]=0;s[11]=0xa000;s[12]=5;s[13]=7;s[28]=10;s[29]=15;s[30]=26;s[31]=31;return s;}
          function drive(g,s,actions=[]){return record(g,a=>{actions.push(a);if(a.call==='cursor-hide')drive(OriginalCursorWork.hide(s),s,actions);});}
          for(const n of [-3,-1,0,1,2]){
            const s=fresh(n),actions=[];drive(OriginalCursorWork.hide(s),s,actions);
            checks.push({name:'hide nesting '+n,passed:OriginalCursorWork.signed(s[0])===(n<0?n-1:-n-1)&&s[1]===123&&actions.filter(a=>a.call==='surface-copy').length===(n<0?0:1)});
          }
          for(const n of [-3,-1,0,1,2]){
            const s=fresh(n),actions=[];drive(OriginalCursorWork.restore(s),s,actions);
            checks.push({name:'restore nesting '+n,passed:OriginalCursorWork.signed(s[0])===(n<0?n+1:n>0?n-1:0)&&s[1]===123&&actions.filter(a=>a.call==='mask-sprite').length===(n===-1?2:0)});
          }
          const s=fresh(1),actions=[];s[2]=1;drive(OriginalCursorWork.restore(s),s,actions);
          checks.push({name:'deferred motion hides old background before showing new position',passed:s[0]===0&&s[2]===0&&equal(Array.from(s.slice(28,32)),[23,34,39,50])&&equal(actions.map(a=>a.call),['cursor-hide','surface-copy','surface-copy','handle-address','mask-sprite','handle-address','mask-sprite'])});
          for(const [name,rect,hidden] of [['overlap',[5,8,21,24],true],['above',[0,8,5,24],false],['below',[21,8,30,24],false],['left',[5,0,21,8],false],['right',[5,24,21,30],false]]){
            const s=fresh(),actions=[];drive(OriginalCursorWork.prepare(s,{pointer:[0,0xa000],rect}),s,actions);
            checks.push({name:'strict cursor rectangle '+name,passed:s[0]===(hidden?65535:1)&&actions.some(a=>a.call==='cursor-hide')===hidden});
          }
          return {results,graphics,failures,checks};
        }''',streams);browser.close()
    report=dict(passed=not result['failures'] and len(result['results'])==len(streams['cursors']) and all(c['passed'] for c in result['checks']),full_cpu_scheduling_parity=False,calls=len(streams['cursors']),matching_calls=len(result['results']),instructions=sum(r['instructions'] for r in result['results']),kinds=dict(Counter(r['kind'] for r in result['results'])),composed_graphics_calls=len(result['graphics']),composed_graphics_instructions=sum(r['instructions'] for r in result['graphics']),composed_graphics_writes=sum(r['writes'] for r in result['graphics']),failures=result['failures'],checks=result['checks'],models={n:hashlib.sha256((ROOT/'treehouse-demo'/n).read_bytes()).hexdigest() for n in modules},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Each root starts with native cursor globals. All nested cursor changes, headers, draw operands and intrinsic instructions are generated without injecting child entry/return state. Graphics source buffers, row tables, shape inputs and REP splits remain per-draw fixtures; handle lookup work, a continuous pixel surface and shared CPU scheduling are not included.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
