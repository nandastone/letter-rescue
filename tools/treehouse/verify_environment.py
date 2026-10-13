"""Compare generated room animation states with complete native RGB frames.

This proves frame membership, not native ordering or timer alignment. Both cursor
visibility states are evaluated at native presentation boundaries.
"""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];REFERENCE=ROOT/'testing/output/treehouse/research-room-environment'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);rows=[json.loads(r)for r in (REFERENCE/'frames.jsonl').read_text().splitlines()];run=json.loads((REFERENCE/'run.json').read_text());report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),comparison=__doc__,sequences={},errors=[])
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate('resident.ambientEnabled=false')
        for action in run['actions']:
            name=action['name'];r=(REFERENCE/f'state/{name}-before.ram-0').read_bytes();ds=0x323f0;word=lambda at:struct.unpack_from('<H',r,at)[0];adjustment=0x2f3a0-16*word(ds+0x4a54);shared=16*word(ds+0x49e0)+adjustment;py,px=struct.unpack_from('<hh',r,ds+0x2064)
            objects=[]
            for i in range(word(ds+0x556c)):
                kind,state,inside,*rect=struct.unpack_from('<7h',r,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
            page.evaluate('''m=>{setScene('inside');resident.objects=m.objects;resident.pose=m.pose;resident.hungerDue=resident.fatigueDue=Infinity;room.now=()=>new Date(1992,0,1,12,m.minute);room.date=room.now();room.cloud=m.cloud;room.cloudX=m.cloudX;room.height=room.target=28;room.portraitFrame=null;for(const o of resident.objects)if(o.type===6)resident.setBounds(o,o.rect);balloon.due=Infinity;treehouseDemo.setPointer(...m.pointer);}''',dict(objects=objects,pose=word(ds+0x5688),minute=word(shared+0x9da),cloud=word(shared+0xb4),cloudX=word(shared+0xa18),pointer=[px,py]))
            native={row['rgb_sha256']for row in rows[action['callback']+30:action['callback']+931]}
            states=page.evaluate('''async name=>{room.interact(name);const out=[];let previous='';for(let i=0;i<1000;i++){const key=balloon.y+':'+(room.environment?.frameUpdates||0)+':'+Number(room.chirpUntil>tick)+':'+Math.floor((tick-room.chirpStart)/8)%2;if(key!==previous){const hashes=[];for(const visible of [false,true]){pointerVisible=visible;render();const rgb=new Uint8Array(192000);for(let p=0;p<64000;p++)rgb.set(screen.image.data.subarray(p*4,p*4+3),p*3);hashes.push(Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join(''));}out.push({tick,key,hashes});previous=key;}advance();if(!room.busy)break;}return out;}''',name)
            for state in states:state['exact']=any(h in native for h in state['hashes'])
            report['sequences'][name]=dict(exact=sum(s['exact']for s in states),total=len(states),states=states)
        report['passed']=not report['errors']and all(s['exact']==s['total']for s in report['sequences'].values());browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'sequences':{k:{a:v[a]for a in ['exact','total']}for k,v in report['sequences'].items()}},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
