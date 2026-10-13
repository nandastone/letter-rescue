"""Native editing/quiz frame comparisons and complete animal-game journeys."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import base64
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture_base(folder):
    run=json.loads((folder/'run.json').read_text())
    if 'main_image_base' in run:return run['main_image_base']
    return capture_base((ROOT/run['restore_source']).parent.parent)


def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport=dict(width=1360,height=960))
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.add_init_script('requestAnimationFrame=()=>0;');page.goto(html.resolve().as_uri())
        def check(value,label):
            report['checks'].append(dict(name=label,passed=bool(value)))
            if not value:raise AssertionError(label)
        def snapshot(name,folder,state,code='',after_release=None):
            ref=DATA/folder;run=json.loads((ref/'run.json').read_text());ram=(ref/'state'/f'{state}.ram-0').read_bytes()
            y,x=struct.unpack_from('<HH',ram,capture_base(ref)+0x321d0+0x2064)
            page.evaluate(code+f';treehouseDemo.setPointer({x},{y});render();')
            image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB')
            native=Image.open(ref/'state'/f'{state}.png').convert('RGB');window=0;matched=None
            if after_release:
                # The native snapshot is taken 180 frontend frames after the
                # notebook drop, while its curtain/preview may still be visible.
                # Compare full images through that recorded game-tick interval.
                before=(ref/'state'/f'{after_release}.ram-0').read_bytes();offset=capture_base(ref)+0x341ee
                window=struct.unpack_from('<I',ram,offset)[0]-struct.unpack_from('<I',before,offset)[0]
                assert 0<window<1000
                chosen=None
                for elapsed in range(window+1):
                    if image.tobytes()==native.tobytes() and chosen is None:chosen=image.copy();matched=elapsed
                    if elapsed<window:
                        page.evaluate('advance(1);render();')
                        image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB')
                if chosen is not None:image=chosen
            delta=ImageChops.difference(image,native)
            count=sum(a!=b for a,b in zip(image.getdata(),native.getdata()))
            report['pixels'][name]=dict(different_pixels=count,exact=count==0,bounds=delta.getbbox())
            if after_release:report['pixels'][name].update(recorded_interval_ticks=window,matched_tick=matched,scope='Full RGB membership in the recorded post-drop interval; not exact timestamp parity.')
            image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        page.evaluate("setScene('theater');theater.start();[0,0,1,1].forEach((v,c)=>theater.choose(c,v));advance(200)")
        snapshot('theater-options','theater-props','options','theater.options=true')
        snapshot('props-enabled','theater-props','props-enabled','theater.propsEnabled=true')
        snapshot('mix-enabled','theater-props','mix-enabled','theater.mixUp=true')
        snapshot('editor-options','theater-props','editor-options','theater.start();advance(64);theater.category=3')
        snapshot('props-list','theater-props','props-list','theater.showChoices(4)')
        page.evaluate('theater.category=3;theater.beginDrag(151,59);advance(16);theater.moveDrag(174,59);theater.endDrag();advance(100)')
        snapshot('token-swapped','research-theater-followup/correction-capture','swapped')
        check(page.evaluate('JSON.stringify(theater.order)==="[1,0,2,3]"'),'Held token swaps categories')
        snapshot('token-invalid-order','research-theater-followup/correction-capture','invalid-order','theater.play();advance(1000)')
        snapshot('token-corrected','research-theater-followup/correction-capture','corrected','theater.correct()')
        page.evaluate('theater.beginDrag(197,59);advance(16);theater.moveDrag(174,59);theater.endDrag();advance(100)')
        snapshot('token-separated','research-theater-followup/correction-capture','separated')
        snapshot('token-invalid-gap','research-theater-followup/correction-capture','invalid-gap','theater.play();advance(1000)')
        snapshot('token-gap-corrected','research-theater-followup/correction-capture','gap-corrected','theater.correct()')
        page.evaluate('theater.beginDrag(220,59);advance(16);theater.moveDrag(40,59);theater.endDrag();advance(100)')
        snapshot('token-deleted','research-theater-followup/correction-capture','deleted-time')
        check(page.evaluate('theater.selection[3]===-1'),'Dropping token left of x67 deletes category')
        page.evaluate('theater.choose(3,1);theater.beginDrag(151,59);advance(16);theater.moveDrag(174,59);theater.endDrag();advance(100);theater.play();advance(1000);theater.beginDrag(151,59);advance(16);theater.moveDrag(174,59);theater.endDrag();advance(100)')
        snapshot('token-manually-corrected','research-theater-followup/correction-edge-capture','manually-corrected')
        check(page.evaluate('theater.previousValidation===5'),'Manual correction retains previous validation')
        snapshot('token-success-feedback','research-theater-followup/correction-edge-capture','success-feedback','theater.play();advance(3000)')
        page.evaluate('theater.choose(2,-1);theater.order=[0,3,2,1];theater.play();advance(1000)')
        snapshot('token-empty-slot-gap','research-theater-followup/correction-edge-capture','gap-feedback')
        snapshot('token-fill-before-action','research-theater-followup/correction-edge-capture','fills-before-action','theater.correct()')
        check(page.evaluate('JSON.stringify(theater.order)==="[2,3,0,1]"'),'Correction fills empty slot before action without moving leading words')
        page.evaluate('theater.beginDrag(35,106);advance(16);theater.moveDrag(151,59);const savedRandom=gameplayRandom.pick;gameplayRandom.pick=()=>0;theater.endDrag();gameplayRandom.pick=savedRandom;void 0;')
        snapshot('token-notebook-add','research-theater-followup/correction-edge-capture','add-place',after_release='add-place-drag')
        page.evaluate('theater.beginDrag(151,59);advance(16);theater.moveDrag(200,120);theater.endDrag();advance(100)')
        snapshot('token-stage-drop','research-theater-followup/correction-edge-capture','outside-drop')
        check(page.evaluate('theater.selection[2]===0'),'Dropping a token on the stage restores it')
        page.evaluate('theater.shuffle();advance(1000)')
        check(page.evaluate('!theater.tokenSequence&&new Set(theater.order).size===4'),'Animated shuffle completes and preserves four unique categories')
        # This fixture is a fresh original session; persistence is tested separately.
        page.evaluate("localStorage.removeItem('treehouse-theater-v1');theater=null;setScene('theater');theater.start();theater.play();advance(1000)")
        snapshot('invalid-empty','research-theater/invalid-empty-a','invalid-empty')
        page.evaluate('theater.choose(0,0);theater.play();advance(1000)')
        snapshot('invalid-actor','research-theater/invalid-actor-a','invalid-actor')
        page.evaluate('theater.choose(2,0);theater.propsEnabled=true;theater.addProp(0);')
        check(page.evaluate('theater.beginDrag(161,116);theater.moveDrag(20,30);theater.endDrag();theater.props[0].length===0'), 'Theater prop dragged outside is removed')
        page.evaluate('theater.addProp(0);theater.beginDrag(161,116);theater.moveDrag(102,60);theater.endDrag();')
        check(page.evaluate('theater.props[0][0].x===103'), 'Partially overlapping theater prop clamps inside on release')
        page.evaluate('theater.choose(2,-1);const rect=theater.actorRect();theater.beginDrag(rect[1]+1,rect[0]+1);')
        check(page.evaluate('!theater.moveDrag(210,120)'), 'Actor drag waits fifteen original ticks')
        page.evaluate('advance(16);theater.moveDrag(210,120);theater.endDrag()')
        check(page.evaluate('theater.actorRect()[1]>=103&&theater.actorRect()[3]<=261'), 'Actor drag stays in original stage bounds')
        page.evaluate("setScene('nature');nature.time=1;nature.attribute=6;nature.values[6]=1;nature.selectClass(0);nature.selectAnimal(1);nature.factIndex=2")
        snapshot('animal-fact','nature-explore','animal')
        page.evaluate('nature.enterQuiz()')
        snapshot('quiz-options','research-nature/quiz-capture','quiz-options')
        snapshot('quiz-ready','research-nature/quiz-capture','quiz-ready','nature.quiz.start()')
        # Native state supplies the random deal, never pixels or code. The game
        # independently renders and operates these ordinary model records.
        ref=DATA/'research-nature/quiz-roll-capture';run=json.loads((ref/'run.json').read_text());ram=(ref/'state/quiz-roll.ram-0').read_bytes();base=run['main_image_base']
        cards=struct.unpack_from('<16H',ram,base+0x31690+6)
        questions=struct.unpack_from('<8h',ram,base+0x321d0+0x52a2)
        secrets=struct.unpack_from('<2H',ram,base+0x31690+0x992)
        page.evaluate('data=>{Object.assign(nature.quiz,data);}',dict(cards=[list(cards[:8]),list(cards[8:])],secret=list(secrets),player=0,phase='question',available=[i for i,v in enumerate(questions)if v]))
        snapshot('quiz-deal','research-nature/quiz-roll-capture','quiz-roll')
        for state,index in [('definition-backbone',0),('definition-legs',3),('definition-active',7)]:
            snapshot(state,'research-nature-followup/capture-a',state,f'nature.quiz.inspectAttribute({index})')
        for state,index in [('inspect-first',0),('inspect-second',1)]:
            snapshot(state,'research-nature-followup/capture-a',state,f'nature.quiz.choose({index})')
        page.evaluate('nature.quiz.selected=-1;nature.quiz.selectedAttribute=-1;nature.quiz.explanation=""')
        def quiz_state(folder,state):
            ref=DATA/folder;ram=(ref/'state'/f'{state}.ram-0').read_bytes();base=capture_base(ref);ds=base+0x321d0
            cards=struct.unpack_from('<16H',ram,base+0x31690+6);secrets=struct.unpack_from('<2H',ram,base+0x31690+0x992)
            return dict(cards=[list(cards[:8]),list(cards[8:])],secret=list(secrets),remaining=list(struct.unpack_from('<2H',ram,ds+0x52ee)),player=struct.unpack_from('<H',ram,ds+0x5250)[0])
        page.evaluate('data=>{Object.assign(nature.quiz,data);}',quiz_state('research-nature/quiz-answer-capture','quiz-answer'))
        snapshot('quiz-answer','research-nature/quiz-answer-capture','quiz-answer','nature.quiz.ask(1);advance(3000)')
        page.evaluate('data=>{nature.quiz.start();Object.assign(nature.quiz,data);nature.quiz.phase="question";nature.quiz.guess(nature.quiz.secret[nature.quiz.player]);advance(3000);}',quiz_state('research-nature/quiz-win-capture','correct-guess'))
        snapshot('quiz-win','research-nature/quiz-win-capture','correct-guess')
        for game in range(30):
            result=page.evaluate('''()=>{const q=nature.quiz;q.opponent=1;q.help=[true,true,true];q.start();q.roll();advance(3000);let turns=0;
              for(;turns<40&&q.winner<0;turns++){
                const keep=Array.from({length:8},(_,i)=>i).filter(i=>q.remaining[q.player]&(1<<i));
                if(keep.length===1)q.guess(keep[0]);else q.ask(q.available.find(i=>!(q.asked[q.player]&(1<<i)))??q.available[0]);
                advance(3000);if(!(q.remaining[q.player]&(1<<q.secret[q.player])))throw Error('Secret was incorrectly eliminated');
                if(q.winner<0){q.roll();advance(3000);}
              }
              render();return{won:q.winner>=0,distinct:q.cards.every(ids=>new Set(ids.map(id=>q.attributes(id).join(','))).size===8),turns};}''')
            check(result['won'] and result['distinct'],f'Game {game}: distinguishable candidates and completed winning journey')
        page.evaluate('nature.quiz.opponent=2;nature.quiz.start();nature.quiz.roll();advance(3000);nature.quiz.ask(nature.quiz.available[0]);advance(3000);nature.quiz.roll();advance(3000)')
        check(page.evaluate('nature.quiz.player===1&&nature.quiz.phase==="answered"'), 'Robot asks and waits for the player to roll, as in DOS')
        page.evaluate('nature.quiz.start();nature.quiz.roll();advance(3000);nature.quiz.help[0]=true;const q=nature.quiz;const wrong=(q.secret[q.player]+1)%8;q.guess(wrong);advance(3000);')
        check(page.evaluate('nature.quiz.winner<0&&nature.quiz.phase==="answered"'), 'Incorrect guess continues the game')
        page.evaluate('nature.quiz.options=true;nature.quiz.changed()')
        page.locator('#quiz-opponent').select_option('1')
        page.locator('#quiz-help-0').check()
        page.get_by_role('button',name='Start the guessing game',exact=True).click()
        page.get_by_role('button',name='Roll for the next turn',exact=True).click()
        page.evaluate('for(let i=0;i<3000&&nature.quiz.busy;i++)advance()')
        check(page.evaluate('nature.quiz.phase==="question"&&nature.quiz.available.length===3'), 'Readable controls start a guessing game')
        page.screenshot(path=str(output/'quiz-browser.png'),full_page=True)
        page.set_viewport_size(dict(width=390,height=844));page.screenshot(path=str(output/'quiz-mobile.png'),full_page=True)
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Quiz mobile layout fits')
        page.get_by_role('button',name='Back',exact=True).click()
        check(page.evaluate('nature.mode==="explore"'), 'Back returns from quiz to nature')
        check(not report['errors'],'No browser exceptions')
        browser.close()
    report['passed']=all(v['passed']for v in report['checks']);report['all_reference_frames_exact']=all(v['exact']for v in report['pixels'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,default=DATA/'continuation-build/index.html')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify(args.html,args.output)
