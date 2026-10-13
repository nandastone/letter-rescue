"""Original maze victory and board reminder frames through runtime generators."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
 with sync_playwright()as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('maze');maze.cancel()")
  def compare(name,path):
   page.evaluate('render()');im=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB');ref=Image.open(path).convert('RGB');delta=ImageChops.difference(im,ref);n=sum(a!=b for a,b in zip(im.getdata(),ref.getdata()));report['pixels'][name]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox());im.save(output/(name+'.png'));delta.save(output/(name+'-difference.png'))
  source=DATA/'research-maze-guidance/idle-controls/state';r=(source/'after-01.ram-0').read_bytes();w=lambda o:struct.unpack_from('<H',r,0x318b0+o)[0];y,x,_,_=struct.unpack_from('<4h',r,0x318b0+0x9ba);py,px=struct.unpack_from('<hh',r,0x323f0+0x2064)
  page.evaluate('m=>{Object.assign(maze,m);maze.wrong=new Set();maze.eliminated=new Set();treehouseDemo.setPointer(m.px,m.py);maze.run(maze.winHint());}',dict(node=9,phase='win',songs=list(struct.unpack_from('<6H',r,0x318b0+0x922)),secret=w(0x9ae),earned=r[0x318b0+0x9e6],actor=[y+40,x+17],actorAnimation=3,actorFrame=0,frog=True,frogPoint=[150,130],frogAnimation=3,frogFrame=0,px=px,py=py,roller=None,falling=None,departureSong=None))
  for label,step in [('after-01',0),('after-25',18),('after-40',12),('after-60',18)]:
   page.evaluate('n=>advance(n)',step);compare('maze-win-'+label,source/(label+'.png'))
  source=DATA/'research-board-sequences/money-choice/state';r=(source/'before.ram-0').read_bytes();w=lambda o,n=1:list(struct.unpack_from('<'+str(n)+'h',r,0x323f0+o));py,px=w(0x2064,2)
  model=dict(mode=0,opponent=2,levels=[0,0],options=False,phase='reward',player=w(0x52d8)[0],nodes=w(0x52c4,2),directions=w(0x5734,2),balances=w(0x5a0c,2),types=w(0x59da,24),remaining=0,rewards=[12,11],rewardCoins=[[0,0,0,1,0,2],[0,0,0,1,0,1]],message='You\'ve been named "Kid of the Year!!"',moving=None,played=True,transfer=None,exchange=None,winner=-1,loser=-1,hintRed=False,offerStage=None,headerHidden=False,ending=False,carHidden=False,paymentHand=None,nodeHint=-1)
  page.evaluate('m=>{setScene("boardgame");boardgame.motion.cancel();Object.assign(boardgame,m);boardgame.resolvedNodeIcons={};}',model);page.evaluate('v=>treehouseDemo.setPointer(...v)',[px,py]);page.evaluate('boardgame.motion.start(boardgame.motion.reminder("reward"))')
  root=DATA/'research-board-final-audit/offer-reminder';rows=json.loads((root/'unique.json').read_text(encoding='utf-8'))
  for stamp,step in [(7727,0),(7739,12)]:
   page.evaluate('n=>advance(n)',step);row=next(v for v in rows if v['original_tick']==stamp);compare('board-offer-'+str(stamp),root/row['image'])
  report['passed']=not report['errors']and all(v['exact']for v in report['pixels'].values());b.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
