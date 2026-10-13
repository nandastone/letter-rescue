"""Native full-frame prize comparisons and complete award/restart paths."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        for folder,activity in [('robot-win','boardgame'),('human-prize','nature')]:
            root=DATA/'research-rewards'/folder;ram=(root/'state/chooser.ram-0').read_bytes();ds=0x323f0;base=0x220;words=lambda at,n=1:list(struct.unpack_from('<'+str(n)+'h',ram,at));y,x=words(ds+0x2064,2)
            if activity=='boardgame':
                state=dict(mode=0,opponent=2,options=False,phase='result',player=words(ds+0x52d8)[0],nodes=words(ds+0x52c4,2),directions=words(ds+0x5734,2),balances=words(ds+0x5a0c,2),types=words(ds+0x59da,24),remaining=-1,rewards=[],message='',moving=None,played=True,optionsBackground=None,transfer=None,exchange=None,winner=1,loser=-1)
                page.evaluate("m=>{setScene('boardgame');boardgame.motion.cancel();Object.assign(boardgame,m);openPrizes('boardgame');}",state)
            else:
                cards=words(base+0x31690+6,16);state=dict(cards=[cards[:8],cards[8:]],secret=words(base+0x31690+0x992,2),remaining=words(ds+0x52ee,2),player=0,phase='won',winner=0,winStage='done',asked=[255,0],options=False,available=[])
                page.evaluate("m=>{setScene('nature');nature.mode='quiz';Object.assign(nature.quiz,m);openPrizes('nature');rewards.choices=[2,6,7,0,3,4];rewards.flash=1;}",state)
            page.evaluate('p=>{treehouseDemo.setPointer(...p);render();}',[x,y]);image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB');ref=Image.open(root/'state/chooser.png').convert('RGB');delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));report['pixels'][folder]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox());image.save(output/f'{folder}.png');delta.save(output/f'{folder}-difference.png');page.evaluate('rewards.active=false')
        def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
        check('every human prize is created once and resets when awarded again',"""(()=>{setScene('boardgame');for(let type=0;type<8;type++){Object.assign(boardgame,{options:false,phase:'result',winner:0,loser:-1});boardgame.motion.cancel();openPrizes('boardgame');rewards.choices=[type,0,1,2,3,4];rewards.choose(0);advance(2500);const o=resident.objects.find(o=>o.type===type);if(rewards.active||!o||o.state!==1)return false;o.state=3;Object.assign(boardgame,{phase:'result',winner:0});boardgame.motion.cancel();openPrizes('boardgame');rewards.choices=[type,0,1,2,3,4];rewards.choose(0);advance(2500);if(resident.objects.filter(o=>o.type===type).length!==1||o.state!==1)return false;}return true;})()""")
        check('six robot prizes reach shelf and restart same game settings',"""(()=>{for(let slot=0;slot<6;slot++){Object.assign(boardgame,{mode:1,options:false,phase:'result',winner:1,loser:-1,opponent:2});boardgame.motion.cancel();openPrizes('boardgame');rewards.choose(slot);advance(2500);if(rewards.active||!rewards.shelf[slot]||boardgame.winner!==-1||boardgame.mode!==1)return false;}return rewards.visited===7;})()""")
        check('next telescope visit shows collected shelf',"(()=>{setScene('telescope');return telescope===3&&rewards.visited===15;})()")
        check('telescope visits cover all four before repeating',"(()=>{rewards.visited=0;return new Set(Array.from({length:4},()=>rewards.nextView())).size===4;})()")
        check('cancel chooser exits activity without granting prize',"(()=>{setScene('boardgame');boardgame.motion.cancel();boardgame.winner=0;boardgame.phase='result';openPrizes('boardgame');const before=JSON.stringify(resident.objects);rewards.dismiss();return scene==='inside'&&!rewards.active&&JSON.stringify(resident.objects)===before;})()")
        report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values());browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
