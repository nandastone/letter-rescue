"""Exercise focus loss and delayed audio unlock through browser input handlers.

Scene setup is direct; mouse/key events use the live handlers. Synthetic blur
and visibility events represent browser lifecycle changes, not DOS behavior.
"""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        def fresh(scene):
            page=browser.new_page(viewport=dict(width=1360,height=960))
            page.set_default_timeout(5000)
            page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri());page.evaluate('(s)=>setScene(s)',scene)
            return page
        def check(page,name,expression):
            passed=bool(page.evaluate(expression));report['checks'].append(dict(name=name,passed=passed));print(name,'PASS' if passed else 'FAIL',flush=True)
        def position(page,x,y):
            box=page.locator('#game').bounding_box();page.mouse.move(box['x']+x*box['width']/320,box['y']+y*box['height']/200)
        def hide(page):
            page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
        page=fresh('nature')
        page.evaluate('nature.addAnimal(0,210,110)')
        x,y=page.evaluate('()=>{const o=nature.objects[0][0],s=store.shape("modules",nature.tables.animals[o.id].large);return [o.x+s.w/2,o.y+s.h/2];}')
        position(page,x,y);page.mouse.down();page.wait_for_function('!!nature.drag',polling=20)
        check(page,'animal drag starts through canvas','!!nature.drag&&pointers.size===1')
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        check(page,'losing focus ends animal drag','!nature.drag&&pointers.size===0')
        page.mouse.up();page.close()

        page=fresh('theater');page.evaluate('theater.options=false;theater.mixUp=true;theater.choose(0,0);render()')
        x,y=page.evaluate('()=>{const r=theater.tables.ui_rects[23];return [(r[1]+r[3])/2,(r[0]+r[2])/2];}')
        position(page,x,y);page.mouse.down();page.wait_for_function('!!theater.drag',polling=20)
        hide(page);check(page,'hiding page cancels sentence-token drag','!theater.drag&&theater.selection[0]===0')
        page.mouse.up();page.close()

        page=fresh('music');page.evaluate('setMusicComposing(true)')
        x,y=page.evaluate('()=>{const r=musicEditor.markers[musicEditor.position+1];return [(r[1]+r[3])/2,(r[0]+r[2])/2];}')
        position(page,x,y);page.mouse.down();page.wait_for_function('!!musicEditor.drag',polling=20)
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        check(page,'losing focus ends score-marker drag','!musicEditor.drag')
        page.mouse.up();page.close()

        page=fresh('nature');page.locator('#game').focus();page.keyboard.down('ArrowRight')
        hide(page);page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));window.positionBeforeResume=[...pointer];advance(30)")
        check(page,'hidden-page held arrow does not keep moving after return','pointerKeys.size===0&&pointer.every((n,i)=>n===positionBeforeResume[i])')
        page.keyboard.up('ArrowRight');page.close()

        for mode in ['keyboard','pointer']:
            page=fresh('music');key=page.locator('#touch-keys button[data-pitch="0"]')
            key.focus();page.evaluate('()=>{audio.unlock=()=>new Promise(resolve=>{window.finishUnlock=resolve;});}')
            if mode=='keyboard':page.keyboard.down('Enter')
            else:
                box=key.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.down()
            page.wait_for_function('typeof finishUnlock==="function"',polling=20)
            page.evaluate("window.dispatchEvent(new Event('blur'));finishUnlock()")
            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            check(page,f'{mode} piano press cannot revive after focus loss during unlock','held.size===0&&audio.active.size===0')
            if mode=='keyboard':page.keyboard.up('Enter')
            else:page.mouse.up()
            # A fresh gesture must still work after cancellation.
            page.evaluate('()=>{audio.unlock=async()=>{};}');key.focus();page.keyboard.down('Enter')
            page.wait_for_function('held.size===1',polling=20);page.keyboard.up('Enter')
            check(page,f'{mode} cancellation allows a fresh piano press and release','held.size===0')
            page.close()
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.html,a.output) else 1)
