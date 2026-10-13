"""Ordered original-frame comparison for squirrel flights and yard animations."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
from collections import defaultdict
import numpy as np
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';REF=DATA/'research-exterior-audit'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),errors=[],sequences={})
    timelines={name:list(map(json.loads,(REF/name/'frames.jsonl').read_text().splitlines()))for name in ['native','credits-window']}
    ranges={}
    for folder in timelines:
        run=json.loads((REF/folder/'run.json').read_text());start=end=1800
        for a in run['actions']:
            end+=a['frames']
            if 'capture'in a:ranges[(folder,a['capture'])]=(start,end);start=end
    with sync_playwright()as p:
        b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        r=(REF/'native/state/outside.ram-0').read_bytes();ds=0x323f0;w=lambda at:struct.unpack_from('<H',r,at)[0];shared=16*w(ds+0x49e0)+0x2f3a0-16*w(ds+0x4a54);objects=[]
        for i in range(w(ds+0x556c)):
            kind,state,inside,*rect=struct.unpack_from('<7h',r,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
        page.evaluate('m=>{resident.objects=m.objects;resident.selected=true;resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;resident.windowDue=Infinity;room.cloud=m.cloud;character=m.sex?"girl":"boy";setScene("hollow");}',dict(objects=objects,cloud=w(shared+0xb4),sex=w(shared+0xa14)))
        cases=[('native',f'nut{i}',f'activate(229,145,"test")')for i in range(1,4)]
        cases += [('native','squirrel-one','activate(158,95,"test")'),('native','squirrel-two','activate(126,113,"test")'),('native','sun-after','setScene("outside");activate(25,18,"test")'),('native','birdhouse-after','activate(150,90,"test")'),('native','pond-after','activate(50,190,"test")'),('credits-window','window-active','resident.hunger=resident.fatigue=1;activate(237,50,"test")')]
        for folder,name,action in cases:
            # The window reference restores a separate yard snapshot before any
            # pond interaction; do not carry the prior fixture's resting frog.
            if folder=='credits-window':page.evaluate('setScene("outside")')
            rr=(REF/folder/'state'/f'{name}.ram-0').read_bytes();py,px=struct.unpack_from('<hh',rr,ds+0x2064);page.evaluate('p=>treehouseDemo.setPointer(...p)',[px,py]);page.evaluate(action)
            generated=page.evaluate('''async()=>{const out=[];let previous='';for(let i=0;i<4000&&resident.busy;i++){render();const rgb=new Uint8Array(192000);for(let j=0;j<64000;j++)rgb.set(screen.image.data.subarray(j*4,j*4+3),j*3);const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');if(hash!==previous){out.push({tick,hash,png:canvas.toDataURL().split(',')[1]});previous=hash;}advance();}return out;}''')
            start,end=ranges[(folder,name)]
            if name=='window-active':end=ranges[(folder,'window-ended')][1]
            native=[r for r in timelines[folder]if start<=r['run']<=end];lookup=defaultdict(list)
            for row in native:lookup[row['rgb_sha256']].append(row)
            last=-1;states=[];cache={}
            for index,g in enumerate(generated):
                png=g.pop('png');matches=[r for r in lookup[g['hash']]if r['run']>last];g['exact']=bool(matches)
                if matches:last=matches[0]['run'];g['native_run']=last
                else:
                    im=Image.open(BytesIO(base64.b64decode(png))).convert('RGB');a=np.array(im);best=None
                    for row in native:
                        if row['run']<=last:continue
                        key=row['image']
                        if key not in cache:cache[key]=np.array(Image.open(REF/folder/key).convert('RGB'))
                        n=int(np.any(a!=cache[key],axis=2).sum())
                        if best is None or n<best[0]:best=n,row,cache[key]
                    if best:g['different_pixels']=best[0];g['nearest_native']=best[1]['run'];im.save(output/f'{name}-{index}.png');ImageChops.difference(im,Image.fromarray(best[2])).save(output/f'{name}-{index}-difference.png')
                states.append(g)
            report['sequences'][name]=dict(states=states,exact=sum(s['exact']for s in states),total=len(states));print(name,report['sequences'][name]['exact'],len(states),flush=True)
        b.close()
    report['passed']=not report['errors']and all(v['exact']==v['total']for v in report['sequences'].values());(output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS'if report['passed']else'FAIL')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
