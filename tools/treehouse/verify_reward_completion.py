"""Prize rendering and real transfer trajectory against native DOS captures."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);manifest=json.loads((ROOT/'testing/treehouse/reward-completion-poses.json').read_text(encoding='utf-8'));report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate('resident.ambientEnabled=false')
  for label,folder,activity in [('robot','robot-win','boardgame'),('human','human-prize','nature')]:
   ram=(DATA/'research-rewards'/folder/'state/chooser.ram-0').read_bytes();ds=0x323f0;words=lambda at,n=1:list(struct.unpack_from('<'+str(n)+'h',ram,at))
   if activity=='boardgame':
    state=dict(mode=0,opponent=2,options=False,phase='result',player=words(ds+0x52d8)[0],nodes=words(ds+0x52c4,2),directions=words(ds+0x5734,2),balances=words(ds+0x5a0c,2),types=words(ds+0x59da,24),remaining=-1,rewards=[],message='',moving=None,played=True,optionsBackground=None,transfer=None,exchange=None,winner=1,loser=-1)
    page.evaluate("m=>{setScene('boardgame');boardgame.motion.cancel();Object.assign(boardgame,m);openPrizes('boardgame');}",state)
   else:
    cards=words(0x318b0+6,16);state=dict(cards=[cards[:8],cards[8:]],secret=words(0x318b0+0x992,2),remaining=words(ds+0x52ee,2),player=0,phase='won',winner=0,winStage='done',asked=[255,0],options=False,available=[])
    page.evaluate("m=>{setScene('nature');nature.mode='quiz';Object.assign(nature.quiz,m);openPrizes('nature');}",state)
   inputs=manifest['branch_inputs'][label];page.evaluate('v=>{rewards.choices=v.choices;treehouseDemo.setPointer(...v.pointer);rewards.selected=0;}',inputs)
   for pose in manifest['branches'][label]:
    page.evaluate('m=>{rewards.phase=m.phase;rewards.sprite=m.sprite||null;rewards.arrived=null;if(m.phase.startsWith("burst-")){const id=Number(m.phase.slice(6)),a=rewards.art(0),[x,y]=rewards.center(a.shape,rewards.destination),shape=store.shape("th",id);rewards.sprite={id,palette:900,x:x+Math.floor(a.shape.w/2)-Math.floor(shape.w/2),y:y+Math.floor(a.shape.h/2)-Math.floor(shape.h/2)};}if(rewards.sprite?.id===923){const a=rewards.art(0),[x,y]=rewards.center(a.shape,rewards.destination);rewards.arrived={...a,x,y};}render();}',pose['model'])
    image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB');ref=Image.open(DATA/'research-reward-completion/native-b'/pose['native_image']).convert('RGB');delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));name=label+'-'+pose['name'];report['pixels'][name]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox());image.save(output/(name+'.png'));delta.save(output/(name+'-difference.png'))
   expected=[p['model']['sprite'] for p in manifest['branches'][label]if p['name'].startswith('flight-')]
   actual=page.evaluate("()=>{rewards.phase='transfer';const generator=rewards.transfer(),out=[];for(let i=0;i<100;i++){const step=generator.next();if(step.done)break;const s=rewards.sprite;if(s&&s.id!==923&&s.id!==924&&s.id!==925)out.push({id:s.id,palette:s.palette,x:s.x,y:s.y});if(s?.id===923)break;}return out;}")
   report['checks'].append(dict(name=label+' original complete flight path',passed=actual==expected))
   page.evaluate('rewards.active=false')
  def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
  check('click shortens presentation without cancelling award',"()=>{setScene('boardgame');boardgame.motion.cancel();Object.assign(boardgame,{options:false,winner:0,loser:-1,phase:'result'});openPrizes('boardgame');rewards.choose(0);advance(12);if(rewards.phase!=='present')return false;rewards.click(309,5);const active=rewards.active;advance();return active&&rewards.active&&rewards.phase==='transfer';}")
  check('Escape does not abandon a flying prize',"()=>{const before=rewards.phase;rewards.dismiss();return rewards.active&&rewards.phase===before;}")
  check('presentation sound uses original rate override',"()=>{rewards.active=false;openPrizes('boardgame');const calls=[],original=rewards.sound;rewards.sound=(...args)=>calls.push(args);rewards.choose(0);advance(12);rewards.sound=original;return calls.some(([id,rate])=>id===10024&&rate===22050);}")
  report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=report['passed'],checks=report['checks'],pixels=len(report['pixels']),failures={k:v for k,v in report['pixels'].items()if not v['exact']},errors=report['errors']),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
