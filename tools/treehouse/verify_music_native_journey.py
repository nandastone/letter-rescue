"""Replay a complete native two-book music journey from one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'


def active_song(raw,mode):
    return [raw[mode],*raw[2:5],*[v for i in range(raw[mode]) for v in ([127,0] if (raw[5+2*i]&127)==127 else raw[5+2*i:7+2*i])]]


def verify(html,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['complete'] and native['passed']
    checkpoints=native['checkpoints'];initial=dict(checkpoints[0]['after'])
    ram=(reference/'state/initial.ram-0').read_bytes()
    initial['idleCountdown']=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]-initial['tick']
    initial['listeningInstrument']=ram[544+0x2f180+0x791+initial['selection'][0]]
    initial['listeningPreferences']=[list(ram[544+0x2f180+offset:544+0x2f180+offset+50]) for offset in (0x75f,0x791,0x7c3)]
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
        reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),checks=[],pixels={},checkpoints=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        page.evaluate('''async m=>{
          await audio.unlock();songId=m.selection[Number(m.advanced)*2];if(typeof listeningBooks==='undefined')listeningInstrument=m.listeningInstrument;
          if(typeof listeningBooks!=='undefined')for(let mode=0;mode<2;mode++){
            for(let id=0;id<25;id++)for(let field=0;field<3;field++)listeningBooks.songs[mode][id][field+2]=m.listeningPreferences[field][mode*25+id];
          }
          musicEditor.enabled=m.composing;longScore=musicEditor.advanced=m.advanced;
          musicEditor.index=[m.selection[1],m.selection[3]];
          if(m.composing)musicEditor.books[Number(m.advanced)][m.selection[Number(m.advanced)*2+1]]=m.song;
          if(m.composing)musicEditor.titles[Number(m.advanced)][m.selection[Number(m.advanced)*2+1]]=musicEditor.encodeTitle(m.title);
          instrument=m.song[3];setScene('music');musicEditor.position=m.marker;
          musicIdle.frame=-1;musicIdle.due=tick+m.idleCountdown;repeatSong=false;
          gameplayRandom.reset(m.seed);treehouseDemo.setPointer(...m.pointer);render();
          window.observeMusic=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){
            render();const data=canvas.toDataURL().split(',')[1];if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};
        }''',initial)
        held=False;keys=set()
        try:
            for checkpoint in checkpoints:
                name=checkpoint['name'];expected=checkpoint['after'];frames=[]
                for action in checkpoint['inputs']:
                    x,y=action['point'];box=page.locator('#game').bounding_box()
                    page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                    new=set(action.get('keys',[]))
                    for key in keys-new:page.keyboard.up('Enter' if key=='enter' else key)
                    for key in new-keys:page.keyboard.down('Enter' if key=='enter' else key)
                    keys=new;page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    frames.extend(page.evaluate('n=>observeMusic(n)',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeMusic(0)')
                actual=page.evaluate('''()=>({scene,seed:gameplayRandom.seed,song:Array.from(currentMusicSong()),title:musicEditor.titleEntry?musicEditor.titleEntry.value:currentMusicTitle(),
                  composing:musicEditor.enabled,advanced:longScore,marker:musicEditor.position,selection:[songId,musicEditor.index[0],songId,musicEditor.index[1]],
                  instrument,tempo,playing:songPlaying,idle:{...musicIdle}})''')
                # DOS's personal-title buffer is stale while listening. Runtime
                # instrument/tempo override the stock SONG header in both games.
                fields=['seed','composing','advanced']+(['title'] if expected['composing'] else [])
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                if not actual['composing']:actual['song'][2:4]=[actual['tempo'],actual['instrument']]
                mode=int(expected['advanced']);es=active_song(expected['song'],mode);bs=active_song(actual['song'],mode)
                if es!=bs:differences['active_song']=dict(expected=es,actual=bs)
                if expected['composing'] and expected['marker']!=actual['marker']:differences['marker']=dict(expected=expected['marker'],actual=actual['marker'])
                index=mode*2+int(expected['composing'])
                if expected['selection'][index]!=actual['selection'][index]:differences['selection']=dict(expected=expected['selection'][index],actual=actual['selection'][index])
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');chosen=None;matched=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():chosen=generated;matched=frame['tick'];break
                if chosen is None:chosen=Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB')
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['checks'].append(dict(name=name+' active state/random sequence',passed=not differences));report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched)
                print(name,'PASS' if not differences and not count else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial music snapshot; ordinary canvas clicks, drags and typing thereafter. Complete image membership and active record/title/marker/RNG checks. Ignored other-mode lengths and unused note bytes are not active song semantics. Full presentation-time and audio waveform equality remain separate.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'music-native-journey-c');a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,a.reference) else 1)
