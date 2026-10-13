"""Compare source-derived VGA copies against native pixels and intrinsic work."""
from pathlib import Path
from collections import Counter
import argparse,base64,gzip,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());meta=trace['blits']
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    path=trace_path.parent/meta['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Surface-copy digest differs')
    rows=[json.loads(s) for s in path.read_text().splitlines()];results=[];modes=Counter()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/surface-copy-work.js'))
        page.evaluate('''()=>{
          window.driveSurface=(input,slices=null)=>{
            const g=OriginalSurfaceCopyWork.run(input),counts={},actions=[];let hash=2166136261,next=g.next(),slice=0;
            while(!next.done){const step=next.value;let answer;
              if(typeof step==='string'){
                const at=parseInt(step.split(':')[1],16);counts[at]=(counts[at]||0)+1;
                for(let shift=0;shift<32;shift+=8)hash=Math.imul(hash^((at>>>shift)&255),16777619)>>>0;
              }else if(step.call==='rep-move-words'){
                if(slices){const native=slices[slice++];if(!native||native.address!==step.address||native.remaining!==step.remaining)throw new Error('REP entry operands differ at slice '+(slice-1));answer=Math.min(step.remaining,Math.max(1,native.budget));}
                else answer=step.remaining;
              }else actions.push(step.call);
              next=g.next(answer);
            }
            if(slices&&slice!==slices.length)throw new Error('Unconsumed REP slices');
            return {...next.value,counts,hash,actions};
          };
        }''')
        for row in rows:
            payload=b''
            if row['copied']:
                payload=gzip.decompress((trace_path.parent/row['pixels']['path']).read_bytes())
                if hashlib.sha256(payload).hexdigest()!=row['pixels']['sha256']:raise ValueError('Pixel fixture digest differs')
                if len(payload)!=row['source_size']+2*row['destination_size']:raise ValueError('Pixel fixture length differs')
            inputs={k:row[k] for k in ['mode','context','source_id','destination_id','source','destination','source_rect','destination_rect','source_rows','destination_rows']}
            source_size=row['source_size'];destination_size=row['destination_size']
            inputs.update(sourcePixels=list(payload[:source_size]),beforePixels=list(payload[source_size:source_size+destination_size]))
            actual=page.evaluate('''({input,slices,expected})=>{
              try{
                const r=driveSurface(input,slices),pixels=Uint8Array.from(atob(expected),c=>c.charCodeAt(0));let different=0,first=[];
                if(r.copied){if(pixels.length!==r.pixels.length)throw new Error('Output buffer size differs');for(let i=0;i<pixels.length;i++)if(pixels[i]!==r.pixels[i]){different++;if(first.length<10)first.push({at:i,expected:pixels[i],actual:r.pixels[i]});}}
                const {pixels:ignored,...rest}=r;return {...rest,different,first};
              }catch(e){return {error:String(e)};}
            }''',dict(input=inputs,slices=row['slices'],expected=base64.b64encode(payload[source_size+destination_size:]).decode()))
            diff={}
            if 'error' not in actual:
                for at in actual['counts'].keys()|row['counts'].keys():
                    if actual['counts'].get(at,0)!=row['counts'].get(at,0):diff[at]=dict(expected=row['counts'].get(at,0),actual=actual['counts'].get(at,0))
                passed=not diff and actual['hash']==row['path_hash'] and actual['copied']==bool(row['copied']) and not actual['different']
            else:passed=False
            results.append(dict(ordinal=row['ordinal'],passed=passed,differences=diff,actual=actual if not passed else {k:actual[k] for k in ['copied','strings','writes','different']},instructions=sum(actual.get('counts',{}).values()),rep_dispatches=len(row['slices'])))
            modes[row['mode']]+=1
            if not passed:break
        checks=page.evaluate('''()=>{
          const checks=[],surface=(base=0x1000)=>[0,base,0,0,6,8,8,0,0,0,6,8,0,0,6,8],rows=Array.from({length:6},(_,i)=>i*8),original=Array.from({length:48},(_,i)=>(i*13+7)&255);
          for(const same of [false,true])for(const mode of [0,1,2,3,4,5,6,7]){
            const destination=same?original.slice():original.map(v=>v^0x5a),expected=destination.slice(),input={mode,context:2,source_id:1,destination_id:2,source:surface(),destination:surface(same?0x1000:0x2000),source_rect:[0,0,3,5],destination_rect:[1,2,4,7],source_rows:rows,destination_rows:rows,sourcePixels:original,beforePixels:destination};
            for(let y=0;y<3;y++)for(let x=0;x<5;x++){const at=(y+1)*8+x+2,a=original[y*8+x]^(mode&4?255:0),b=destination[at];expected[at]=(mode&3)===0?original[y*8+x]:(mode&3)===1?a&b:(mode&3)===2?a|b:a^b;}
            const r=driveSurface(input);checks.push({name:(same?'overlap backward':'separate surfaces')+' mode '+mode,passed:Array.from(r.pixels).every((v,i)=>v===expected[i])&&r.writes===15});
          }
          const clipped={mode:0,context:2,source_id:1,destination_id:2,source:surface(),destination:surface(0x2000),source_rect:[-1,-2,3,4],destination_rect:[0,0,4,6],source_rows:rows,destination_rows:rows,sourcePixels:original,beforePixels:Array(48).fill(0)};
          const r=driveSurface(clipped),expected=Array(48).fill(0);for(let y=0;y<3;y++)for(let x=0;x<4;x++)expected[(y+1)*8+x+2]=original[y*8+x];
          checks.push({name:'source clipping shifts destination origin',passed:r.width===4&&r.height===3&&Array.from(r.pixels).every((v,i)=>v===expected[i])});
          const empty=driveSurface({...clipped,destination_rect:[20,20,24,26]});checks.push({name:'fully outside copy makes no writes',passed:!empty.copied&&empty.writes===0});
          const active=surface(0x2000);active.splice(12,4,2,3,4,6);const clip=driveSurface({...clipped,source_rect:[0,0,6,8],destination_rect:[0,0,6,8],destination:active});
          checks.push({name:'active destination clip limits copy',passed:clip.width===3&&clip.height===2&&clip.writes===6&&clip.pixels[19]===original[19]});
          const shared=new Uint8Array(48),generator=OriginalSurfaceCopyWork.run({...clipped,source_rect:[0,0,2,4],destination_rect:[0,0,2,4],destinationPixels:shared});let step=generator.next(),firstRep=false,visible=false;
          while(!step.done){
            if(step.value.call==='rep-move-words'){
              step=generator.next(firstRep?step.value.remaining:1);
              if(!firstRep){firstRep=true;visible=shared[0]===original[0]&&shared[1]===original[1]&&shared[2]===0&&!step.done;}
            }else step=generator.next();
          }
          checks.push({name:'partial REP writes are visible in shared buffer before completion',passed:visible&&step.value.pixels===shared&&shared[11]===original[11]});
          return checks;
        }''');browser.close()
    report=dict(passed=len(results)==meta['calls'] and all(r['passed'] for r in results+checks),full_cpu_scheduling_parity=False,calls=len(results),matching_calls=sum(r['passed'] for r in results),instructions=sum(r['instructions'] for r in results),rep_dispatches=sum(r['rep_dispatches'] for r in results),pixels_written=sum(r['actual'].get('writes',0) for r in results),modes=dict(modes),failures=[r for r in results if not r['passed']],checks=checks,model_sha256=hashlib.sha256((ROOT/'treehouse-demo/surface-copy-work.js').read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Every captured VGA surface copy: generated clipping, overlap traversal, pixel output, intrinsic instruction counts and ordered hash. REP dispatch budgets are explicit fixtures; cursor preparation/restoration helpers are excluded, and pixel snapshots surround the copy loop after/before those helpers. No captured destination output is used to generate writes. This is not live scanout or full execution-clock parity.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.trace,a.control,a.output) else 1)
