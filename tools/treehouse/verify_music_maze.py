"""Verify reconstructed maze frames and complete generated games."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=1000));page.add_init_script('requestAnimationFrame=()=>0;');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("setScene('maze')")
        def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
        for folder,name in [('playthrough','settled')]+[('playthrough',f'correct-{i}')for i in range(7)]+[('early-win','guess-open'),('early-win','win-settled')]:
            ref=DATA/f'research-music-maze/{folder}';ram=(ref/'state'/f'{name}.ram-0').read_bytes();base=0x318b0
            word=lambda offset:struct.unpack_from('<H',ram,base+offset)[0]
            y,x,b,r=struct.unpack_from('<4h',ram,base+0x9ba);py,px=struct.unpack_from('<hh',ram,0x323f0+0x2064)
            model=dict(node=word(0x9d4),choices=list(struct.unpack_from('<4H',ram,base+0xa1e)),type=word(0x26),earned=ram[base+0x9e6],secret=word(0x9ae),songs=list(struct.unpack_from('<6H',ram,base+0x922)),actor=[y+40,x+17],phase='win'if name=='win-settled'else'play',chooser=name=='guess-open',frog=name=='win-settled')
            page.evaluate('(model)=>{maze.cancel();Object.assign(maze,model);maze.actorAnimation=3;maze.actorFrame=0;maze.wrong=new Set();maze.eliminated=new Set();maze.guessLocked=false;maze.feedback=-1;maze.hint=false;maze.roller=null;maze.falling=null;}',model)
            page.evaluate(f'treehouseDemo.setPointer({px},{py});render()');image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB');original=Image.open(ref/'state'/f'{name}.png').convert('RGB');delta=ImageChops.difference(image,original);count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()));report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),observed_model=model);image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        # Independently render every source-defined drawer position against native callback images.
        ref=DATA/'research-music-maze/early-win';ram=(ref/'state/guess-open.ram-0').read_bytes();word=lambda o:struct.unpack_from('<H',ram,0x318b0+o)[0];y,x,_,_=struct.unpack_from('<4h',ram,0x318b0+0x9ba);py,px=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        page.evaluate("m=>{maze.cancel();Object.assign(maze,m);maze.frog=false;maze.actorAnimation=3;maze.actorFrame=0;maze.chooser=true;maze.guessHighlight=-1;maze.eliminated=new Set();treehouseDemo.setPointer(m.px,m.py);}",dict(node=word(0x9d4),choices=list(struct.unpack_from('<4H',ram,0x318b0+0xa1e)),type=word(0x26),earned=ram[0x318b0+0x9e6],secret=word(0x9ae),songs=list(struct.unpack_from('<6H',ram,0x318b0+0x922)),actor=[y+40,x+17],phase='play',px=px,py=py))
        for position in json.loads((ROOT/'testing/treehouse/maze-drawer-comparison.json').read_text())['positions']:
            page.evaluate('y=>{maze.drawerY=y;render();}',position['bar_y']);raw=base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]);image=Image.open(BytesIO(raw)).convert('RGB');example=position['examples'][0];original=Image.open(DATA/'research-music-maze'/example['root']/example['image']).convert('RGB');delta=ImageChops.difference(image,original);count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()));report['pixels'][f"drawer-{position['bar_y']}"]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox())
        page.evaluate('window.finishMaze=()=>{let n=0;while((maze.busy||roomTravel)&&n++<30000){advance(1);if(n%16===0)render();}if(maze.busy||roomTravel)throw new Error("Maze transition did not finish");render();return n;};maze.reset();finishMaze()')
        check('automatic replay preserves the independent hint deadline','(()=>{const hint=maze.hintDue;maze.hearTarget(true);finishMaze();return maze.hintDue===hint&&maze.targetDue===maze.tick+360;})()')
        check('idle sign hints preserve target replay deadline','(()=>{const target=maze.targetDue;maze.run(maze.idleHint());finishMaze();return maze.targetDue===target&&maze.hintDue===maze.tick+900;})()')
        check('empty replay flashes for twelve ticks','(()=>{maze.earned=0;maze.run(maze.emptyReplay());const red=maze.replaying;advance(11);const held=maze.replaying;advance();return red&&held&&!maze.replaying&&!maze.busy;})()')
        check('six unique offered songs','new Set(maze.songs).size===6&&maze.songs.every(i=>i>=0&&i<24)')
        check('first question uses instrument timbre','maze.type===4&&new Set(maze.choices).size===4')
        check('guess unavailable before first note','!maze.canGuess')
        check('wrong answer keeps scene and dims sign','(()=>{const node=maze.node,d=[0,1,2,3].find(d=>d!==maze.correct);maze.choose(d);finishMaze();return maze.node===node&&maze.earned===0&&maze.wrong.has(d)&&maze.streak===0;})()')
        check('correct answer earns note and follows original graph','(()=>{const expected=maze.t.neighbors[maze.node][maze.correct];maze.choose(maze.correct);finishMaze();return maze.node===expected&&maze.earned===1&&!maze.wrong.size&&maze.canGuess;})()')
        check('wrong song guess locks guesses until next stage','(()=>{maze.openGuess();finishMaze();const wrong=[0,1,2,3,4,5].find(i=>i!==maze.secret);maze.guess(wrong);finishMaze();return maze.eliminated.has(wrong)&&maze.guessLocked&&!maze.canGuess;})()')
        check('next earned note unlocks guessing and raises difficulty','(()=>{maze.choose(maze.correct);finishMaze();return maze.earned===2&&maze.canGuess&&maze.hard;})()')
        check('correct early guess reaches victory','(()=>{maze.openGuess();finishMaze();maze.guess(maze.secret);finishMaze();return maze.phase==="win"&&maze.node===9&&maze.frog;})()')
        check('victory melody includes complete advanced score','maze.melody(true).length===Array.from({length:maze.song[1]},(_,i)=>maze.song[5+2*i]&127).filter(p=>p!==127).length')
        check('victory guidance flashes both controls without changing songbook','(()=>{const songs=maze.songs.join();maze.run(maze.winHint());const a=[maze.controlFlash];advance(18);a.push(maze.controlFlash);advance(12);a.push(maze.controlFlash);advance(18);return JSON.stringify(a)==="[0,null,1]"&&maze.controlFlash===null&&maze.songs.join()===songs&&maze.hintDue===maze.tick+900;})()')
        check('new-game departure retains won title and score until next scene','(()=>{const won=maze.activeSong,title=maze.title,song=maze.song;maze.newGame();const ok=maze.activeSong===won&&maze.title===title&&maze.song===song&&maze.songs[maze.secret]!==won;finishMaze();return ok&&maze.phase==="play"&&maze.departureSong===null;})()')
        page.evaluate("maze.phase='win';maze.node=9;maze.frogPoint=[150,130]")
        check('new-game arrow starts a fresh maze','(()=>{maze.click(14,110);finishMaze();return maze.phase==="play"&&maze.earned===0&&maze.node<9;})()')
        check('ordinary click skips tutor and leaves playable challenge',"(()=>{maze.introduced=false;maze.reset();maze.click(160,170);finishMaze();return !maze.tutoring&&!maze.largeIntro&&maze.node<9&&maze.playerVisible&&maze.revealedSigns===4;})()")
        check('ordinary click interrupts replay without a stuck motion',"(()=>{maze.hearTarget();maze.click(160,170);finishMaze();return !maze.busy&&!maze.currentEvent;})()")
        check('completed round replaces exactly the previously selected song',"(()=>{const before=maze.songs.slice(),slot=maze.secret;maze.phase='win';maze.reset();finishMaze();return maze.songs.every((s,i)=>i===slot?s!==before[i]:s===before[i])&&new Set(maze.songs).size===6;})()")
        journeys=page.evaluate('''()=>{const games=[],types=new Set();let seed=7834;maze.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};for(let game=0;game<40;game++){maze.reset();finishMaze();if(game%2===0){maze.choose((maze.correct+1)%4);finishMaze();}let turns=0;while(maze.phase!=='win'&&turns++<30){types.add(maze.type);maze.choose(maze.correct);finishMaze();}games.push({turns,won:maze.phase==='win',notes:maze.earned,expected:maze.song[0]});}return{games,types:[...types].sort()};}''')
        report['generated_journeys']=journeys
        report['checks'].append(dict(name='40 complete generated maze games',passed=all(g['won']and g['notes']==g['expected']for g in journeys['games'])))
        report['checks'].append(dict(name='all five challenge types exercised',passed=journeys['types']==[0,1,2,3,4]))
        check('victory return enters piano','(()=>{maze.click(285,66);finishMaze();return scene==="music";})()')
        page.get_by_role('button',name='Play the musical maze',exact=True).click()
        page.evaluate("()=>{let n=0;while(roomTravel&&n++<3000)advance();render();}")
        check('readable controls open maze','scene==="maze"')
        page.evaluate('maze.reset();finishMaze()');page.get_by_role('button',name='Hear the sound again',exact=True).click()
        check('readable replay schedules target audio','maze.audioQueue.length>=0&&maze.audioDue>maze.tick')
        page.set_viewport_size(dict(width=390,height=844));page.screenshot(path=str(output/'mobile.png'),full_page=True)
        check('maze controls fit mobile','document.documentElement.scrollWidth<=window.innerWidth')
        page.keyboard.press('Escape');check('Escape returns to music','scene==="music"')
        report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());report['full_timing_parity']=False;browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items()if k!='generated_journeys'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
