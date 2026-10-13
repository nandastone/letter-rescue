"""Compare every generated basket/bird state with complete native frames in order."""
from pathlib import Path
import json,struct,hashlib,argparse
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parents[2]/'testing/output/treehouse';ROOT=P/'research-room-ordered-audit';N=ROOT/'native-basket'
parser=argparse.ArgumentParser();parser.add_argument('--html',type=Path,default=P/'completion-build/index.html');parser.add_argument('--output',type=Path,default=ROOT/'comparison');args=parser.parse_args();html=args.html;O=args.output;O.mkdir(parents=True,exist_ok=False)
r=(N/'state/before.ram-0').read_bytes();ds=0x323f0
word=lambda at:struct.unpack_from('<H',r,at)[0]
adjustment=0x2f3a0-16*word(ds+0x4a54);shared=16*word(ds+0x49e0)+adjustment
objects=[]
for i in range(word(ds+0x556c)):
 kind,state,inside,*rect=struct.unpack_from('<7h',r,ds+0x5830+20*i);objects.append(dict(type=kind,state=state,inside=bool(inside),rect=rect,due=0))
py,px=struct.unpack_from('<hh',r,ds+0x2064)
model=dict(objects=objects,pose=word(ds+0x5688),hunger=word(ds+0x5282),fatigue=word(ds+0x581c),minute=word(shared+0x9da),cloud=word(shared+0xb4),cloudX=word(shared+0xa18),sex=word(shared+0xa14),pointer=[px,py])
report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),initial_model=model,errors=[],states=[])
rows=[json.loads(l)for l in (N/'frames.jsonl').read_text().splitlines()];unique=[];last=''
for row in rows:
 if row['run']<1889:continue
 if row['image']!=last:unique.append(row);last=row['image']
targets=[np.array(Image.open(N/a['image']).convert('RGB'))for a in unique]
with sync_playwright()as p:
 b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
 page.evaluate('''m=>{setScene('inside');animations.length=0;resident.active=null;resident.queue=[];resident.objectMotion=null;resident.objectTask=null;Object.assign(resident,{pose:m.pose,hunger:m.hunger,fatigue:m.fatigue,objects:m.objects});character=m.sex?'girl':'boy';room.now=()=>new Date(1992,0,1,12,m.minute);room.date=room.now();room.portraitFrame=null;room.cloud=m.cloud;room.cloudX=m.cloudX;room.height=room.target=28;room.cloudDue=Infinity;resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;for(const o of resident.objects)if(o.type===6)resident.setBounds(o,o.rect);balloon.hidden=!resident.objects.some(o=>o.type===6);balloon.due=Infinity;treehouseDemo.setPointer(...m.pointer);render();}''',model)
 before=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB');before.save(O/'runtime-before.png');native=Image.open(N/'state/before.png').convert('RGB');report['baseline_difference']=int(np.any(np.array(before)!=np.array(native),axis=2).sum())
 page.evaluate('resident.begin(...pointer)');previous='';last_key='';monotonic=-1
 for tick in range(240):
  state=page.evaluate('''()=>({busy:resident.busy,basket:resident.objects.find(o=>o.type===10)?.state,sprite:resident.objectSprite?{x:resident.objectSprite.x,y:resident.objectSprite.y}:null})''')
  key=json.dumps(state)
  if key==last_key:
   page.evaluate('advance()');continue
  last_key=key;state['pixels']=page.evaluate('()=>{render();return Array.from(screen.image.data)}')
  a=np.array(state.pop('pixels'),dtype=np.uint8).reshape(200,320,4)[:,:,:3].copy();h=hashlib.sha256(a.tobytes()).hexdigest()
  if h!=previous:
   diffs=[int(np.any(a!=v,axis=2).sum())for v in targets];best=min(range(len(diffs)),key=diffs.__getitem__);exact=[i for i,d in enumerate(diffs)if d==0 and i>monotonic];matched=exact[0]if exact else None
   if matched is not None:monotonic=matched
   item=dict(tick=tick,**state,best_difference=diffs[best],best_native=unique[best],ordered_exact=matched is not None,ordered_native=unique[matched]if matched is not None else None);report['states'].append(item)
   Image.fromarray(a).save(O/f'runtime-{tick:03d}.png');Image.fromarray(np.where(np.any(a!=targets[best],axis=2)[:,:,None],targets[best],0).astype('uint8')).save(O/f'diff-{tick:03d}.png');previous=h
  if not state['busy']:break
  page.evaluate('advance()')
 b.close()
report['ordered_exact']=sum(v['ordered_exact']for v in report['states']);report['total']=len(report['states']);report['exact']=report['ordered_exact'];report['passed']=not report['errors'] and report['baseline_difference']==0 and report['exact']==report['total'];(O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k not in ['initial_model','states']},indent=2));print([(v['tick'],v['basket'],v['sprite'],v['best_difference'],v['best_native']['run'])for v in report['states']])
