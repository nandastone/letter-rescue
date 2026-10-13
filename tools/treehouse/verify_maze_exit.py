"""Win through ordinary inputs, then compare readable/canvas exits and saved history."""
from pathlib import Path
import argparse,hashlib,json,re,sys
from playwright.sync_api import sync_playwright


def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[],journeys=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for touch,route in [(False,'readable'),(True,'readable'),(False,'canvas'),(False,'global'),(False,'interrupt'),(False,'treehouse'),(True,'treehouse')]:
            label=('touch' if touch else 'desktop')+'-'+route
            context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch,timezone_id='Australia/Brisbane')
            page=context.new_page();page.set_default_timeout(5000)
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('2026-09-28T10:00:00+10:00');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
            page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
            actions=[]
            def check(name,expression):
                ok=bool(page.evaluate(expression));report['checks'].append(dict(name=label+': '+name,passed=ok))
                if not ok:raise AssertionError(name)
            def press(name):
                b=page.get_by_role('button',name=name,exact=True);b.tap() if touch else b.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');actions.append(name)
                if name=='Play the musical maze':
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")
            def settle():
                done=page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='maze'&&maze.busy;while(busy()&&n++<30000)advance();render();return !busy();}''')
                if not done:raise AssertionError('Animation did not settle')
            def leave():
                if route in ('canvas','treehouse'):
                    x,y=page.evaluate('(index)=>{const r=maze.t.ui_rects[index];return [(r[1]+r[3])/2,(r[0]+r[2])/2];}',0 if route=='treehouse' else 6)
                    canvas=page.locator('#game');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
                    click=page.touchscreen.tap if touch else page.mouse.click
                    click(box['x']+x*box['width']/320,box['y']+y*box['height']/200)
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');actions.append('Canvas return control')
                else:press('Back' if route=='global' else 'Back to the piano')
            try:
                press('Choose the girl' if touch else 'Choose the boy');settle()
                press('Make some music');settle();press('Play the musical maze');press('Skip introduction');settle()
                direction=page.evaluate('maze.correct')
                press(page.get_by_role('button',name=re.compile('^'+['Left','Up','Right','Down'][direction]+':')).inner_text());settle()
                press('Guess the song');settle();press(page.evaluate('maze.title'));settle()
                check('ordinary game reaches victory','maze.phase==="win"&&!maze.busy')
                won=page.evaluate('maze.activeSong')
                if route=='interrupt':
                    press('Hear the whole song')
                    check('song playback starts','maze.busy&&!!maze.currentEvent')
                    leave()
                    check('first return press interrupts playback without leaving','scene==="maze"')
                    settle();check('interrupted playback returns to victory controls','maze.phase==="win"&&!maze.busy')
                leave()
                if route not in ('global','treehouse'):
                    check('return plays original control flash before departure','scene==="maze"&&maze.busy&&maze.controlFlash===1')
                    check('departure retains solved score while choosing replacement',f'maze.activeSong==={won}&&maze.songs[maze.secret]!=={won}')
                settle()
                destination='inside' if route=='treehouse' else 'music'
                check('exit animation reaches '+destination,f'scene==="{destination}"&&!maze.busy')
                songs=page.evaluate('maze.songs')
                check('solved song replaced before save',f'!maze.songs.includes({won})&&maze.roundReplaced')
                check('stored song list immediately matches replacement','''()=>{const raw=Uint8Array.from(atob(localStorage.getItem('treehouse-status-v1')),c=>c.charCodeAt(0)),view=new DataView(raw.buffer);return maze.songs.every((song,i)=>view.getUint16(0x8da+2*i,true)===song);}''')
                check('stored song history immediately matches runtime','''()=>{const raw=Uint8Array.from(atob(localStorage.getItem('treehouse-status-v1')),c=>c.charCodeAt(0)),view=new DataView(raw.buffer);return Array.from({length:24},(_,i)=>!!view.getUint16(0x8aa+2*i,true)===maze.history.has(i)).every(Boolean);}''')
                page.reload();press('Choose the girl' if touch else 'Choose the boy');settle()
                press('Make some music');settle();press('Play the musical maze');press('Skip introduction');settle()
                check('reload retains exactly the replacement song set','JSON.stringify(maze.songs)==='+json.dumps(json.dumps(songs,separators=(',',':'))))
                report['journeys'].append(dict(name=label,actions=actions,won=won,songs=songs,passed=True));print(label,'PASS',flush=True)
            except Exception as e:
                report['errors'].append(label+': '+str(e));report['journeys'].append(dict(name=label,actions=actions,passed=False))
                page.screenshot(path=str(output/(label+'-failure.png')),full_page=True);print(label,'FAIL',str(e),flush=True)
            context.close()
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Seven fresh ordinary-control wins followed by desktop/touch readable return, canvas return, global Back, return during song replay and desktop/touch treehouse exits. Checks destination, exit choreography, immediate stored replacement/history and reload. Fixed initial clock, accelerated animations, state read for answers only; no native timing claim.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2));return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();sys.exit(0 if verify(a.html,a.output) else 1)
