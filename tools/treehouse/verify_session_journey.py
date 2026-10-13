"""An uninterrupted creation/game/prize session, followed by a full reload.

Only visible controls change gameplay. Reads provide assertions and game answers;
advance() speeds animations without installing any gameplay state.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], sessions=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            label = 'touch-girl' if touch else 'desktop-boy'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch, timezone_id='Australia/Brisbane')
            page = context.new_page(); page.set_default_timeout(5000)
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('2026-09-28T10:00:00+10:00');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            actions, checkpoints = [], []

            def check(name, expression):
                ok = bool(page.evaluate(expression))
                report['checks'].append(dict(name=label+': '+name, passed=ok))
                if not ok:
                    raise AssertionError(name)

            def press(name):
                b = page.get_by_role('button', name=name, exact=True)
                b.tap() if touch else b.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                actions.append(name)
                if name=='Play the musical maze':
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")

            def settle():
                done = page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||rewards.active&&rewards.phase!=='choose'||scene==='theater'&&(theater.playing||theater.presentation||theater.tokenSequence||theater.previewCategory>=0)||scene==='maze'&&maze.busy||scene==='nature'&&nature.mode==='quiz'&&(nature.quiz.busy||nature.quiz.winAnimation&&!nature.quiz.winAnimation.done)||scene==='boardgame'&&(boardgame.motion.busy||boardgame.moving||boardgame.phase==='rolling')||scene==='telescope'&&telescopeBusy();while(busy()&&n++<30000)advance();render();return !busy();}''')
                if not done:
                    raise AssertionError('Action did not settle')

            def mark(name):
                checkpoints.append(dict(name=name, state=page.evaluate('()=>({scene,tick,seed:gameplayRandom.seed,notes:stats.notesPlayed})')))

            def songbooks():
                return page.evaluate('()=>Array.from(musicEditor.exportData())')

            def collage():
                return page.evaluate('nature.objects.map(list=>list.map(({id,x,y})=>({id,x,y})))')

            try:
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Make some music'); settle()
                page.locator('#music-book').select_option('1')
                for mode in [0, 1]:
                    page.locator('#score-size').select_option(str(mode))
                    page.locator('#song-title').fill('Session '+('long' if mode else 'short'))
                    page.locator('#song-title').press('Tab')
                    for pitch in [5,9,12]:
                        key = page.locator(f'#touch-keys button[data-pitch="{pitch}"]')
                        if touch:
                            key.tap()
                        else:
                            key.focus(); page.keyboard.down('Space')
                            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                            page.evaluate('advance(8)'); page.keyboard.up('Space')
                    press('Add a rest')
                    check(f'book {mode} contains entered notes and rest', f'musicEditor.books[{mode}][0][{mode}]===4&&[5,9,12].every((n,i)=>(musicEditor.books[{mode}][0][5+2*i]&127)===n)&&musicEditor.books[{mode}][0][12]>=8')
                book = songbooks(); mark('both songbooks created')
                press('Play song'); page.evaluate('advance(6000);render()')
                check('composed song plays to completion', '!songPlaying&&!held.size')
                press('Play the musical maze'); press('Skip introduction'); settle()
                direction = page.evaluate('maze.correct')
                press(page.get_by_role('button', name=re.compile('^'+['Left','Up','Right','Down'][direction]+':')).inner_text()); settle()
                press('Guess the song'); settle(); press(page.evaluate('maze.title')); settle()
                check('maze wins after composing and playback', 'maze.phase==="win"&&!maze.busy')
                press('Back to the piano'); settle()
                check('maze keeps both compositions unchanged', 'JSON.stringify(Array.from(musicEditor.exportData()))==='+json.dumps(json.dumps(book,separators=(',',':'))))
                press('Back'); settle(); mark('maze completed')

                press('Put on a play'); settle()
                if page.get_by_role('button', name='Start the theater', exact=True).count():
                    press('Start the theater')
                for part in range(4):
                    page.locator(f'#theater-part-{part}').select_option('0')
                press('Perform my sentence'); settle()
                check('theater performance finishes', 'theater.performances>0&&!theater.playing')
                play = page.evaluate('theater.savedState()')
                press('Back'); settle(); mark('sentence performed')

                press('Explore nature'); settle()
                for night in [False, True]:
                    if night:
                        press('Switch to nighttime')
                    category = page.locator('#nature-class option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                    page.locator('#nature-class').select_option(category)
                    animal = page.locator('#nature-animal option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                    page.locator('#nature-animal').select_option(animal); press('Add this animal')
                animals = collage()
                check('both collages populated', 'nature.objects.every(list=>list.length===1)')
                press('Play the animal guessing game')
                page.locator('#quiz-opponent').select_option('1')
                press('Start the guessing game'); settle(); press('Roll for the next turn'); settle()
                press('Make a guess'); settle()
                answer = page.evaluate('()=>{const q=nature.quiz;return nature.name(q.cards[q.player][q.secret[q.player]]);}')
                press('Guess '+answer); settle(); press('Choose a prize'); settle()
                choice = page.evaluate('rewards.choices.findIndex(id=>[2,7].includes(id))')
                if choice < 0:
                    raise AssertionError('Stable room prize absent from choices')
                prize = page.evaluate('(i)=>rewards.choices[i]', choice)
                press(page.locator('#controls button').nth(choice).inner_text()); settle()
                check('prize earned after other activities', f'!rewards.active&&resident.objects.some(o=>o.type==={prize})')
                press('Back'); press('Back'); settle(); mark('nature win and prize')

                press('Play the board game'); settle(); press('Start the board game'); settle()
                press('Roll for the next turn'); settle()
                check('board accepts first turn after prize', 'boardgame.phase==="move"&&boardgame.remaining>0')
                press('Back'); settle()
                press('Look through the telescope'); settle(); press('The birdbath'); settle(); press('Back'); settle()
                press('Go outside'); press('Visit the squirrels'); press('Toss a nut'); settle()
                press('Back to the yard'); press('Go inside'); settle(); mark('board telescope and yard')

                press('Make some music'); settle()
                check('both songbooks survive activity visits', 'JSON.stringify(Array.from(musicEditor.exportData()))==='+json.dumps(json.dumps(book,separators=(',',':'))))
                press('Play song'); page.evaluate('advance(6000);render()')
                check('saved composition still plays', '!songPlaying&&!held.size')
                press('Back'); settle(); press('Explore nature'); settle()
                check('collages survive quiz and visits', 'JSON.stringify(nature.objects.map(list=>list.map(({id,x,y})=>({id,x,y}))))==='+json.dumps(json.dumps(animals,separators=(',',':'))))
                press('Back'); settle(); press('Put on a play'); settle()
                check('sentence survives other activities', 'JSON.stringify(theater.savedState())==='+json.dumps(json.dumps(play,separators=(',',':'))))
                press('Perform my sentence'); settle(); press('Back'); settle()
                check('room prize survives complete session', f'resident.objects.some(o=>o.type==={prize})')
                mark('creations revisited')
                page.reload(); press('Choose the girl' if touch else 'Choose the boy'); settle()
                check('prize survives full reload', f'resident.objects.some(o=>o.type==={prize})')
                press('Make some music'); settle()
                check('both books reload byte for byte', 'JSON.stringify(Array.from(musicEditor.exportData()))==='+json.dumps(json.dumps(book,separators=(',',':'))))
                press('Back'); settle(); press('Explore nature'); settle()
                check('both collages reload exactly', 'JSON.stringify(nature.objects.map(list=>list.map(({id,x,y})=>({id,x,y}))))==='+json.dumps(json.dumps(animals,separators=(',',':'))))
                press('Back'); settle(); press('Put on a play'); settle()
                check('sentence reloads exactly', 'JSON.stringify(theater.savedState())==='+json.dumps(json.dumps(play,separators=(',',':'))))
                check('no page overflow', 'document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(output/(label+'-complete.png')), full_page=True)
                report['sessions'].append(dict(name=label,actions=actions,checkpoints=checkpoints,prize=prize,passed=True))
                print(label,'PASS',flush=True)
            except Exception as e:
                report['errors'].append(label+': '+str(e))
                report['sessions'].append(dict(name=label,actions=actions,checkpoints=checkpoints,passed=False))
                page.screenshot(path=str(output/(label+'-failure.png')),full_page=True)
                print(label,'FAIL',str(e),flush=True)
            context.close()
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Two uninterrupted desktop/touch sessions: both songbooks authored and played, maze won, sentence performed, day/night collages created, animal game won and prize earned, board/telescope/yard visits, creations revisited and full reload. Fixed initial date; animation time accelerated. No native RNG ordering, audible waveform or timing equivalence claim.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();sys.exit(0 if verify(args.html,args.output) else 1)
