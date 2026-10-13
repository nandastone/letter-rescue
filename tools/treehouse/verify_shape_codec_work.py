"""Compare ordered caption codec and expansion with offline native stage fixtures."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());meta=trace['frames_work'];stream=trace_path.parent/meta['path']
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('Missing same-DLL control')
    if hashlib.sha256(stream.read_bytes()).hexdigest()!=meta['sha256'] or meta['partial_final_calls']:raise ValueError('Frame stream differs')
    rows=[json.loads(s) for s in stream.read_text().splitlines()];results=[]
    modules=['resident-near-work.js','shape-codec-work.js','cpu-budget.js','work-runner.js'];sources={n:(ROOT/'treehouse-demo'/n).read_bytes() for n in modules}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for n,b in sources.items():page.add_script_tag(content=b.decode())
        for row in rows:
            if not row['conversion_source']:continue
            data=gzip.decompress((trace_path.parent/row['memory']['path']).read_bytes())
            if hashlib.sha256(data).hexdigest()!=row['memory']['sha256']:raise ValueError('RAM/path digest differs')
            result=page.evaluate('''({row,raw})=>{
              let index=0,recent=[];
              try{
                const bytes=Uint8Array.from(atob(raw),c=>c.charCodeAt(0)),size=row.memory.ram_size,addresses=new Uint32Array(bytes.buffer,row.memory.ram_images*size,row.instructions),residentBase=row.samples[0].address-0xc78a+0xd510;
                const assert=(ok,message)=>{if(!ok)throw new Error(message);},stage=offset=>{const i=row.stages.findIndex(s=>s.address===offset);assert(i>=0,'Missing stage');return {...row.stages[i],memory:bytes.slice((3+i)*size,(4+i)*size)};};
                const decode=stage(0xe03e),expand=stage(0xde10),freed=stage(0x64ce),memory=decode.memory.slice(),codec=new OriginalShapeCodecWork({memory,ds:row.ds}),a=decode.args;
                const input={rows:a[0],stride:a[1],length:a[2],source:a[3]+16*a[4],destination:a[5]+16*a[6]};
                function execute(generator,entry,exit){
                  index=addresses.indexOf(residentBase+entry);assert(index>=0,'Missing entry');const first=index,last=addresses.indexOf(residentBase+exit,index);assert(last>=index,'Missing return');
                  const runner=new OriginalWorkRunner(generator,{singleStrings:OriginalShapeCodecWork.singleStrings,onInstruction:label=>{
                    const actual=residentBase+parseInt(label.split(':')[1],16);assert(addresses[index]===actual,'Instruction '+index+' '+label+' != '+(addresses[index]-residentBase).toString(16));
                    index++;recent.push(label);if(recent.length>12)recent.shift();
                  }}),stop=runner.runSlice(new OriginalCpuBudget({cycles:100000000,left:0,maximum:100000000}));
                  assert(stop.kind==='complete','Codec did not complete');assert(index===last+1,'Wrong return boundary');return {instructions:runner.instructions,strings:runner.strings,value:stop.value};
                }
                const decoded=execute(codec.columnLz(input),0xe03e,0xe064),differences=[];let checked=0,changed=0;
                const lo=16*row.ss+expand.stack_low,hi=16*row.ss+row.sp;
                for(let i=0;i<size;i++){if(i>=lo&&i<hi)continue;checked++;if(memory[i]!==decode.memory[i])changed++;if(memory[i]!==expand.memory[i]&&differences.length<12)differences.push({address:i,actual:memory[i],expected:expand.memory[i]});}
                assert(!differences.length,'Decoded RAM differs '+JSON.stringify(differences));
                // Expansion starts from the independently captured next entry.
                // No expected pixels are passed to either generator.
                const expandedMemory=expand.memory.slice(),expander=new OriginalShapeCodecWork({memory:expandedMemory,ds:row.ds}),e=expand.args,header=e[3]+16*e[4],pixels=e[1]+16*e[2];
                const expanded=execute(expander.expandNibbles({header,pixels,paletteShift:e[0]}),0xde10,0xde77),v=new DataView(expand.memory.buffer),length=v.getUint16(header,true)*v.getUint16(header+2,true);
                for(let i=0;i<size;i++){
                  if(i>=pixels&&i<pixels+length)assert(expandedMemory[i]===freed.memory[i],'Expanded pixel differs at '+i);
                  else assert(expandedMemory[i]===expand.memory[i],'Expansion writes outside pixel extent at '+i);
                }
                return {passed:true,decoded,expanded,checkedBytes:checked,changedBytes:changed,pixels:length};
              }catch(e){return {passed:false,error:String(e),index,recent};}
            }''',dict(row=row,raw=base64.b64encode(data).decode()))
            results.append(dict(ordinal=row['ordinal'],**result))
            if not result['passed']:break
        checks=page.evaluate('''()=>{
          const checks=[],run=(g,slice=100000000)=>{
            const runner=new OriginalWorkRunner(g,{singleStrings:OriginalShapeCodecWork.singleStrings}),cpu=new OriginalCpuBudget({cycles:slice,left:0,maximum:slice});let stop;
            for(let guard=0;guard<100000;guard++){stop=runner.runSlice(cpu);if(stop.kind!=='exhausted')return stop;cpu.cycles=slice;}
            throw new Error('Focused run did not terminate');
          };
          function arena(){const memory=new Uint8Array(0x80000),v=new DataView(memory.buffer),ds=0x1000,base=16*ds;
            for(const [at,n] of [[0x1776,0x6000],[0x1778,0x6000],[0x177a,0x6800],[0x6000,0x7ff],[0x6800,0]])v.setUint16(base+at,n,true);
            return {memory,ds,v,base,codec:new OriginalShapeCodecWork({memory,ds})};}
          for(const [rows,stride] of [[1,1],[2,3],[3,5],[20,60]]){
            const length=rows*stride,values=Array.from({length},(_,i)=>(i*37)&255),packed=[];
            for(let i=0;i<length;i+=8)packed.push(255,...values.slice(i,i+8));
            for(const slice of [3,100000000]){
              const a=arena(),source=0x30000,destination=0x40000;a.memory.set(packed,source);
              const stop=run(a.codec.columnLz({rows,stride,length,source,destination}),slice);
              const ok=values.every((value,i)=>a.memory[destination+(i%rows)*stride+Math.floor(i/rows)]===value);
              checks.push({name:'Literal columns '+rows+'x'+stride+' budget '+slice,passed:stop.kind==='complete'&&stop.value===packed.length&&ok});
            }
          }
          for(const length of [2,4]){
            const a=arena();a.memory.set([1,0xab,3,0xbe],0x30000);const stop=run(a.codec.columnLz({rows:1,stride:length,length,source:0x30000,destination:0x40000}),2);
            checks.push({name:'Overlapping ring reference and clipped token '+length,passed:stop.value===4&&a.memory.slice(0x40000,0x40000+length).every(n=>n===0xab)});
          }
          for(const width of [1,2,3,7,8,15])for(const rows of [0,1,3]){
            const a=arena(),header=0x2ff00,pixels=0x30000,stride=Math.ceil(width/2),expected=[],packed=[];
            a.v.setUint16(header,rows,true);a.v.setUint16(header+2,width,true);a.v.setUint16(header+4,stride,true);
            for(let y=0;y<rows;y++)for(let x=0;x<width;x+=2){const hi=(x+y)%16,lo=x+1<width?(x+y+1)%16:15;packed.push(hi*16+lo);expected.push(hi?hi+96:0);if(x+1<width)expected.push(lo?lo+96:0);}
            a.memory.set(packed,pixels);const before=a.memory.slice(),stop=run(a.codec.expandNibbles({header,pixels,paletteShift:6}),3);
            checks.push({name:'In-place nibble expansion '+rows+'x'+width,passed:stop.kind==='complete'&&expected.every((n,i)=>a.memory[pixels+i]===n)&&a.memory.every((n,i)=>(i>=pixels&&i<pixels+rows*width)||n===before[i])});
          }
          return checks;
        }''')
        browser.close()
    expected=sum(bool(r['conversion_source']) for r in rows);passed=bool(results) and len(results)==expected and all(r['passed'] for r in results+checks)
    report=dict(passed=passed,expected_calls=expected,matching_calls=sum(r['passed'] for r in results),results=results,models={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Intrinsic E03E plus generated near allocation/free, and DE10 expansion, each from its captured entry state. All instruction addresses match. Decoder RAM compares at DE10 entry outside the observed active stack; expansion writes only its declared pixel extent and matches the later pre-free pixels. CPU queue/refills, converter wrapper, far allocation/resize and live integration remain separate.')
    report['checks']=checks
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return passed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['trace','control','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
