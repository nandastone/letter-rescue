"""Ordinary activity returns with overdue character reminders."""
from pathlib import Path
import argparse, hashlib, json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport=dict(width=1360, height=960))
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())

        def press(name):
            page.get_by_role('button', name=name, exact=True).click()
            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            assert page.evaluate('()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}')

        try:
            press('Choose the boy')
            # Observe real action dispatch/completion without replacing gameplay.
            page.evaluate('''()=>{
              window.returnActions=[];window.actionFinishes=[];window.returnEnds=[];
              const travel=updateRoomTravel;updateRoomTravel=function(){const returning=!!roomTravel?.returning;const result=travel();if(returning&&!roomTravel)returnEnds.push({tick,hunger:resident.hunger,fatigue:resident.fatigue,hungerDue:resident.hungerDue,fatigueDue:resident.fatigueDue});return result;};
              const action=resident.action,finish=resident.finishAction;
              resident.action=function(id,after){returnActions.push({id,tick,returning:!!roomTravel?.returning});return action.call(this,id,after);};
              resident.finishAction=function(){const before={id:this.active.action,tick,seed:gameplayRandom.seed};
                const result=finish.call(this);actionFinishes.push({...before,after:gameplayRandom.seed,due:this.ambientDue});return result;};
            }''')
            for _ in range(3):
                press('Make some music'); page.evaluate('advance(18000);render()'); press('Back');page.evaluate('advance(601);let n=0;while((resident.busy||room.busy)&&n++<30000)advance();render()')
                if page.evaluate('actionFinishes.some(a=>a.id===13)'):
                    break
            actions = page.evaluate('returnActions'); finishes = page.evaluate('actionFinishes')
            ends=page.evaluate('returnEnds');report.update(actions=actions, finishes=finishes, return_ends=ends)
            report['checks'].append(dict(name='return gives urgent needs at least 600 ticks',passed=bool(ends) and all(e[name]<3 or e[name+'Due']-e['tick']>=600 for e in ends for name in ['hunger','fatigue'])))
            reminders = [a for a in finishes if a['id'] == 13]
            report['checks'].append(dict(name='ordinary return reaches overdue hunger reminder', passed=bool(reminders)))
            report['checks'].append(dict(name='reminders start after return effect', passed=bool(actions) and not any(a['returning'] for a in actions)))
            for a in reminders:
                expected = (a['seed']*214013+2531011) & 0xffffffff
                delay = 60*(20+((expected >> 16) % 11))
                report['checks'].append(dict(name='finished reminder schedules original ambient delay and random draw', passed=a['after']==expected and a['due']==a['tick']+delay, actual=a))
        except Exception as e:
            report['errors'].append(str(e))
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Fresh ordinary controls with accelerated activity time; no gameplay-state installation. Tests return/action order and original action-wrapper ambient scheduling. Full native image/timing comparison remains separate.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL', report['checks'], report['errors'])
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output) else 1)
