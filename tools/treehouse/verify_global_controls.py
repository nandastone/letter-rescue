"""Original nature dialogs, erase/print workflows, keyboard pointer and signed saves."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('nature')")
  def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
  for label,message,source,yes in [('single-clear','Send all animals home?','native',True),('empty-clear','No animals to send home!','native',False),('print-question','Print this Scene?','native',True),('both-clear','Send daytime AND nighttime animals home?','native-ctrl',True)]:
   page.evaluate('v=>{if(preferences)closePreferences();askNature(v.message,v.yes?()=>{}:null);pointerVisible=false;}',dict(message=message,yes=yes))
   reference=Image.open(DATA/'research-global-coverage'/source/'state'/(label+'.png')).convert('RGB').crop((6,98,124,166));options=[]
   for phase in range(4):
    page.evaluate('phase=>{preferences.start=tick-phase*12;render();}',phase);im=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB').crop((6,98,124,166));n=sum(a!=b for a,b in zip(im.getdata(),reference.getdata()));options.append((n,phase,im))
   n,phase,image=min(options,key=lambda v:v[0]);delta=ImageChops.difference(image,reference);report['pixels'][label]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox(),phase=phase,region=[6,98,124,166]);image.save(output/(label+'.png'));delta.save(output/(label+'-difference.png'))
  page.evaluate("closePreferences();setScene('inside');room.height=room.target=28;balloon.hidden=true;askChalk();advance(15);pointerVisible=false")
  reference=Image.open(DATA/'research-global-coverage/chalk-question/state/chalk-question.png').convert('RGB').crop((162,28,283,98));options=[]
  for phase in range(4):
   page.evaluate('phase=>{preferences.start=tick-phase*12;render();}',phase);im=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB').crop((162,28,283,98));n=sum(a!=b for a,b in zip(im.getdata(),reference.getdata()));options.append((n,phase,im))
  n,phase,image=min(options,key=lambda v:v[0]);report['pixels']['chalk-question']=dict(exact=n==0,different_pixels=n,phase=phase,region=[162,28,283,98]);image.save(output/'chalk-question.png')
  check('chalk confirmation unrolls blank calendar and No preserves drawing','()=>{chalk.bitmap.pixels[0]=0xffffffff;const ok=room.blank&&room.height===98;answerQuestion(false);advance(14);return ok&&!room.question&&!room.blank&&room.height===28&&chalk.bitmap.pixels[0]===0xffffffff;}')
  check('chalk Yes closes calendar before clearing drawing','()=>{room.height=room.target=98;askChalk();advance(28);const ok=preferences?.message==="Erase Chalkboard?";answerQuestion(true);const pending=chalk.bitmap.pixels[0]===0xffffffff;advance(14);return ok&&pending&&chalk.bitmap.pixels.every(v=>v===0xff000000)&&!room.question;}')
  page.evaluate("setScene('nature');nature.time=0;nature.objects=[[],[]];nature.addAnimal(nature.tables.animals.find(a=>nature.name(a.id)==='Ant').id,221,99);nature.requestClear();answerQuestion(true);pointerVisible=false")
  for i,label in enumerate(['after-01','after-06','after-10','after-50']):
   if i:page.evaluate('advance(4)')
   page.evaluate('render()');im=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB').crop((210,90,232,108));reference=Image.open(DATA/'research-global-coverage/nature-burst/state'/(label+'.png')).convert('RGB').crop((210,90,232,108));n=sum(a!=b for a,b in zip(im.getdata(),reference.getdata()));report['pixels']['nature-burst-'+label]=dict(exact=n==0,different_pixels=n,region=[210,90,232,108]);im.save(output/('nature-burst-'+label+'.png'))
  page.evaluate('closePreferences();nature.time=0;nature.objects=[[],[]];nature.addAnimal(0,210,110);nature.time=1;nature.addAnimal(60,210,110);nature.time=0;nature.selectAnimal(0);nature.factIndex=0;')
  check('single clear requests confirmation and No preserves both scenes','()=>{nature.requestClear();const pending=preferences?.message==="Send all animals home?";answerQuestion(false);return pending&&nature.objects.every(a=>a.length===1);}')
  check('single clear uses three four-tick bursts and retains facts','()=>{nature.requestClear();answerQuestion(true);const a=[nature.eraseEffect.id];advance(4);a.push(nature.eraseEffect.id);advance(4);a.push(nature.eraseEffect.id);advance(4);return JSON.stringify(a)==="[923,924,925]"&&!nature.eraseTask&&nature.objects[0].length===0&&nature.objects[1].length===1&&nature.factOpen&&nature.selected===0;}')
  check('undo restores erased animals','()=>{nature.undoClear();return nature.objects.every(a=>a.length===1);}')
  check('Control erase requests both scenes and clears without bursts','()=>{const r=nature.tables.rectangles[10];activate((r[1]+r[3])/2,(r[0]+r[2])/2,"test",{ctrlKey:true});const pending=preferences?.message==="Send daytime AND nighttime animals home?";answerQuestion(true);return pending&&nature.objects.every(a=>a.length===0)&&!nature.eraseTask&&nature.factOpen;}')
  check('empty acknowledgment dismisses from any pointer position','()=>{nature.requestClear();clickPreferences(200,180);return !preferences;}')
  check('print waits for consent and prints original framebuffer without cursor','()=>{window.printCalls=0;window.print=()=>{window.printCalls++;window.printState={modal:!!preferences,cursor:pointerVisible,width:canvas.width,height:canvas.height};};printNature();const pending=window.printCalls===0&&preferences?.message==="Print this Scene?";answerQuestion(true);return pending&&window.printCalls===1&&!window.printState.modal&&!window.printState.cursor&&window.printState.width===320&&window.printState.height===200;}')
  check('printing preference disables scene printing','()=>{gameSave.preferences.printing=false;printNature();const ok=!preferences&&printCalls===1;gameSave.preferences.printing=true;return ok;}')
  page.locator('#game').focus();page.evaluate('pointer=[100,100]');page.keyboard.down('ArrowRight');page.evaluate('advance(6)');page.keyboard.up('ArrowRight');check('keyboard pointer one pixel per three ticks','pointer[0]===103&&pointer[1]===100')
  page.keyboard.down('Shift');page.keyboard.down('ArrowDown');page.evaluate('advance(3)');page.keyboard.up('ArrowDown');page.keyboard.up('Shift');check('Shift pointer one pixel per tick','pointer[0]===103&&pointer[1]===104')
  page.evaluate('pointer=[319,199]');page.keyboard.down('ArrowRight');page.keyboard.down('ArrowDown');page.evaluate('advance(12)');page.keyboard.up('ArrowRight');page.keyboard.up('ArrowDown');check('keyboard pointer stays on original screen','pointer[0]===319&&pointer[1]===199')
  page.evaluate('nature.time=0;const r=nature.tables.rectangles[13];pointer=[(r[1]+r[3])/2,(r[0]+r[2])/2]');page.keyboard.press('Enter');check('Enter activates current pointer hotspot','nature.time===1')
  page.evaluate('nature.time=0;nature.objects=[[],[]];const o=nature.addAnimal(0,210,110),s=store.shape("modules",nature.tables.animals[0].large);window.dragX=o.x;pointer=[o.x+Math.floor(s.w/2),o.y+Math.floor(s.h/2)]');page.keyboard.down('Space');page.keyboard.down('ArrowRight');page.evaluate('advance(16)');page.keyboard.up('ArrowRight');page.keyboard.up('Space');check('Space supports original slow keyboard dragging','nature.objects[0][0].x===dragX+3&&!nature.drag')
  page.evaluate('const o=nature.objects[0][0],s=store.shape("modules",nature.tables.animals[o.id].large);pointer=[o.x+Math.floor(s.w/2),o.y+Math.floor(s.h/2)]');page.keyboard.press('z');check('mapped keyboard action releases its temporary animal drag','!nature.drag')
  check('offscreen balloon survives DOS save import and exact export','()=>{const data=bytes(ORIGINAL.status),v=new DataView(data.buffer);v.setUint16(0x8ea,1,true);[6,1,1,-1,95,37,124].forEach((n,i)=>v.setInt16(0x8ec+2*i,n,true));gameSave.importData(data);const object=resident.objects.find(o=>o.type===6);return object?.rect[0]===-1&&!balloon.hidden&&gameSave.exportData().every((n,i)=>n===data[i]);}')
  report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
