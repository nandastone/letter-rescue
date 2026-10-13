"""Ordered full-frame comparison of original room/activity teleport stages."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
from collections import defaultdict
import numpy as np
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';NATIVE=DATA/'research-activity-transitions/native-a'

def model(path):
    r=path.read_bytes();ds=0x323f0;word=lambda at:struct.unpack_from('<H',r,at)[0]
    adjustment=0x2f3a0-16*word(ds+0x4a54);shared=16*word(ds+0x49e0)+adjustment
    objects=[]
    for i in range(word(ds+0x556c)):
        kind,state,inside,*rect=struct.unpack_from('<7h',r,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
    return dict(objects=objects,pose=word(ds+0x5688),minute=word(shared+0x9da),cloud=word(shared+0xb4),cloudX=word(shared+0xa18),sex=word(shared+0xa14))

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),errors=[],sequences={})
    driver=json.loads((NATIVE/'driver.json').read_text());timeline={r['run']:r for r in map(json.loads,(NATIVE/'frames.jsonl').read_text().splitlines())}
    with sync_playwright() as p:
        b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        for event in driver['events']:
            branch=event['branch'];name=branch.split('-')[0];returning=branch.endswith('-return');variant=['music','nature','theater','board'].index(name)
            native=[timeline[r['run']] for r in driver['rows'] if r['branch']==branch and r['run'] in timeline];lookup=defaultdict(list)
            for row in native:lookup[row['rgb_sha256']].append(row)
            m=model(NATIVE/'state'/f'{name}-before.ram-0');pointer_ram=(NATIVE/'state'/f"{name}-{'return-settled' if returning else 'inside'}.ram-0")
            py,px=struct.unpack_from('<hh',pointer_ram.read_bytes(),0x34454);m.update(variant=variant,returning=returning,pointer=[px,py])
            page.evaluate('''m=>{roomTravel=null;setScene('inside');animations=[];resident.active=null;resident.queue=[];resident.objectTask=null;resident.ambientAnimation=null;Object.assign(resident,{objects:m.objects,pose:m.pose,ambientEnabled:false,hungerDue:Infinity,fatigueDue:Infinity});character=m.sex?'girl':'boy';room.now=()=>new Date(1992,0,1,12,m.minute);room.date=room.now();room.cloud=m.cloud;room.cloudX=m.cloudX;room.cloudDue=Infinity;room.height=room.target=28;room.portraitFrame=null;for(const o of resident.objects)if(o.type===6)resident.setBounds(o,o.rect);balloon.hidden=!resident.objects.some(o=>o.type===6);balloon.due=Infinity;treehouseDemo.setPointer(...m.pointer);roomTravel={phase:'effect',effect:new RoomTransition(store,{variant:m.variant,returning:m.returning,tick,speak:theaterSpeech,stopSound:()=>audio.stopAll(),complete:()=>{roomTravel=null;}})};}''',m)
            generated=page.evaluate('''async()=>{const rows=[];let previous='';for(let i=0;i<1400&&roomTravel;i++){render();const rgb=new Uint8Array(192000);for(let j=0;j<64000;j++)rgb.set(screen.image.data.subarray(j*4,j*4+3),j*3);const sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');if(sha256!==previous){rows.push({tick,phase:roomTravel.effect.phase,frame:roomTravel.effect.actor?.frameUpdates,sha256,png:canvas.toDataURL().split(',')[1]});previous=sha256;}advance();}return rows;}''')
            states=[];last=-1;cache={}
            for index,g in enumerate(generated):
                matches=[r for r in lookup[g['sha256']] if r['run']>last];png=g.pop('png');g['exact']=bool(matches)
                if matches:last=matches[0]['run'];g['native_run']=last
                else:
                    image=Image.open(BytesIO(base64.b64decode(png))).convert('RGB');a=np.array(image);best=None
                    for row in native:
                        if row['run']<=last:continue
                        key=row['image']
                        if key not in cache:cache[key]=np.array(Image.open(NATIVE/key).convert('RGB'))
                        count=int(np.any(a!=cache[key],axis=2).sum())
                        if best is None or count<best[0]:best=(count,row,cache[key])
                    if best:
                        g['different_pixels']=best[0];g['nearest_native']=best[1]['run'];image.save(output/f'{branch}-{index}.png');ImageChops.difference(image,Image.fromarray(best[2])).save(output/f'{branch}-{index}-difference.png')
                states.append(g)
            report['sequences'][branch]=dict(states=states,exact=sum(s['exact']for s in states),total=len(states));print(branch,report['sequences'][branch]['exact'],len(states),flush=True)
        b.close()
    report['passed']=not report['errors'] and all(v['exact']==v['total']for v in report['sequences'].values());(output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS'if report['passed']else'FAIL')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
