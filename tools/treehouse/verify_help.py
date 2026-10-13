"""Original help regions, context routing and keyboard modal behavior."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate('resident.ambientEnabled=false')
  def check(name,code,arg=None):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code,arg))))
  def compare(label,path,box):
   image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB').crop(box);ref=Image.open(path).convert('RGB').crop(box);delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));report['pixels'][label]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox(),region=box);image.save(output/(label+'.png'));delta.save(output/(label+'-difference.png'))
  rows=json.loads((DATA/'research-help/comparison.json').read_text(encoding='utf-8'))
  for row in rows:
   if row.get('status'):continue
   label=row['label'];extra=label in ['board-active','theater-options'];capture='theater-both'if label=='theater-options'else label
   path=DATA/'research-help'/('extra'if extra else'native')/'state'/(capture+('-help'if 'context'in row else''))
   ram=path.with_suffix('.ram-0').read_bytes();py,px=struct.unpack_from('<hh',ram,0x34454)
   page.evaluate('()=>{statusOverlay=null;if(preferences)closePreferences();setScene("outside");resident.task=null;room.task=null;pointerVisible=false;}')
   if 'context'in row:
    page.evaluate('v=>{if(v.theater)setScene("theater");openHelp();preferences.layout=ORIGINAL.help.find(h=>h.context===v.context);treehouseDemo.setPointer(v.x,v.y);render();}',dict(context=row['context'],theater=label.startswith('theater'),x=px,y=py))
   else:page.evaluate('v=>{showStatusOverlay(v);render();}','Version 1.1'if label=='version'else'Sound is Off')
   t,l,b,r=row['rectangle'];compare(label,path.with_suffix('.png'),[l,t,r,b])
  page.evaluate('statusOverlay=null;scene="outside";resident.selected=false;pointer=[160,100];openHelp();render()')
  check('welcome help and complete original text',r"()=>preferences.layout.context===18&&$('instructions').textContent===preferences.layout.body.replace(/\r/g,'\n')")
  page.evaluate('pointer=[10,10]');page.keyboard.press('Escape');check('outside Escape keeps help open','()=>!!preferences')
  page.evaluate("activate(10,10,'test')");check('outside click keeps help open','()=>!!preferences')
  page.evaluate('pointer=[160,100]');page.keyboard.press('Escape');check('inside key presses Done for twenty ticks','()=>{advance(19);const open=!!preferences;advance();return open&&!preferences;}')
  page.keyboard.press('F1');check('F1 reopens help','()=>preferences?.kind==="help"')
  page.keyboard.press('Control+v');check('version overlays help and blocks activity for 180 ticks','()=>{const before=resident.tick;advance(179);const active=!!statusOverlay;advance();return active&&!statusOverlay&&preferences?.kind==="help"&&resident.tick===before;}')
  page.keyboard.press('Control+s');check('sound shortcut works in help','()=>statusOverlay?.label===(audio.enabled?"Sound is On":"Sound is Off")')
  page.keyboard.press('x');check('input dismisses only status box','()=>!statusOverlay&&!!preferences')
  page.evaluate('closePreferences();pointer=[0,0]');page.keyboard.press('Control+Alt+F1');check('original hidden dedication','()=>preferences.layout.context===29')
  page.get_by_role('button',name='Done',exact=True).click();page.evaluate('advance(20)');check('readable Done works with pointer outside','()=>!preferences')
  # Source-backed context routes; native pixels above are a separate check.
  routes=[('outside','resident.selected=false',18),('inside','resident.selected=true',19),('music','musicSelector.open=false;musicEditor.enabled=false',0),('music','musicEditor.enabled=true',15),('music','musicSelector.open=true;musicSelector.category=-1',6),('music','musicSelector.category=0',7),('theater','theater.options=true',13),('theater','theater.options=false;theater.mixUp=false;theater.propsEnabled=false',2),('theater','theater.mixUp=true;theater.propsEnabled=true',20),('theater','theater.mixUp=false',21),('theater','theater.mixUp=true;theater.propsEnabled=false',22),('boardgame','boardgame.options=true',10),('boardgame','boardgame.options=false;boardgame.winner=-1;boardgame.loser=-1;boardgame.exchange=null;boardgame.phase="ready"',3),('boardgame','boardgame.exchange={}',25),('boardgame','boardgame.exchange=null;boardgame.phase="reward";boardgame.mode=0',16),('boardgame','boardgame.mode=1',24),('boardgame','boardgame.winner=0',23),('nature','nature.mode="explore"',1),('nature','nature.mode="quiz";nature.quiz.options=true',11),('nature','nature.quiz.options=false;nature.quiz.winner=-1;nature.quiz.phase="ready"',26),('nature','nature.quiz.phase="question";nature.quiz.player=0;nature.quiz.help[0]=false',9),('nature','nature.quiz.help[0]=true',27),('nature','nature.quiz.winner=0',28),('maze','maze.cancel();maze.largeIntro=false;maze.phase="play"',8),('maze','maze.phase="win"',17)]
  for scene,setup,expected in routes:check('context '+str(expected),'()=>{if(scene!=='+json.dumps(scene)+')setScene('+json.dumps(scene)+');'+setup+';return helpContext()==='+str(expected)+';}')
  report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
