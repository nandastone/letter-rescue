"""Compare independently rendered character/object states with native RAM models."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate('resident.ambientEnabled=false')
        def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
        for folder,name in [('drag-a',f'{n}-done')for n in ['fruit17','fruit18','fruit19','fruit20','pillow8','nuts9','basket10']]+[('sleep-a','asleep')]:
            ref=DATA/'research-character'/folder/'state'/name;ram=ref.with_suffix('.ram-0').read_bytes();ds=0x323f0
            word=lambda at:struct.unpack_from('<H',ram,at)[0]
            adjustment=0x2f3a0-16*word(ds+0x4a54);shared=16*word(ds+0x49e0)+adjustment
            objects=[]
            for i in range(word(ds+0x556c)):
                kind,state,inside,*rect=struct.unpack_from('<7h',ram,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
            y,x=struct.unpack_from('<2h',ram,ds+0x2064)
            model=dict(pose=word(ds+0x5688),hunger=word(ds+0x5282),fatigue=word(ds+0x581c),objects=objects,cloud=word(shared+0xb4),cloudX=word(shared+0xa18),minute=word(shared+0x9da),sex=word(shared+0xa14),pointer=[x,y],wake=[word(ds+0x5526),word(ds+0x5592)])
            page.evaluate('''m=>{setScene('inside');resident.active=null;resident.queue=[];resident.objectMotion=null;Object.assign(resident,{pose:m.pose,hunger:m.hunger,fatigue:m.fatigue,objects:m.objects});character=m.sex?'girl':'boy';room.now=()=>new Date(1992,0,1,12,m.minute);room.date=room.now();room.portraitFrame=m.pose===4?931:null;room.cloud=m.cloud;room.cloudX=m.cloudX;resident.wakeTime=m.pose===4?new Date(1992,0,1,...m.wake):null;for(const o of resident.objects)if(o.type===6)resident.setBounds(o,o.rect);balloon.hidden=!resident.objects.some(o=>o.type===6);treehouseDemo.setPointer(...m.pointer);render();}''',model)
            if name=='nuts9-done':
                reference=Image.open(ref.with_suffix('.png')).convert('RGB')
                match=page.evaluate("""encoded=>{const target=bytes(encoded);resident.ambientAnimation=new Animation(store,'th',1403,1400,{startTick:0});pointerVisible=false;let best=64001,at=-1,frame=null;for(let n=0;n<1200;n++){resident.ambientAnimation.update(n);render();let diff=0;for(let i=0;i<64000;i++)if(screen.image.data[4*i]!==target[3*i]||screen.image.data[4*i+1]!==target[3*i+1]||screen.image.data[4*i+2]!==target[3*i+2])diff++;if(diff<best){best=diff;at=n;frame=canvas.toDataURL().split(',')[1];}if(!diff)break;}resident.ambientAnimation=null;return {best,at,frame};}""",base64.b64encode(reference.tobytes()).decode())
                report['squirrel_reference_tick']=match['at']
                page.evaluate("encoded=>{const img=new Image();img.onload=()=>ctx.drawImage(img,0,0);img.src='data:image/png;base64,'+encoded;}",match['frame'])
                page.wait_for_timeout(30)
            image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB');original=Image.open(ref.with_suffix('.png')).convert('RGB');delta=ImageChops.difference(image,original);n=sum(a!=b for a,b in zip(image.getdata(),original.getdata()));report['pixels'][name]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox(),native_model=model);image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        page.evaluate("resident.active=null;resident.ambientAnimation=null;resident.objectTask=null;resident.queue=[];resident.pose=0;resident.wakeTime=null;resident.hunger=3;resident.fatigue=1;room.now=()=>new Date(1992,0,1,12,39);room.leave();setScene('inside')")
        check('hungry character consumes apple',"(()=>{resident.offer(resident.create(18));advance(3000);return resident.hunger===1&&resident.fatigue===2&&!resident.objects.some(o=>o.type===18);})()")
        check('refused fruit returns through SCR callback',"(()=>{resident.offer(resident.create(20));advance(3000);const o=resident.objects.find(o=>o.type===20);return resident.hunger===1&&resident.pose===1&&o&&o.rect[1]===245&&o.rect[2]===142;})()")
        check('alternate pose resolves authored refusal script',"(()=>{resident.pose=2;resident.offer(resident.create(20));const id=resident.active.id;advance(3000);return id===20609&&resident.pose===1;})()")
        check('reused action relocates to alternate position',"(()=>{resident.pose=1;resident.action(31);const a=resident.active,ok=a.id===20531&&a.origin[0]===a.script.bounds[1]+59&&a.origin[1]===a.script.bounds[0]-3;advance(3000);return ok;})()")
        check('pillow refused while not tired',"(()=>{resident.pose=0;resident.fatigue=1;resident.offer(resident.create(8));advance(3000);return resident.pose===0&&resident.objects.some(o=>o.type===8)&&!resident.wakeTime;})()")
        check('pillow starts nap and scheduled wake',"(()=>{resident.fatigue=4;resident.offer(resident.create(8));advance(3000);return resident.pose===4&&resident.fatigue===1&&!resident.objects.some(o=>o.type===8)&&resident.wakeTime.getMinutes()===41;})()")
        check('sleeping character click stays asleep',"(()=>{resident.clickCharacter();advance(3000);return resident.pose===4;})()")
        check('activity entry interrupts sleep and returns pillow',"(()=>{setScene('music');advance(3000);return scene==='music'&&resident.pose===0&&resident.fatigue===4&&resident.objects.some(o=>o.type===8);})()")
        page.evaluate("setScene('inside');resident.pose=0;resident.fatigue=4;resident.offer(resident.create(8));advance(3000);room.now=()=>new Date(1992,0,1,12,41);advance(3000)")
        check('natural wake restores rested character','resident.pose===0&&resident.fatigue===1&&resident.objects.some(o=>o.type===8)')
        check('every available pose/action/character script renders',"(()=>{resident.hungerDue=resident.fatigueDue=Infinity;resident.wakeTime=null;for(const who of ['boy','girl'])for(const pose of [0,1,2])for(let action=1;action<32;action++){const id=20500+action+(resident.tables.exempt[action]?0:pose===1?200:pose===2?100:0);if(!store.data.scripts[who+':'+id])continue;character=who;resident.pose=pose;resident.active=null;resident.queue=[];resident.action(action);for(let t=0;t<3000&&(resident.active||resident.actionPreparation);t++){resident.update(resident.tick+1);if(t%30===0)resident.draw(new Surface());}if(resident.active||resident.actionPreparation)return false;}return true;})()")
        report['passed']=not report['errors']and all(v['exact']for v in report['pixels'].values())and all(c['passed']for c in report['checks']);browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=report['passed'],checks=report['checks'],pixels={k:{x:v[x]for x in ['exact','different_pixels','bounds']}for k,v in report['pixels'].items()},errors=report['errors']),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
