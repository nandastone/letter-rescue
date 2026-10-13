"""Fresh/reloaded desktop and touch journeys using the visible game controls.

Only the clock is stepped for speed. Gameplay state is read for assertions,
never assigned. The focused suites cover original-frame and generated-game parity.
"""
from pathlib import Path
import argparse, hashlib, json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in (False, True):
            label = 'touch' if touch else 'desktop'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=844 if touch else 960), has_touch=touch, is_mobile=touch)
            page = context.new_page()
            page.add_init_script('requestAnimationFrame=()=>0')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(html.resolve().as_uri())

            def check(name, expression):
                passed = bool(page.evaluate(expression))
                report['checks'].append(dict(name=f'{label}: {name}', passed=passed))
                if not passed:
                    raise AssertionError(f'{label}: {name}')

            def press(name):
                button = page.get_by_role('button', name=name, exact=True)
                button.tap() if touch else button.click()
                page.wait_for_function('!audio.context || audio.context.state === "running"')
                # Await the asynchronous audio-unlock click handler.
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                if name=='Play the musical maze':
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")

            def settle():
                result = page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='theater'&&(theater.playing||theater.presentation||theater.tokenSequence||theater.previewCategory>=0)||scene==='boardgame'&&boardgame.motion.busy||scene==='nature'&&nature.mode==='quiz'&&nature.quiz.busy;while(busy()&&n++<6000)advance();render();return !busy();}''')
                if not result:
                    raise AssertionError(f'{label}: action did not complete')

            try:
                check('fresh welcome', 'scene==="outside"&&!resident.selected')
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                check('entrance reaches selected friend', 'scene==="inside"&&resident.selected&&!entering')
                page.locator('#text-size').fill('30'); page.locator('#text-size').dispatch_event('input')
                check('reading size is applied', 'getComputedStyle(document.documentElement).getPropertyValue("--read-size").trim()==="30px"')

                press('Go outside'); press('Watch the birdhouse')
                check('yard animation starts', 'resident.busy&&resident.ambientAnimation.id===1060')
                press('Go inside')
                check('navigation does not abandon animation', 'scene==="outside"&&resident.busy')
                settle(); press('Visit the squirrels')
                for _ in range(3):
                    press('Toss a nut'); settle()
                check('three visible nuts', 'scene==="hollow"&&exterior.nuts.length===3')
                press('Read the sign'); settle(); press('Back to the yard'); press('Go inside')
                check('ladder returns without another greeting', 'scene==="inside"&&!entering')

                press('Make some music'); settle()
                check('music navigation completes', 'scene==="music"&&!roomTravel')
                press('Play song'); page.evaluate('advance(10000)')
                check('song finishes', '!songPlaying')
                press('Play the musical maze'); press('Skip introduction'); page.evaluate('()=>{for(let i=0;i<6000&&maze.busy;i++)advance();render();}')
                check('maze accepts player choices', 'scene==="maze"&&!maze.busy&&maze.phase!=="intro"')
                # Complete the original bucket/smoke return before requesting
                # the separate piano-to-room journey.
                press('Back'); settle(); press('Back'); settle()

                press('Put on a play'); settle()
                if page.get_by_role('button', name='Start the theater', exact=True).count():
                    press('Start the theater')
                page.locator('#theater-part-0').select_option('0')
                page.locator('#theater-part-1').select_option('0')
                press('Perform my sentence'); settle()
                check('sentence performed', 'scene==="theater"&&theater.performances>0&&!theater.playing')
                press('Back'); settle()

                press('Explore nature'); settle()
                category = page.locator('#nature-class option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                page.locator('#nature-class').select_option(category)
                animal = page.locator('#nature-animal option').evaluate_all('o=>o.find(v=>v.value!=="-1").value')
                page.locator('#nature-animal').select_option(animal); press('Add this animal')
                check('animal and readable facts appear', 'nature.objects.flat().length>0&&!$("fact-card").hidden&&$("fact").textContent.length>0')
                press('Play the animal guessing game'); press('Start the guessing game'); settle()
                check('guessing game starts', 'nature.mode==="quiz"&&!nature.quiz.options&&nature.quiz.cards.every(c=>c.length===8)')
                press('Back'); press('Back'); settle()

                press('Play the board game'); settle(); press('Start the board game'); settle()
                check('board game starts', 'scene==="boardgame"&&!boardgame.options')
                press('Back'); settle(); press('Look through the telescope'); settle()
                press('The birdbath'); page.evaluate('advance(1500)'); press('Back'); settle()
                check('telescope returns friend to room', 'scene==="inside"&&!roomTravel&&resident.pose===1')

                # Navigation saved the creations through the ordinary save path.
                page.reload()
                check('reading size survives reload', '$("text-size").value==="30"')
                press('Choose the boy'); settle(); press('Explore nature'); settle()
                check('collage survives reload', 'nature.objects.flat().length>0')
                press('Back'); settle(); press('Put on a play'); settle()
                if page.get_by_role('button', name='Start the theater', exact=True).count():
                    press('Start the theater')
                check('sentence survives reload', 'theater.selection[0]===0&&theater.selection[1]===0')
                check('no page overflow', 'document.documentElement.scrollWidth<=window.innerWidth')
                page.screenshot(path=str(output/f'{label}.png'), full_page=True)
            except Exception as error:
                report['errors'].append(f'{label}: {error}')
                page.screenshot(path=str(output/f'{label}-failure.png'), full_page=True)
            context.close()
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); verify(args.html, args.output)
