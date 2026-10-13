"""Focused real mouse/touch press, hold and cancellation checks for click-only objects.

Scene/object fixtures isolate each kind. Input travels through production canvas
handlers; a read-only click-dispatch trace observes the production implementation.
"""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright
CASES=[('egg',0,True,1),('nuts',9,True,1),('basket',10,True,1),('open-basket',10,True,3),('bird',15,True,1),('broken-flower',7,True,5),('outside-plane',1,False,1),('pile',14,False,1),('food',16,False,1)]
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True)
  for touch in [False,True]:
   context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch);page=context.new_page();page.set_default_timeout(5000);page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());cdp=context.new_cdp_session(page)if touch else None
   page.evaluate("()=>{const original=resident.clickObject;window.dispatches=[];resident.clickObject=function(o,point){dispatches.push({type:o.type,tick});return original.call(this,o,point);};}")
   def flush():page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
   def down():
    page.locator('#game').scroll_into_view_if_needed();b=page.locator('#game').bounding_box();pt=dict(x=b['x']+65.1*b['width']/320,y=b['y']+130.1*b['height']/200)
    if touch:cdp.send('Input.dispatchTouchEvent',dict(type='touchStart',touchPoints=[dict(**pt,id=1)]))
    else:page.mouse.move(**pt);page.mouse.down()
    flush()
   def up():
    if touch:cdp.send('Input.dispatchTouchEvent',dict(type='touchEnd',touchPoints=[]))
    else:page.mouse.up()
    flush()
   def check(name,expression):
    passed=bool(page.evaluate(expression));report['checks'].append(dict(name=('touch'if touch else'mouse')+': '+name,passed=passed))
    if not passed:raise AssertionError(name)
   for name,kind,inside,state in CASES:
    for mode in ['release','hold','blur','hidden','cancel']:
     try:
      page.evaluate("""m=>{releaseAll();Object.defineProperty(document,'hidden',{configurable:true,value:false});resident.active=null;resident.queue=[];resident.objectTask=null;resident.ambientAnimation=null;resident.objectMotion=null;resident.objects=[];resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;setScene(m.inside?'inside':'outside');resident.selected=true;room.leave();room.height=room.target=28;balloon.hidden=true;const o=resident.create(m.kind,m.inside);o.state=m.state;o.rect=[120,50,140,80];window.dispatches=[];window.testKind=m.kind;render();}""",dict(kind=kind,inside=inside,state=state))
      down();page.wait_for_function('!!resident.drag');page.evaluate('advance(5)');check(name+' '+mode+' waits during early press','dispatches.filter(e=>e.type===testKind).length===0')
      if mode=='release':up();page.evaluate('advance(1)');check(name+' release dispatches once after capture loss','dispatches.filter(e=>e.type===testKind).length===1');page.evaluate('advance(4)');check(name+' release does not redispatch','dispatches.filter(e=>e.type===testKind).length===1')
      elif mode=='hold':page.evaluate('advance(9)');check(name+' held before threshold','dispatches.filter(e=>e.type===testKind).length===0');page.evaluate('advance(1)');check(name+' held threshold dispatches once','dispatches.filter(e=>e.type===testKind).length===1');up();page.evaluate('advance(5)');check(name+' held release does not repeat the original object click','dispatches.filter(e=>e.type===testKind).length===1')
      else:
       if mode=='blur':page.evaluate("window.dispatchEvent(new Event('blur'))")
       elif mode=='hidden':page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
       else:page.evaluate("canvas.dispatchEvent(new PointerEvent('pointercancel',{pointerId:[...pointers.keys()][0]}))")
       up();page.evaluate('advance(30)');check(name+' '+mode+' cancels pending action','dispatches.filter(e=>e.type===testKind).length===0&&!resident.drag')
     except Exception as e:report['errors'].append(f'{name}/{mode}/{touch}: {e}');break
   context.close()
  browser.close()
 report['passed']=not report['errors']and all(c['passed']for c in report['checks']);report['scope']='Focused fixtures with production mouse/touch handlers, press timing and cancellation. Native rendering, gameplay and sound are compared by separate captured journeys.'
 (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2));return report['passed']
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output)else 1)
