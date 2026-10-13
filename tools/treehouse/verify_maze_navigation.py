"""Compare maze navigation, room state and RGB after one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
import browser_audio_observation as audio_observation
from verify_board_native_journey import model as board_model
from verify_music_native_journey import active_song

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'

def music_model(path):
    ram=path.read_bytes();ds=0x323f0
    word=lambda at:struct.unpack_from('<H',ram,at)[0]
    adjust=16*word(ds+0x4a54)-(544+0x2f180);shared=16*word(ds+0x4a22)-adjust
    off,seg=struct.unpack_from('<HH',ram,ds+word(ds+0x528e));song=seg*16+(off&15)+6-adjust
    advanced=bool(word(shared+0xa4));composing=bool(word(shared+0xa2))
    return dict(advanced=advanced,composing=composing,page=ram[shared+0x9e+2*advanced+composing],song=active_song(list(ram[song:song+65]),int(advanced)))


def verify(html,output,reference,observe_room=False):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['passed']
    m=native['checkpoints'][0]['after'];ram=(reference/'state/initial.ram-0').read_bytes();low=(reference/'state/initial.ram-100000').read_bytes()
    m['secondsOfDay']=struct.unpack_from('<I',low,0x46c)[0]*65536/1193181
    m['actor']=list(struct.unpack_from('<4h',ram,0x318b0+0x9ba));m['frog']=list(struct.unpack_from('<4h',ram,0x318b0+0x9c2))
    m['earned']=ram[0x318b0+0x9e6];m['mazeTimers']=list(struct.unpack_from('<2H',ram,0x323f0+0x2018))
    m['selection']=list(ram[0x318b0+0x9e:0x318b0+0xa2]);m['composing']=bool(struct.unpack_from('<H',ram,0x318b0+0xa2)[0]);m['advanced']=bool(struct.unpack_from('<H',ram,0x318b0+0xa4)[0])
    m['listeningPreferences']=[list(ram[544+0x2f180+offset:544+0x2f180+offset+50]) for offset in (0x75f,0x791,0x7c3)]
    m['musicIdleDue']=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),checks=[],pixels={},checkpoints=[],errors=[],native_input_schedule={c['name']:dict(click=any(a['left'] for a in c['inputs']),inputs=c['inputs']) for c in native['checkpoints']})
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960));page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        page.evaluate('''async m=>{
          await audio.unlock();character=m.sex?'girl':'boy';resident.selected=m.selected;setScene('maze');maze.cancel();Object.assign(maze,m.maze);maze.history=new Set(m.maze.history);maze.random=null;maze.started=true;maze.introduced=true;maze.roundReplaced=false;maze.initialAdvanced=m.maze.hard;gameSave.preferences.advanced=m.maze.hard;
          maze.phase=m.scene===17?'win':'play';maze.actor=[m.actor[0]+40,m.actor[1]+17];maze.actorAnimation=3;maze.actorFrame=0;maze.frog=m.scene===17;maze.frogPoint=[m.frog[0]+38,m.frog[1]+17];maze.frogAnimation=3;maze.frogFrame=0;maze.earned=m.earned;maze.wrong=new Set();maze.eliminated=new Set();maze.guessLocked=false;maze.feedback=-1;maze.hint=false;maze.roller=null;maze.falling=null;maze.targetDue=tick+m.mazeTimers[0];maze.hintDue=tick+m.mazeTimers[1];
          resident.objects=m.objects.map(o=>({...o,due:tick+o.due-m.tick}));balloon.hidden=!resident.objects.some(o=>o.type===6);
          for(const o of resident.objects){resident.setBounds(o,o.rect);if(o.type===6)balloon.due=o.due;}
          const start=tick,date=new Date(+new Date(1992,0,1)+m.secondsOfDay*1000);
          room.now=()=>new Date(+date+(tick-start)*1000/TICK_HZ);room.date=new Date(m.date[0],m.date[1]-1,m.date[2]);room.portraitFrame=null;room.cloud=m.cloud;room.cloudX=m.cloudX;room.cloudDue=tick+m.windowRemaining;room.height=room.target=m.calendarOpen?98:28;chalk.select(m.chalkTool);
          for(const k of ['pose','hunger','fatigue','outsideCycle'])resident[k]=m[k];for(const k of ['ambientDue','longDue','hungerDue','fatigueDue'])resident[k]=tick+m[k]-m.tick;resident.windowDue=tick+m.windowRemaining;
          songId=m.selection[Number(m.advanced)*2];musicEditor.enabled=m.composing;longScore=musicEditor.advanced=m.advanced;
          for(let mode=0;mode<2;mode++)for(let id=0;id<25;id++)for(let field=0;field<3;field++)listeningBooks.songs[mode][id][field+2]=m.listeningPreferences[field][mode*25+id];
          if(m.scene===0){setScene('music');musicIdle.due=tick+m.musicIdleDue-m.tick;}gameplayRandom.reset(m.seed);treehouseDemo.setPointer(...m.pointer);if(scene==='maze')mazePanel();render();
          window.observeNavigation=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};
        }''',m)
        if observe_room:
            page.evaluate('''origin=>{
              const start=tick,originalAdvance=advance;let previous='';window.roomSchedule=[];
              advance=function(count=1){for(let i=0;i<count;i++){originalAdvance();
                const state={scene,rect:[balloon.y,balloon.x,balloon.y+38,balloon.x+29],due:balloon.due-start+origin,pointer:pointer.map(Math.floor),travel:roomTravel?.effect?.phase||roomTravel?.phase||null,character:resident.active?.action??null,environment:room.pendingEnvironment||(room.environment?.id??null)};
                const key=JSON.stringify(state);if(key!==previous){window.roomSchedule.push({tick:tick-start+origin,...state});previous=key;}
              }};
            }''',m['tick'])
        audio_observation.install(page);held=False
        try:
            for cp in native['checkpoints']:
                name=cp['name'];expected=cp['after'];audio_observation.checkpoint(page,name);frames=[]
                for action in cp['inputs']:
                    # Native intervals start at the snapshot before input is
                    # submitted. A one-callback action may still display that
                    # boundary image before the emulator consumes its input.
                    boundary=page.evaluate('observeNavigation(0)')
                    for frame in boundary:frame['before_input']=True
                    frames.extend(boundary)
                    x,y=action['point'];box=page.locator('#game').bounding_box();page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                    page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))');frames.extend(page.evaluate('observeNavigation',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeNavigation(0)')
                actual=page.evaluate('''()=>({scene:scene==='maze'?(maze.phase==='win'?17:8):scene==='theater'?(theater.options?13:2):scene==='boardgame'?(boardgame.options?10:null):{inside:5,music:0,nature:1,telescope:12}[scene],runtimeScene:scene,seed:gameplayRandom.seed,selected:resident.selected,sex:character==='girl'?1:0,pose:resident.pose,hunger:resident.hunger,fatigue:resident.fatigue,cloud:room.cloud,objects:resident.objects.map(o=>({type:o.type,state:o.state,inside:o.inside,rect:resident.bounds(o)})),songs:maze.songs,history:[...maze.history].sort((a,b)=>a-b),travel:roomTravel?{phase:roomTravel.phase,maze:!!roomTravel.maze}:null})''')
                keys=['scene','seed','selected','sex'];differences={k:dict(expected=expected[k],actual=actual[k]) for k in keys if actual[k]!=expected[k]}
                for k in ['songs','history']:
                    if expected['maze'][k]!=actual[k]:differences[k]=dict(expected=expected['maze'][k],actual=actual[k])
                if expected['scene'] in [8,17]:
                    fields=['hard','streak','excluded','supportedTypes','secret','node','type','correct','choices']
                    browser_maze=page.evaluate('fields=>Object.fromEntries(fields.map(k=>[k,maze[k]]))',fields)
                    original_maze={k:expected['maze'][k] for k in fields};actual['maze']=browser_maze
                    if original_maze!=browser_maze:differences['maze']=dict(expected=original_maze,actual=browser_maze)
                if expected['scene']==0:
                    original_music=music_model(reference/'state'/f'{name}.ram-0')
                    browser_music=page.evaluate('''()=>({advanced:longScore,composing:musicEditor.enabled,page:musicEditor.enabled?musicEditor.index[Number(longScore)]:songId,song:Array.from(currentMusicSong()),tempo,instrument})''')
                    browser_music['song'][2:4]=[browser_music.pop('tempo'),browser_music.pop('instrument')]
                    browser_music['song']=active_song(browser_music['song'],int(browser_music['advanced']))
                    actual['music']=browser_music
                    if original_music!=browser_music:differences['music']=dict(expected=original_music,actual=browser_music)
                if expected['scene'] in [3,10]:
                    original_board=board_model(reference/'state'/f'{name}.ram-0')
                    browser_board=page.evaluate('''()=>boardgame&&({mode:boardgame.mode,opponent:boardgame.opponent,levels:boardgame.levels,player:boardgame.player,nodes:boardgame.nodes,directions:boardgame.directions,balances:boardgame.balances,types:boardgame.types,remaining:boardgame.remaining,first:boardgame.first,seed:gameplayRandom.seed})''')
                    if original_board!=browser_board:differences['board']=dict(expected=original_board,actual=browser_board)
                if expected['scene']==5:
                    for k in ['pose','hunger','fatigue','cloud']:
                        if expected[k]!=actual[k]:differences[k]=dict(expected=expected[k],actual=actual[k])
                    objects=[{k:o[k] for k in ['type','state','inside','rect']} for o in expected['objects']]
                    if sorted(objects,key=lambda o:o['type'])!=sorted(actual['objects'],key=lambda o:o['type']):differences['objects']=dict(expected=objects,actual=actual['objects'])
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');chosen=None;matched=None;before_input=False
                for frame in frames:
                    image=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if image.tobytes()==original.tobytes():chosen=image;matched=frame['tick'];before_input=frame.get('before_input',False);break
                if chosen is None:chosen=image
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched,matched_before_input=before_input)
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual));report['checks'].append(dict(name=name+' scene, saved maze and active room state',passed=not differences))
                print(name,'PASS' if not differences and count==0 else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        if observe_room:report['room_schedule']=page.evaluate('window.roomSchedule')
        audio_observation.collect(page,report);browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(p['exact'] for p in report['pixels'].values())
    report['scope']='One original maze/room snapshot followed by actual recorded mouse inputs and game-tick waits. Full RGB checkpoint membership includes the left boundary before input submission, as the native interval does; such matches are identified and do not establish input latency. Destination, saved song history, random and active room state are compared after each interval. Exact presentation timing and complete audio waveforms remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--reference',type=Path,default=DATA/'maze-navigation-global-a')
    parser.add_argument('--observe-room',action='store_true',help='Read-only balloon and room-transition schedule diagnostics; acceptance is unchanged.')
    a=parser.parse_args();raise SystemExit(0 if verify(a.html,a.output,a.reference,a.observe_room) else 1)
