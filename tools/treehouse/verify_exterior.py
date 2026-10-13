"""Original exterior, credits, squirrel hollow and selected-friend behavior."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';REF=DATA/'research-exterior-audit'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
    with sync_playwright()as p:
        b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        def pointer(folder,name):
            r=(REF/folder/'state'/f'{name}.ram-0').read_bytes();py,px=struct.unpack_from('<hh',r,0x34454);page.evaluate('p=>treehouseDemo.setPointer(...p)',[px,py]);return r
        def snapshot(folder,name):
            pointer(folder,name);raw=page.evaluate('()=>{render();return canvas.toDataURL().split(",")[1];}');im=Image.open(BytesIO(base64.b64decode(raw))).convert('RGB');ref=Image.open(REF/folder/'state'/f'{name}.png').convert('RGB');diff=ImageChops.difference(im,ref);n=sum(a!=b for a,b in zip(im.getdata(),ref.getdata()));report['pixels'][name]=dict(exact=n==0,different_pixels=n,bounds=diff.getbbox());im.save(output/f'{name}.png');diff.save(output/f'{name}-difference.png')
        def check(name,code):
            try:report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
            except Exception as e:report['checks'].append(dict(name=name,passed=False,error=str(e)))
        for i in range(8):
            page.evaluate('i=>{exterior.credit=i;}',i)
            snapshot('credits-followup','credit4-settled')if i==4 else snapshot('credits-window',f'credit-{i}')
        r=pointer('native','outside');ds=0x323f0;word=lambda at:struct.unpack_from('<H',r,at)[0];shared=16*word(ds+0x49e0)+0x2f3a0-16*word(ds+0x4a54)
        objects=[]
        for i in range(word(ds+0x556c)):
            kind,state,inside,*rect=struct.unpack_from('<7h',r,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
        page.evaluate('m=>{resident.selected=true;resident.ambientEnabled=false;resident.objects=m.objects;resident.hungerDue=resident.fatigueDue=Infinity;room.cloud=m.cloud;character=m.sex?"girl":"boy";setScene("outside");}',dict(objects=objects,cloud=word(shared+0xb4),sex=word(shared+0xa14)))
        snapshot('native','outside')
        check('selected ladder returns directly without greeting','()=>{activate(270,130,"test");return scene==="inside"&&!entering&&!roomTravel;}')
        page.evaluate('setScene("outside");activate(218,142,"test")');snapshot('native','hollow')
        for i in range(1,4):
            page.evaluate('()=>{activate(229,145,"test");for(let i=0;i<1000&&resident.busy;i++)advance();}');snapshot('native',f'nut{i}')
        check('hollow accepts exactly three nuts per visit','()=>{activate(229,145,"test");return exterior.nuts.length===3&&!resident.busy;}')
        for name,x,y in [('squirrel-one',158,95),('squirrel-two',126,113)]:
            page.evaluate('p=>{activate(...p,"test");for(let i=0;i<1000&&resident.busy;i++)advance();}',[x,y]);snapshot('native',name)
        check('hollow sign waits for its original voice and stops','()=>{activate(180,40,"test");const active=exterior.signWaiting;advance(1000);return active&&!exterior.signWaiting&&!resident.busy;}')
        check('outside hollow border exits to selected exterior','()=>{activate(10,190,"test");return scene==="outside"&&resident.selected&&!animations.length;}')
        check('returning to hollow resets only its local nuts','()=>{const before=JSON.stringify(resident.objects);activate(218,142,"test");const ok=exterior.nuts.length===0&&JSON.stringify(resident.objects)===before;activate(10,190,"test");return ok;}')
        check('exterior cloud cycles all seven original shapes','()=>{const start=room.cloud;for(let i=0;i<7;i++)activate(80,25,"test");return room.cloud===start;}')
        for label,x,y,script in [('sun',25,18,1301),('birdhouse',150,90,1060),('pond',50,190,1000)]:
            check(f'{label} selects its original exterior script',f'()=>{{activate({x},{y},"test");const id=resident.ambientAnimation?.id;for(let i=0;i<3000&&resident.busy;i++)advance();return id==={script}&&!resident.busy;}}')
        check('pond cycles and resets on exterior reentry','()=>{activate(50,190,"test");const a=resident.ambientAnimation?.id;advance(3000);activate(50,190,"test");const b=resident.ambientAnimation?.id;advance(3000);setScene("inside");setScene("outside");return a===1001&&b===1002&&resident.outsideCycle===0;}')
        check('window click uses entrance status and retreat scripts','()=>{resident.hunger=resident.fatigue=1;const ids=[];activate(237,50,"test");for(let i=0;i<4000&&resident.busy;i++){const id=resident.windowAnimation?.id;if(ids.at(-1)!==id)ids.push(id);advance();}return JSON.stringify(ids)==="[20400,20407,20401]"&&!resident.windowAnimation;}')
        # Main 5578/564E retain the old need while the window warning plays;
        # the increment follows its synchronous return at 5636/5745.
        check('exterior hunger increments after its warning completes','()=>{resident.hunger=3;resident.fatigue=1;resident.hungerDue=tick+1;resident.fatigueDue=Infinity;advance();const ok=resident.hunger===3&&resident.busy&&resident.hungerDue===tick+7200;advance(4000);return ok&&!resident.busy&&resident.hunger===4;}')
        check('exterior fatigue increments after its warning completes','()=>{resident.fatigue=3;resident.hunger=1;resident.fatigueDue=tick+1;resident.hungerDue=Infinity;advance();const ok=resident.fatigue===3&&resident.busy&&resident.fatigueDue===tick+14400;advance(4000);return ok&&!resident.busy&&resident.fatigue===4;}')
        check('healthy exterior reminder uses independent three-minute timer','()=>{resident.fatigue=resident.hunger=1;resident.hungerDue=resident.fatigueDue=Infinity;resident.windowDue=tick+1;advance();const ok=resident.windowAnimation?.id===20400;for(let i=0;i<4000&&resident.busy;i++)advance();return ok&&resident.windowDue===tick+10800;}')
        check('leaving sleeping friend preserves nap and window plays two snores','()=>{setScene("inside");room.now=()=>new Date(1992,0,1,12,0);resident.pose=4;resident.wakeTime=new Date(1992,0,1,12,2);resident.create(8,false);navigateScene("outside");const sleeping=scene==="outside"&&resident.pose===4;const old=resident.sound,sounds=[];resident.sound=id=>{sounds.push(id);return 0;};activate(237,50,"test");advance(100);resident.sound=old;return sleeping&&resident.pose===4&&JSON.stringify(sounds)==="[10123,10123]";}')
        check('timed outdoor wake restores indoor pillow without body animation','()=>{room.now=()=>new Date(1992,0,1,12,3);advance();for(let i=0;i<4000&&resident.busy;i++)advance();return resident.pose===0&&!resident.busy&&resident.fatigue===1&&!resident.wakeTime&&resident.objects.some(o=>o.type===8&&o.inside);}')
        check('first credit lasts600 ticks and following credits360','()=>{resident.selected=false;setScene("outside");exterior.fresh(tick);advance(599);const a=exterior.credit===0;advance();const b=exterior.credit===1;advance(359);const c=exterior.credit===1;advance();return a&&b&&c&&exterior.credit===2;}')
        check('sleeping friend does not freeze yard ambient events','()=>{const original=gameplayRandom.int,results=[];for(let choice=0;choice<8;choice++){resident.selected=true;setScene("outside");resident.pose=4;room.now=()=>new Date(1992,0,1,12,0);resident.wakeTime=new Date(1992,0,1,12,3);resident.ambientEnabled=true;resident.ambientDue=tick+1;resident.longDue=Infinity;gameplayRandom.int=function(n){return n===7?choice:original.call(this,n);};advance(2);gameplayRandom.int=original;const serviced=resident.busy;resident.ambientEnabled=false;for(let i=0;i<4000&&resident.busy;i++)advance();results.push({choice,serviced,finished:!resident.busy,scheduled:resident.ambientDue>tick,sleeping:resident.pose===4});}window.sleepAmbientCases=results;return results.every(r=>r.finished&&r.sleeping&&(r.choice===7?!r.serviced:r.serviced&&r.scheduled));}')
        check('indoor shelf nut cannot start a squirrel in the yard','()=>{const nut=resident.create(11);nut.rect=[178,232,187,244];nut.due=tick+1;advance(2);return !resident.ambientAnimation&&nut.inside;}')
        check('hollow wake restores pillow without an indoor actor','()=>{navigateScene("hollow");room.now=()=>new Date(1992,0,1,12,4);advance();for(let i=0;i<4000&&resident.busy;i++){if(resident.active)return false;advance();}return scene==="hollow"&&resident.pose===0&&!resident.wakeTime&&resident.objects.some(o=>o.type===8&&o.inside);}')
        check('unselected title hides retained yard objects and ignores their hits','()=>{resident.selected=false;resident.pose=0;setScene("outside");const o=resident.create(2,false);o.rect=[120,180,140,200];render();const before=new Uint32Array(screen.pixels);o.hidden=true;render();const hidden=screen.pixels.every((p,i)=>p===before[i]);o.hidden=false;activate(190,130,"test");return hidden&&!resident.drag&&!resident.busy;}')
        check('outside need announcement precedes an expired ambient event','()=>{resident.selected=true;setScene("outside");resident.pose=0;resident.ambientEnabled=true;resident.ambientDue=tick;resident.hunger=1;resident.fatigue=3;resident.hungerDue=Infinity;resident.fatigueDue=tick+1;advance();const ok=!!resident.windowAnimation&&!resident.ambientAnimation;resident.ambientEnabled=false;return ok;}')
        report['sleep_ambient_cases']=page.evaluate('sleepAmbientCases');
        report['passed']=not report['errors']and all(v['exact']for v in report['pixels'].values())and all(v['passed']for v in report['checks']);b.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
