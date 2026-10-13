"""Nature idle reminder stages and native seeded question generation."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
import numpy as np
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse';REF=DATA/'research-nature-final-audit'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
 index=json.loads((REF/'fixture-index.json').read_text(encoding='utf-8'))
 with sync_playwright()as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('nature');nature.mode='quiz'")
  for case in ['ready-idle','question-idle','guess-idle']:
   run=json.loads((REF/case/'run.json').read_text(encoding='utf-8'));r=(DATA/run['origin']).with_suffix('.ram-0').read_bytes();u=lambda at:struct.unpack_from('<H',r,at)[0];cards=struct.unpack_from('<16H',r,0x318b6);py,px=struct.unpack_from('<hh',r,0x34454)
   model=dict(cards=[cards[:8],cards[8:]],secret=list(struct.unpack_from('<2H',r,0x32242)),player=u(0x37640),asked=list(struct.unpack_from('<2H',r,0x376cc)),remaining=list(struct.unpack_from('<2H',r,0x376de)),available=[i for i in range(8)if u(0x37692+2*i)],pointer=[px,py],options=False,phase='ready'if case=='ready-idle'else'question',guessing=case=='guess-idle',waiting=case=='guess-idle',visibleQuestions=[]if case=='guess-idle'else None)
   page.evaluate('m=>{nature.quiz=new NatureQuiz(nature,{character:()=>character,speak:theaterSpeech});Object.assign(nature.quiz,m,{tick});treehouseDemo.setPointer(...m.pointer);}',model)
   rows=page.evaluate('()=>{const q=nature.quiz,rows=[],save=()=>{render();const png=canvas.toDataURL().split(",")[1];if(rows.at(-1)?.png!==png)rows.push({tick,png});};save();q.run(q.reminder());save();for(let i=0;i<150&&q.busy;i++){advance();save();}return rows;}')
   frames=[np.array(Image.open(BytesIO(base64.b64decode(v['png']))).convert('RGB'))for v in rows];previous=0
   for item in [v for v in index if v['name']==case]:
    ref=np.array(Image.open(REF/item['file']).convert('RGB'));counts=[int(np.any(a!=ref,axis=2).sum())if i>=previous else 64001 for i,a in enumerate(frames)];best=min(range(len(counts)),key=counts.__getitem__);previous=best;label=case+'-'+item['label'];report['pixels'][label]=dict(exact=counts[best]==0,different_pixels=counts[best],candidate_tick=rows[best]['tick']);Image.fromarray(frames[best]).save(output/(label+'.png'));ImageChops.difference(Image.fromarray(frames[best]),Image.fromarray(ref)).save(output/(label+'-difference.png'))
  source=DATA/'research-nature-input-final'
  fixtures=json.loads((source/'fixtures.json').read_text(encoding='utf-8'))
  for phase in ['ready','question']:
   model=next(v for v in fixtures if v['phase']==phase and v['fixture'].endswith('definition.png'))
   page.evaluate('m=>{nature.quiz=new NatureQuiz(nature,{character:()=>character,speak:theaterSpeech});Object.assign(nature.quiz,m,{tick,selectedAttribute:-1});nature.quiz.click(14,54);}',model)
   for state in ['definition','dismissed']:
    fixture=next(v for v in fixtures if v['phase']==phase and v['fixture'].endswith(state+'.png'))
    page.evaluate('m=>{treehouseDemo.setPointer(...m.pointer);if(m.dismiss)nature.quiz.click(...m.pointer);render();}',dict(pointer=fixture['pointer'],dismiss=state=='dismissed'))
    image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB');ref=Image.open(source/fixture['fixture']).convert('RGB');difference=ImageChops.difference(image,ref);count=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));label=phase+'-'+state;report['pixels'][label]=dict(exact=count==0,different_pixels=count);image.save(output/(label+'.png'));difference.save(output/(label+'-difference.png'))
  def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
  check('native start matches both hands secrets and final RNG','()=>{const q=nature.quiz;gameplayRandom.reset(0x991cfbe5);q.opponent=2;q.start();return JSON.stringify(q.cards)==="[[47,89,67,55,58,17,40,24],[64,43,61,59,16,87,36,8]]"&&JSON.stringify(q.secret)==="[2,0]"&&q.player===1&&gameplayRandom.seed===0x6aa986a8;}')
  check('first roll generates native question order and final seed','()=>{const q=nature.quiz;q.roll();for(let i=0;i<3000&&q.busy;i++)advance();return JSON.stringify(q.available)==="[6,1,2]"&&gameplayRandom.seed===0x317a079d;}')
  check('each of eight guess hints consumes one original random call','()=>{const q=nature.quiz;q.phase="question";q.guessing=true;q.remaining[q.player]=255;gameplayRandom.reset(123);let expected=123;for(let i=0;i<8;i++)expected=(Math.imul(expected,214013)+2531011)>>>0;q.run(q.reminder());for(let i=0;i<100&&q.busy;i++)advance();return gameplayRandom.seed===expected;}')
  check('robot waits for cue before choosing a question','()=>{const q=nature.quiz;q.task=null;q.reminding=false;q.phase="question";q.player=1;q.guessing=false;q.robotSpoken=false;q.robotDue=tick+60;q.available=[1,2,6];q.remaining=[255,255];const sounds=[];q.speak=id=>{sounds.push({id,tick});return id===1011?28:0;};const start=tick;advance(60);const cue=sounds.length===1&&sounds[0].id===1011&&sounds[0].tick===start+60;advance(27);const pending=q.robotSpoken;advance(2);return cue&&pending&&sounds.some(v=>v.id===10048&&v.tick>=start+88)&&q.actorScript!==null;}')
  check('help waits only for newly eliminated candidates','()=>{const q=new NatureQuiz(nature,{character:()=>character,speak:()=>0});q.player=0;q.cards[0]=[0,1,2,3,4,5,6,7];q.secret[0]=0;q.remaining[0]=5;q.help[0]=true;q.attributes=id=>[Number(id!==0)];q.perform=function*(){};q.cleanup=()=>{};const waits=[...q.question(0)];return JSON.stringify(waits)==="[36,18,60]"&&q.remaining[0]===1;}')
  check('candidate removal and restoration use their original pitched waits','()=>{const calls=[],q=new NatureQuiz(nature,{speak:(id,rate)=>{calls.push([id,rate]);return rate===8269?14:7;}});q.options=false;q.phase="question";q.player=0;q.opponent=1;q.crossOut(1);const removed=q.remaining[0]===253&&q.candidateWait;for(let i=1;i<=14;i++)q.update(i);const ended=!q.busy;q.crossOut(1);const restored=q.remaining[0]===255&&q.candidateWait;for(let i=15;i<=21;i++)q.update(i);return removed&&ended&&restored&&!q.busy&&JSON.stringify(calls)==="[[1006,8269],[1006,16537]]";}')
  check('candidate cue accepts one input without dispatching another action','()=>{const q=new NatureQuiz(nature,{speak:()=>14});q.options=false;q.phase="question";q.player=0;q.crossOut(1);q.click(310,10);return !q.busy&&!q.candidateWait&&q.remaining[0]===253;}')
  check('turn waits eight lit ticks then sixty before switching player','()=>{const q=new NatureQuiz(nature,{speak:()=>0});q.start();const player=q.player;q.roll();const lit=q.hintControl&&q.player===player;for(let i=1;i<=8;i++)q.update(i);const pause=!q.hintControl&&q.player===player;for(let i=9;i<=67;i++)q.update(i);const held=q.player===player;q.update(68);return lit&&pause&&held&&q.player===1-player;}')
  check('turn lead-in can be interrupted without triggering another control','()=>{const q=new NatureQuiz(nature,{speak:()=>0});q.start();const player=q.player;q.roll();q.click(310,10);const paused=q.leadWait&&!q.hintControl&&q.player===player;q.click(310,10);return paused&&!q.leadWait&&q.player===1-player;}')
  check('prize chooser follows the same die lead-in','()=>{let award=false;const q=new NatureQuiz(nature,{speak:()=>0});q.options=false;q.winner=0;q.phase="won";q.award=()=>award=true;q.roll();for(let i=1;i<68;i++)q.update(i);const waiting=!award;q.update(68);return waiting&&award&&!q.busy;}')
  check('invalid ready candidate gives immediate original die feedback','()=>{const sounds=[],q=new NatureQuiz(nature,{speak:id=>sounds.push(id)});q.start();q.choose(0);return q.reminding&&q.hintControl&&JSON.stringify(sounds)==="[1017]";}')
  check('same definition tab does not repeat selection sound','()=>{const sounds=[],q=new NatureQuiz(nature,{speak:id=>sounds.push(id)});q.start();q.inspectAttribute(3);q.inspectAttribute(3);q.inspectAttribute(4);return JSON.stringify(sounds)==="[1008,1008]";}')
  report['passed']=not report['errors']and all(v['exact']for v in report['pixels'].values())and all(v['passed']for v in report['checks']);b.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
