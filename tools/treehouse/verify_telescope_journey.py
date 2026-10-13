"""Native ordered telescope approach and return, driven through navigation."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
from collections import defaultdict
import numpy as np
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from verify_room_transitions import model
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';NATIVE=DATA/'research-telescope-navigation'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),errors=[],sequences={},checks=[])
    native=list(map(json.loads,(NATIVE/'frames.jsonl').read_text().splitlines()))
    driver=json.loads((NATIVE/'driver.json').read_text())
    with sync_playwright()as p:
        b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        cache={}
        for visit,destination in [(0,'telescope'),(0,'inside'),(1,'telescope'),(1,'inside')]:
            returning=destination=='inside';label=f"visit-{visit}-{'return'if returning else'approach'}"
            press=next(e for e in driver['events'] if e['branch']==label and e['action']=='press')
            end=next((e['run'] for e in driver['events'] if e['action']=='move' and e['run']>press['run']),native[-1]['run']+1)
            branch_native=[r for r in native if press['run']<=r['run']<end]
            lookup=defaultdict(list)
            for row in branch_native:lookup[row['rgb_sha256']].append(row)
            last=press['run']-1
            path=NATIVE/'state'/f"visit-{visit}-{'before-return'if returning else'before-click'}.ram-0";m=model(path);py,px=struct.unpack_from('<hh',path.read_bytes(),0x34454);m.update(pointer=[px,py],returning=returning)
            page.evaluate('''m=>{roomTravel=null;setScene(m.returning?'telescope':'inside');animations=[];resident.active=null;resident.queue=[];Object.assign(resident,{objects:m.objects,pose:m.pose,ambientEnabled:false,hungerDue:Infinity,fatigueDue:Infinity});character=m.sex?'girl':'boy';room.now=()=>new Date(1992,0,1,12,m.minute);room.date=room.now();room.cloud=m.cloud;room.cloudX=m.cloudX;room.cloudDue=Infinity;room.height=room.target=28;room.portraitFrame=null;for(const o of resident.objects)if(o.type===6)resident.setBounds(o,o.rect);balloon.hidden=!resident.objects.some(o=>o.type===6);balloon.due=Infinity;treehouseDemo.setPointer(...m.pointer);}''',m)
            page.evaluate('next=>navigateScene(next)',destination)
            generated=page.evaluate('''async()=>{const out=[];let previous='';for(let i=0;i<3000&&roomTravel;i++){render();const rgb=new Uint8Array(192000);for(let j=0;j<64000;j++)rgb.set(screen.image.data.subarray(j*4,j*4+3),j*3);const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');if(hash!==previous){out.push({tick,hash,png:canvas.toDataURL().split(',')[1]});previous=hash;}advance();}return out;}''')
            states=[]
            for i,g in enumerate(generated):
                png=g.pop('png');matches=[r for r in lookup[g['hash']]if r['run']>last];g['exact']=bool(matches)
                if matches:
                    last=matches[0]['run'];g['native_run']=last;g['native_tick']=matches[0]['original_tick']-press['tick']
                else:
                    im=Image.open(BytesIO(base64.b64decode(png))).convert('RGB');a=np.array(im);best=None
                    seen=set()
                    for row in branch_native:
                        if row['run']<=last:continue
                        key=row['image']
                        if key in seen:continue
                        seen.add(key)
                        if key not in cache:cache[key]=np.array(Image.open(NATIVE/key).convert('RGB'))
                        n=int(np.any(a!=cache[key],axis=2).sum())
                        if best is None or n<best[0]:best=n,row,cache[key]
                    if best:g['different_pixels']=best[0];g['nearest_native']=best[1]['run'];im.save(output/f'{label}-{i}.png');ImageChops.difference(im,Image.fromarray(best[2])).save(output/f'{label}-{i}-difference.png')
                states.append(g)
            report['sequences'][label]=dict(native_window=dict(start_run=press['run'],end_run_exclusive=end,input_tick=press['tick']),states=states,exact=sum(s['exact']for s in states),total=len(states));print(label,report['sequences'][label]['exact'],len(states),flush=True)
            report['checks'].append(dict(name=f'{label} completes through normal navigation',passed=page.evaluate('next=>scene===next&&!roomTravel',destination)))
        report['checks'].append(dict(name='return leaves native pose1',passed=page.evaluate('resident.pose===1')))
        b.close()
    report['passed']=not report['errors']and all(v['exact']==v['total']for v in report['sequences'].values())and all(v['passed']for v in report['checks']);(output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS'if report['passed']else'FAIL')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
