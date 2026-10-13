"""Complete guessing games and collect prizes using only visible controls.

The clock is stepped to avoid waiting through every animation in real time.
Model state is read to choose test answers and assert results; it is never set.
These are browser integration journeys, not native timing-parity evidence.
"""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[],journeys=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for touch,opponent,helped,seek_robot in [(False,1,False,False),(False,2,True,False),(True,1,True,False),(True,2,False,False),(False,2,False,True),(True,2,False,True)]:
            label=f'{"touch" if touch else "desktop"}-{"robot" if opponent==2 else "friend"}-{"helped" if helped else "manual"}'
            if seek_robot:label+='-robot-winner'
            context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=844 if touch else 960),has_touch=touch,is_mobile=touch,timezone_id='Australia/Brisbane')
            page=context.new_page();page.set_default_timeout(5000);page.add_init_script('''{const NativeDate=Date,fixed=Date.parse('2026-09-28T10:00:00+10:00');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;''')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri());actions=[]
            def check(name,expression):
                ok=bool(page.evaluate(expression));report['checks'].append(dict(name=label+': '+name,passed=ok))
                if not ok:raise AssertionError(name)
            def press(name):
                b=page.get_by_role('button',name=name,exact=True);b.tap() if touch else b.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');actions.append(name)
            def settle():
                result=page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||rewards.active&&rewards.phase!=='choose'||scene==='theater'&&(theater.presentation||theater.playing||theater.tokenSequence||theater.previewCategory>=0)||scene==='nature'&&nature.mode==='quiz'&&(nature.quiz.busy||nature.quiz.winAnimation&&!nature.quiz.winAnimation.done||nature.quiz.phase==='question'&&nature.quiz.role()===2);while(busy()&&n++<30000)advance();render();return {done:!busy(),ticks:n};}''')
                if not result['done']:raise AssertionError('Action did not settle')
            def human_turn():
                for _ in range(8):
                    settle()
                    if page.evaluate('nature.quiz.winner>=0'):return False
                    if page.evaluate('nature.quiz.phase==="question"&&nature.quiz.role()!==2'):return True
                    press('Roll for the next turn')
                raise AssertionError('No human turn reached')
            try:
                press('Choose the girl' if touch else 'Choose the boy');settle()
                press('Explore nature');settle();press('Play the animal guessing game')
                page.locator('#quiz-opponent').select_option(str(opponent));page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                page.locator('#quiz-help-0').set_checked(helped)
                if opponent==1:page.locator('#quiz-help-1').set_checked(helped)
                press('Start the guessing game');human_turn()
                check('game deals two complete candidate sets','nature.quiz.cards.every(c=>c.length===8)&&nature.quiz.winner===-1')
                # Keep a wrong candidate for the next step even when help is
                # enabled; the first offered question can identify the answer.
                question=page.evaluate('''()=>{const q=nature.quiz,answer=q.attributes(q.cards[q.player][q.secret[q.player]]),count=a=>q.cards[q.player].filter((id,i)=>(q.remaining[q.player]&(1<<i))&&q.attributes(id)[a]===answer[a]).length,attribute=[...q.available].sort((a,b)=>count(b)-count(a))[0];return 'Ask about '+nature.strings(5300)[attribute].toLowerCase();}''')
                press(question);settle();check('question produces an answer and ends its turn','nature.quiz.phase==="answered"&&!!nature.quiz.answer')
                human_turn();press('Make a guess');settle()
                wrong=page.evaluate('()=>{const q=nature.quiz,i=q.cards[q.player].findIndex((_,i)=>i!==q.secret[q.player]&&(q.remaining[q.player]&(1<<i)));return i<0?null:nature.name(q.cards[q.player][i]);}')
                if wrong is None:raise AssertionError('No wrong candidate available')
                press('Guess '+wrong);settle();check('wrong guess allows the game to continue','nature.quiz.winner===-1&&nature.quiz.phase==="answered"')
                next_human=human_turn()
                if seek_robot:
                    # Exercise robot prize ownership deliberately, rather than
                    # depending on an incidental robot win in another route.
                    for _ in range(32):
                        if not next_human:break
                        press(page.get_by_role('button').filter(has_text='Ask about ').first.inner_text());settle()
                        next_human=human_turn()
                    check('robot reaches its own winning ending','nature.quiz.winner===1')
                if next_human:
                    press('Make a guess');settle()
                    answer=page.evaluate('()=>{const q=nature.quiz;return nature.name(q.cards[q.player][q.secret[q.player]]);}')
                    press('Guess '+answer);settle()
                check('correct guess completes celebration','nature.quiz.winner>=0&&nature.quiz.winStage==="done"&&!nature.quiz.busy')
                press('See the other animal');settle();check('both secret animals can be revealed','nature.quiz.revealed===3')
                press('Choose a prize');settle();check('winner reaches prize chooser','rewards.active&&rewards.phase==="choose"&&rewards.role===(nature.quiz.winner===0?0:nature.quiz.opponent)')
                robot_prize=page.evaluate('rewards.role===2')
                # Pick a new non-food room object when offered, avoiding ambient
                # consumption as a source of ambiguity in the reload assertion.
                choice=0 if robot_prize else page.evaluate('()=>{const slot=rewards.choices.findIndex(id=>[0,1,2,5,7].includes(id)&&!resident.objects.some(o=>o.type===id));return slot>=0?slot:0;}')
                prize=page.evaluate('(i)=>rewards.choices[i]',choice)
                name=page.locator('#controls button').nth(choice).inner_text();press(name);settle()
                check('prize reaches winner inventory',f'rewards.shelf[{choice}]' if robot_prize else f'resident.objects.some(o=>o.type==={prize})')
                check('award resets to a playable new game','!rewards.active&&nature.quiz.phase==="ready"&&nature.quiz.winner===-1&&!nature.quiz.options')
                press('Back');press('Back');settle();check('return from prize game reaches room','scene==="inside"&&!roomTravel')
                page.screenshot(path=str(output/(label+'-room.png')),full_page=True)
                if robot_prize:
                    press('Look through the telescope');settle();page.evaluate('advance(1500);render()')
                    check('earned robot prize selects the shelf on the next telescope visit', 'scene==="telescope"&&telescope===3&&rewards.visited===15')
                    check('robot prize is visible on its telescope shelf',f'scene==="telescope"&&telescope===3&&rewards.shelf[{choice}]')
                    press('Back');settle();press('Put on a play');settle();press('Back');settle()
                    check('robot shelf ownership survives another activity',f'rewards.shelf[{choice}]&&scene==="inside"')
                page.reload()
                check('prize lifetime matches its owner', '!rewards.shelf.some(Boolean)' if robot_prize else f'resident.objects.some(o=>o.type==={prize})')
                report['journeys'].append(dict(name=label,actions=actions,prize=prize,robot_prize=robot_prize,passed=True))
                print(label,'PASS',flush=True)
            except Exception as e:
                report['errors'].append(label+': '+str(e));report['journeys'].append(dict(name=label,actions=actions,passed=False))
                page.screenshot(path=str(output/(label+'-failure.png')),full_page=True)
                print(label,'FAIL',str(e),flush=True)
            context.close()
        browser.close()
    report['checks'].append(dict(name='both human and robot prize ownership covered',passed=any(j.get('robot_prize') is True for j in report['journeys']) and any(j.get('robot_prize') is False for j in report['journeys'])))
    report['passed']=not report['errors'] and len(report['journeys'])==6 and all(c['passed'] for c in report['checks'])
    report['scope']='Six fresh ordinary-control browser journeys: four desktop/touch friend/robot helped/manual variants and explicit mouse/boy and touch/girl robot-winner routes. Question, wrong guess, recovery, human/robot wins, both reveals, prize transfer, next game, return and reload. Human prizes persist; robot prizes automatically select the telescope shelf on the next visit, survive another activity, and remain session-only. No explicit shelf-selection button is used to bypass next-view selection. Initial calendar/BIOS-seed clock fixed to 2026-09-28 10:00 Brisbane; game clock accelerated; answers read from current state. No native timing or exhaustive branch claim.'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.html,a.output) else 1)
