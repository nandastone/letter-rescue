"""Original offer/ending frames compared with tick-driven browser sequences."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
import numpy as np
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';REF=DATA/'research-board-sequences'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[],full_timing_parity=False)
 index=json.loads((REF/'fixture-index.json').read_text(encoding='utf-8'))
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('boardgame')")
  for folder,mode,amounts,coins,message in [('money-choice',0,[12,11],[[0,0,0,1,0,2],[0,0,0,1,0,1]],'You\'ve been named "Kid of the Year!!"'),('chips-choice',1,[4,2],[],'You drove a neighbor to the store!'),('robot-winning-choice',0,[11,12],[[0,0,0,1,0,1],[0,0,0,1,0,2]],'You drove a neighbor to the store!')]:
   ram=(REF/folder/'state/before.ram-0').read_bytes();d=0x323f0;words=lambda at,n=1:list(struct.unpack_from('<'+str(n)+'h',ram,d+at));py,px=words(0x2064,2)
   model=dict(mode=mode,opponent=1 if mode else 2,levels=[0,0],options=False,phase='reward',player=words(0x52d8)[0],nodes=words(0x52c4,2),directions=words(0x5734,2),balances=words(0x5a0c,2),types=words(0x59da,24),remaining=0,rewards=amounts,rewardCoins=coins,message=message,moving=None,played=True,transfer=None,exchange=None,winner=-1,loser=-1,hintRed=False,offerStage=None,headerHidden=False,ending=False,carHidden=False,paymentHand=None)
   page.evaluate('m=>{boardgame.motion.cancel();Object.assign(boardgame,m);boardgame.resolvedNodeIcons=m.mode?{8:25}:{};}',model);page.evaluate('p=>treehouseDemo.setPointer(...p)',[px,py])
   raw=page.evaluate("()=>{const frames=[],seen=new Set(),save=()=>{render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data,phase:boardgame.phase,stage:boardgame.offerStage});}};save();boardgame.choose(0);save();for(let i=0;i<2200;i++){advance();save();if(!boardgame.motion.busy&&i>1000)break;}return frames;}")
   frames=[np.array(Image.open(BytesIO(base64.b64decode(f['data']))).convert('RGB'))for f in raw]
   # Distinct stable/source-timed stages produced by the real generator. Native drawing-only intermediate callbacks are recorded separately.
   skipped={'balance-updated'}if folder=='robot-winning-choice'else set()
   if skipped:report['partial_native_redraws']=[dict(name='robot-winning-choice-balance-updated',reason='Native callback captures units digit after update but seventh stack coin before draw; subsequent complete header-clear and victory frames compared. Source overlay3:19EB-1A91.')]
   ordered=[]
   for name,record in index[folder].items():
    if name in skipped:continue
    ref=np.array(Image.open(ROOT/record['image']).convert('RGB'));counts=[int(np.any(a!=ref,axis=2).sum())for a in frames];best=min(range(len(counts)),key=counts.__getitem__);label=folder+'-'+name
    ordered.append(raw[best]['tick'])
    report['pixels'][label]=dict(exact=counts[best]==0,different_pixels=counts[best],candidate_tick=raw[best]['tick'],phase=raw[best]['phase'],stage=raw[best]['stage']);Image.fromarray(frames[best]).save(output/(label+'.png'));ImageChops.difference(Image.fromarray(frames[best]),Image.fromarray(ref)).save(output/(label+'-difference.png'))
   report['checks'].append(dict(name=folder+' native stage order',passed=all(a<=b for a,b in zip(ordered,ordered[1:]))))
   report['checks'].append(dict(name=folder+' finishes',passed=page.evaluate('!boardgame.motion.busy&&boardgame.phase==="result"')))
  report['checks'].append(dict(name='three human car blinks at twelve-tick intervals',passed=page.evaluate('()=>{boardgame.winner=-1;boardgame.loser=-1;boardgame.motion.start(boardgame.motion.postRoll());const a=[];for(let i=0;i<6;i++){a.push(boardgame.carHidden);advance(12);}return JSON.stringify(a)==="[true,false,true,false,true,false]"&&boardgame.phase==="move"&&!boardgame.motion.busy;}')))
  report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
