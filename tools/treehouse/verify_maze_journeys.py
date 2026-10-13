"""Win and restart musical mazes through visible controls, without installing state.

Reads model answers as an input oracle and steps the animation clock. This is
browser integration coverage, not a claim of native graphics or timing parity.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                  checks=[], errors=[], journeys=[])
    types, scenes = set(), set()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for touch in [False, True]:
            label = 'touch-girl' if touch else 'desktop-boy'
            context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960),
                                          has_touch=touch, is_mobile=touch, timezone_id='Australia/Brisbane')
            page = context.new_page()
            page.set_default_timeout(5000)
            hour = 11 if touch else 10
            page.add_init_script("{const NativeDate=Date,fixed=Date.parse('2026-09-28T%02d:00:00+10:00');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;" % hour)
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            actions, rounds = [], []

            def check(name, expression):
                ok = bool(page.evaluate(expression))
                report['checks'].append(dict(name=label + ': ' + name, passed=ok))
                if not ok:
                    raise AssertionError(name)

            def press(name):
                button = page.get_by_role('button', name=name, exact=True)
                button.tap() if touch else button.click()
                actions.append(name)
                if name=='Play the musical maze':
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    assert page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();return !roomTravel&&scene==='maze';}")

            def settle():
                state = page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='maze'&&maze.busy;while(busy()&&n++<30000)advance();render();return {done:!busy(),ticks:n};}''')
                if not state['done']:
                    raise AssertionError('Animation did not settle')

            def sample():
                state = page.evaluate('()=>({phase:maze.phase,node:maze.node,type:maze.type,earned:maze.earned,correct:maze.correct,song:maze.activeSong})')
                if state['phase'] == 'play':
                    types.add(state['type']); scenes.add(state['node'])
                return state

            def direction(index):
                name = page.get_by_role('button', name=re.compile('^' + ['Left', 'Up', 'Right', 'Down'][index] + ':')).inner_text()
                press(name); settle()

            try:
                press('Choose the girl' if touch else 'Choose the boy'); settle()
                press('Make some music'); settle()
                press('Play the musical maze')
                if touch:
                    press('Skip introduction')
                settle()
                check('introduction reaches first challenge', 'scene==="maze"&&maze.phase==="play"&&!maze.busy')
                for round_index in range(6):
                    start = sample()
                    if round_index == 0:
                        press('Hear the sound again'); settle()
                        wrong = [i for i in range(4) if i != start['correct']]
                        direction(wrong[0]); direction(wrong[1])
                        check('two wrong signs preserve progress and disable choices', 'maze.wrong.size===2&&maze.earned===0&&maze.phase==="play"')
                        for index in wrong[:2]:
                            button = page.get_by_role('button', name=re.compile('^' + ['Left', 'Up', 'Right', 'Down'][index] + ':'))
                            if not button.is_disabled():
                                raise AssertionError('Wrong sign remains enabled')
                        direction(start['correct'])
                        check('correct sign recovers and earns a note', 'maze.earned===1&&maze.wrong.size===0&&maze.canGuess')
                        sample(); press('Hear my collected notes'); settle()
                        press('Guess the song'); settle()
                        wrong_title = page.evaluate('store.data.strings["modules:101"][maze.songs[(maze.secret+1)%6]]')
                        press(wrong_title); settle()
                        check('wrong song requires another note', 'maze.eliminated.size===1&&maze.guessLocked&&!maze.canGuess&&!maze.chooser')
                        if not page.get_by_role('button', name='Guess the song', exact=True).is_disabled():
                            raise AssertionError('Guess button permits immediate second guess')
                        direction(sample()['correct'])
                        check('another note unlocks guessing', 'maze.canGuess&&!maze.guessLocked')
                    # Alternate early identification and collecting every note.
                    if round_index % 2 == 0:
                        if page.evaluate('maze.earned===0'):
                            direction(sample()['correct'])
                        press('Guess the song'); settle()
                        press(page.evaluate('maze.title')); settle()
                    else:
                        for step in range(30):
                            state = sample()
                            if state['phase'] == 'win':
                                break
                            # Keep one ordinary round at the easier difficulty
                            # through wrong answers, exercising its pitch sets.
                            if round_index == 1:
                                direction((state['correct'] + 1) % 4)
                            direction(state['correct'])
                        else:
                            raise AssertionError('Collecting notes never reached victory')
                    check(f'round {round_index+1} reaches complete win', 'maze.phase==="win"&&!maze.busy&&maze.earned===maze.song[0]')
                    won = page.evaluate('()=>({song:maze.activeSong,title:maze.title,earned:maze.earned})')
                    rounds.append(dict(start=start, win=won, method='guess' if round_index % 2 == 0 else 'all-notes'))
                    press('Hear the whole song'); settle()
                    check(f'round {round_index+1} song replay returns to win', 'maze.phase==="win"&&!maze.busy')
                    if round_index == 5:
                        page.screenshot(path=str(output/(label+'-win.png')), full_page=True)
                    press('Start a new maze'); settle()
                    check(f'round {round_index+1} restart replaces solved song', f'maze.phase==="play"&&maze.earned===0&&maze.activeSong!=={won["song"]}&&!maze.busy')
                press('Back to the piano'); settle()
                check('return reaches working piano', 'scene==="music"')
                report['journeys'].append(dict(name=label, actions=actions, rounds=rounds, passed=True))
                print(label, 'PASS', flush=True)
            except Exception as e:
                report['errors'].append(label+': '+str(e))
                report['journeys'].append(dict(name=label, actions=actions, rounds=rounds, passed=False))
                page.screenshot(path=str(output/(label+'-failure.png')), full_page=True)
                print(label, 'FAIL', str(e), flush=True)
            context.close()
        browser.close()
    report['challenge_types'] = sorted(types)
    report['scenes'] = sorted(scenes)
    report['checks'].append(dict(name='all five challenge types encountered', passed=types==set(range(5))))
    report['checks'].append(dict(name='all nine maze scenes encountered', passed=scenes==set(range(9))))
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Twelve visible-control wins in two fixed-clock desktop/touch sessions, including wrong directions, wrong song recovery, early guesses, collecting every note, song replay and restart. State is read to select answers; only the animation clock is advanced. No native comparison or timing equivalence claim.'
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']), types=sorted(types), scenes=sorted(scenes), errors=report['errors']), indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.exit(0 if verify(args.html, args.output) else 1)
