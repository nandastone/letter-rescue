"""Play complete money/chip games using visible controls at every goal level.

Current board state selects test moves; gameplay state is never installed.
Animation time is accelerated. These checks establish browser integration only.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from playwright.sync_api import sync_playwright


def verify(html, output, money_loss_only=False):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[], journeys=[])
    exchanges = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for mode in ([0] if money_loss_only else range(2)):
            for opponent in [1, 2]:
                scenarios=[(2,True,False),(2,True,True)] if money_loss_only else [(level,False,level==1) for level in range(3)]
                if not money_loss_only and mode==0 and opponent==1:scenarios.append((2,True,False))
                for level,seek_loss,touch in scenarios:
                    label = f'{"chips" if mode else "money"}-{ "robot" if opponent==2 else "friend"}-goal{level}-{ "touch" if touch else "desktop"}'
                    if seek_loss:label+='-payment-loss'
                    context = browser.new_context(viewport=dict(width=390 if touch else 1360, height=960), has_touch=touch, is_mobile=touch, timezone_id='Australia/Brisbane')
                    page = context.new_page(); page.set_default_timeout(5000)
                    page.add_init_script("{const NativeDate=Date,fixed=Date.parse('2026-09-28T10:00:00+10:00');globalThis.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;}};}requestAnimationFrame=()=>0;")
                    page.on('pageerror', lambda e: report['errors'].append(str(e)))
                    page.goto(html.resolve().as_uri())
                    actions, turns, trades, endings = [], [], [], []
                    rejected_road = False
                    rejected_trade = False

                    def check(name, expression):
                        ok = bool(page.evaluate(expression))
                        report['checks'].append(dict(name=label+': '+name, passed=ok))
                        if not ok:
                            raise AssertionError(name)

                    def press(name):
                        button = page.get_by_role('button', name=name, exact=True)
                        button.tap() if touch else button.click()
                        actions.append(name)

                    def settle():
                        state = page.evaluate('''()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||rewards.active&&rewards.phase!=='choose'||scene==='boardgame'&&(boardgame.motion.busy||boardgame.moving||boardgame.phase==='rolling')&&!(boardgame.phase==='exchange'&&!boardgame.motion.accepted);while(busy()&&n++<30000)advance();render();return {done:!busy(),phase:boardgame?.phase};}''')
                        if not state['done']:
                            raise AssertionError('Animation did not settle: '+state['phase'])

                    def canvas_click(point):
                        canvas = page.locator('#game')
                        canvas.scroll_into_view_if_needed()
                        box = canvas.bounding_box()
                        x, y = box['x']+point[0]*box['width']/320, box['y']+point[1]*box['height']/200
                        page.touchscreen.tap(x,y) if touch else page.mouse.click(x,y)
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                        actions.append(dict(canvas=point))

                    try:
                        press('Choose the girl' if touch else 'Choose the boy'); settle()
                        press('Play the board game'); settle()
                        page.locator('#board-mode').select_option(str(mode))
                        page.locator('#board-opponent').select_option(str(opponent))
                        page.locator('#board-goal-0').select_option(str(level))
                        if opponent == 1:
                            page.locator('#board-goal-1').select_option(str(level))
                        press('Start the board game'); settle()
                        check('selected game starts', f'!boardgame.options&&boardgame.mode==={mode}&&boardgame.opponent==={opponent}&&boardgame.levels.every(n=>n==={level})')
                        # One route deliberately seeks payments and a loss;
                        # other routes favour player zero while playing both seats.
                        preferred_winner = -1 if level == 0 or seek_loss else 0
                        for game_index in range(8 if money_loss_only else 1):
                            for step in range(1200):
                                state = page.evaluate('()=>({phase:boardgame.phase,player:boardgame.player,winner:boardgame.winner,loser:boardgame.loser,balance:[...boardgame.balances],remaining:boardgame.remaining,exchange:boardgame.exchange})')
                                if state['winner'] >= 0 or state['loser'] >= 0:
                                    result = state
                                    break
                                phase = state['phase']
                                if phase in ['ready', 'result']:
                                    turns.append(state); press('Roll for the next turn')
                                elif phase == 'move':
                                    if not rejected_road:
                                        bad = page.evaluate('''()=>{const g=boardgame;for(let n=0;n<24;n++)if(!g.neighbours().includes(n)&&g.findPath(n)===null)return {point:g.center(n),node:g.nodes[g.player],remaining:g.remaining};return null;}''')
                                        if bad:
                                            canvas_click(bad['point']); settle()
                                            check('unreachable road is rejected without spending moves', f'boardgame.phase==="move"&&boardgame.nodes[boardgame.player]==={bad["node"]}&&boardgame.remaining==={bad["remaining"]}')
                                            rejected_road = True
                                    direction = page.evaluate('''preferred=>{const g=boardgame,favour=g.player===preferred,rank=favour?[23,24,25,26]:[26,25,24,23],targets=Array.from({length:24},(_,i)=>i).sort((a,b)=>rank.indexOf(g.types[a])-rank.indexOf(g.types[b]));for(const target of targets){const path=g.findPath(target);if(path?.length)return g.tables.adjacency[g.nodes[g.player]].indexOf(path[0]);}return -1;}''', preferred_winner)
                                    if direction < 0:
                                        raise AssertionError('No legal road')
                                    press('Drive '+['left','up','right','down'][direction])
                                elif phase == 'reward':
                                    choice = page.evaluate('''preferred=>{const g=boardgame,more=g.rewards[0]>=g.rewards[1]?0:1;return g.player===preferred?more:1-more;}''', preferred_winner)
                                    press('Choose the '+(['left','right'] if mode else ['upper','lower'])[choice]+' amount')
                                elif phase == 'exchange':
                                    trades.append(state['exchange']); exchanges.add(state['exchange']['kind'])
                                    if not rejected_trade:
                                        point = page.evaluate('()=>{const g=boardgame,r=g.tables.chip_rects[1+(g.exchange.digit+1)%3];return [(r[1]+r[3])/2,(r[0]+r[2])/2];}')
                                        canvas_click(point); settle()
                                        check('wrong chip stack leaves trade pending', 'boardgame.phase==="exchange"&&!boardgame.motion.accepted')
                                        rejected_trade = True
                                    press('Trade these chips')
                                else:
                                    raise AssertionError('Unexpected settled phase: '+phase)
                                settle()
                            else:
                                raise AssertionError('Game did not finish in 1200 actions')
                            check('game ends after complete transfer and celebration', '!boardgame.motion.busy&&!boardgame.transfer&&boardgame.phase==="result"&&(boardgame.winner>=0||boardgame.loser>=0)')
                            check('balances respect win or loss', 'boardgame.winner>=0?boardgame.balances[boardgame.winner]>=boardgame.goal(boardgame.winner):boardgame.balances[boardgame.loser]===0')
                            if not rejected_road:
                                raise AssertionError('No invalid road checked')
                            press('Choose a prize'); settle()
                            check('winner receives the prize chooser', 'rewards.active&&rewards.phase==="choose"&&rewards.role===((boardgame.winner>=0?boardgame.winner:1-boardgame.loser)===0?0:boardgame.opponent)')
                            robot_prize = page.evaluate('rewards.role===2')
                            choice = 0 if robot_prize else page.evaluate('()=>{const i=rewards.choices.findIndex(id=>[0,1,2,5,7].includes(id)&&!resident.objects.some(o=>o.type===id));return i>=0?i:0;}')
                            prize = page.evaluate('(i)=>rewards.choices[i]', choice)
                            press(page.locator('#controls button').nth(choice).inner_text()); settle()
                            check('prize is delivered', f'rewards.shelf[{choice}]' if robot_prize else f'resident.objects.some(o=>o.type==={prize})')
                            check('new game is playable', '!rewards.active&&!boardgame.options&&boardgame.winner===-1&&boardgame.loser===-1&&boardgame.phase==="ready"')
                            endings.append(dict(result=result, robot_prize=robot_prize, prize=prize))
                            if not money_loss_only or result['loser'] >= 0:
                                break
                        else:
                            raise AssertionError('No payment loss in eight complete games')
                        if seek_loss:
                            report['checks'].append(dict(name=label+': ordinary money payments reach a losing ending', passed=result['loser']>=0 and result['winner']==-1))
                            if result['loser'] < 0:
                                raise AssertionError('No payment loss')
                        press('Back'); settle()
                        check('return reaches room', 'scene==="inside"&&!roomTravel')
                        page.screenshot(path=str(output/(label+'-room.png')), full_page=True)
                        page.reload()
                        check('prize has correct reload lifetime', '!rewards.shelf.some(Boolean)' if robot_prize else f'resident.objects.some(o=>o.type==={prize})')
                        report['journeys'].append(dict(name=label, actions=actions, turns=turns, trades=trades, endings=endings, result=result, robot_prize=robot_prize, prize=prize, passed=True))
                        print(label, 'PASS', flush=True)
                    except Exception as e:
                        report['errors'].append(label+': '+str(e))
                        report['journeys'].append(dict(name=label, actions=actions, turns=turns, trades=trades, endings=endings, passed=False))
                        page.screenshot(path=str(output/(label+'-failure.png')), full_page=True)
                        print(label, 'FAIL', str(e), flush=True)
                    context.close()
        browser.close()
    report['exchange_kinds'] = sorted(exchanges)
    if not money_loss_only:
        report['checks'].append(dict(name='carry and borrow occur through gameplay', passed=exchanges=={'carry','borrow'}))
        report['checks'].append(dict(name='both winning and losing endings occur', passed=any(j.get('result',{}).get('winner',-1)>=0 for j in report['journeys']) and any(j.get('result',{}).get('loser',-1)>=0 for j in report['journeys'])))
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Thirteen ordinary-control money/chip games: both opponents and all three goals, plus an explicit money-payment loss route, through endings, prize selection, transfer, restart, room and reload. Read-only answer oracle and accelerated animation clock. No native timing or image comparison claim.'
    if money_loss_only:
        report['checks'].append(dict(name='all four friend/robot and mouse/touch loss journeys complete', passed=len(report['journeys'])==4 and all(j['passed'] for j in report['journeys'])))
        report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
        report['scope'] = 'Four fresh ordinary-control money games at the highest goal: friend/robot with mouse/touch, prioritizing payments and playing up to eight consecutive games without state injection, through required losing ending, prize selection, delivery, restart, room and reload. Read-only path oracle and accelerated animation clock. No native image/timing claim.'
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']), exchanges=sorted(exchanges), errors=report['errors']), indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.exit(0 if verify(args.html, args.output) else 1)
