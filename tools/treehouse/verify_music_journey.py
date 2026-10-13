"""Author, edit, play, copy and interchange both songbooks through ordinary UI."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright


def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],playbacks=[],actions=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        def press(name):
            page.get_by_role('button',name=name,exact=True).click();page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            assert page.evaluate('''()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}''')
        def check(name,expression):
            ok=bool(page.evaluate(expression));report['checks'].append(dict(name=name,passed=ok));assert ok,name
        def select(id,value):
            # Python Playwright maps value= to valueOrLabel; numeric labels can
            # select the preceding one-based slot. Select its exact option node.
            option=page.locator(f'#{id} option[value="{value}"]').element_handle()
            result=page.locator('#'+id).select_option(element=option);page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            report['actions'].append(dict(action='select',id=id,value=value,result=result,state=page.evaluate('()=>({position:musicEditor.position,song:musicEditor.song.slice(0,13)})')))
        def note(key):
            page.locator('#game').focus();page.keyboard.down(key);page.wait_for_function('held.size===1');page.evaluate('advance(8)');page.keyboard.up(key)
            report['actions'].append(dict(action='note',key=key,state=page.evaluate('()=>({position:musicEditor.position,song:musicEditor.song.slice(0,13)})')))
        def data():return bytes(page.evaluate('Array.from(musicEditor.exportData())'))
        def download(name):
            with page.expect_download() as pending:press('Download songbooks')
            result=pending.value;assert result.suggested_filename=='SONGS.DAT';target=output/name;result.save_as(target);return target
        try:
            press('Choose the girl');press('Make some music');select('music-book',1)
            # Read event dispatch while retaining the actual playback implementation.
            page.evaluate('''()=>{window.musicJourneyNotes=[];const play=playPitch;playPitch=(pitch,instrument,finite)=>{musicJourneyNotes.push({pitch,instrument,tick});return play(pitch,instrument,finite);};}''')
            for mode in [0,1]:
                select('score-size',mode);select('song',0)
                title='Evening melody' if mode else 'Morning melody'
                page.locator('#song-title').fill(title);page.locator('#song-title').press('Tab')
                select('instrument',9 if mode==0 else 11);select('note-duration',4)
                for key in ['z','c','b']:note(key)
                press('Add a rest')
                select('note-position',1);note('n')
                select('note-position',0);press('Erase selected note');note('z')
                if mode:
                    select('note-position',15);note(',')
                check(f'book {mode}: edits preserve expected pitches and rest',f'musicEditor.song[{mode}]==={16 if mode else 4}&&[0,9,7,5].every((p,i)=>(musicEditor.song[5+2*i]&127)===p)&&musicEditor.song[12]===12')
                if mode:check('long book: second staff contains entered note','(musicEditor.song[35]&127)===12')
                for speed in range(5):
                    select('tempo',speed);page.evaluate('musicJourneyNotes=[]');press('Play song')
                    page.evaluate('advance(12000);render()')
                    played=page.evaluate('musicJourneyNotes');report['playbacks'].append(dict(mode=mode,speed=speed,notes=played))
                    expected=[0,9,7,12] if mode else [0,9,7]
                    ok=[n['pitch'] for n in played]==expected and page.evaluate('!songPlaying&&!held.size')
                    report['checks'].append(dict(name=f'book {mode}: complete playback at speed {speed}',passed=ok));assert ok
                select('repeat-song',1);press('Play song');page.evaluate('advance(12000);render()')
                check(f'book {mode}: repeat continues','songPlaying')
                press('Stop');check(f'book {mode}: stop ends playback','!songPlaying&&songVoice===null')
                select('repeat-song',0)
                press('Song contents');press(title)
                check(f'book {mode}: contents returns to named song',f'musicEditor.index[{mode}]===0&&!musicEditor.contents&&musicEditor.title==={json.dumps(title)}')
                press('Erase this song');press('No')
                check(f'book {mode}: declined erase preserves song',f'musicEditor.song[{mode}]==={16 if mode else 4}')
            # Copy an original song into the first free page of each authored book.
            for mode in [0,1]:
                select('score-size',mode);select('music-book',0);select('song',20)
                source=page.evaluate('Array.from(currentMusicSong())')
                press('Copy this song to my book');press('Yes')
                check(f'book {mode}: copy uses first free page',f'musicEditor.enabled&&musicEditor.index[{mode}]===1&&musicEditor.title==="My Lion Theme"')
                actual=page.evaluate('Array.from(musicEditor.song)')
                report['checks'].append(dict(name=f'book {mode}: copied notes retain original bytes',passed=actual[5:]==source[5:]));assert actual[5:]==source[5:]
            expected=data();saved=download('SONGS.DAT')
            report['checks'].append(dict(name='download contains both exact original-format books',passed=saved.read_bytes()==expected and len(expected)==8688));assert saved.read_bytes()==expected
            press('Back');page.reload();press('Choose the girl');press('Make some music')
            report['checks'].append(dict(name='both books survive complete browser reload',passed=data()==expected));assert data()==expected
            select('music-book',1);press('Erase this song');press('Yes');assert data()!=expected
            with page.expect_file_chooser() as chooser:press('Open songbooks')
            chooser.value.set_files(saved)
            page.wait_for_function("document.getElementById('status').textContent==='Both songbooks loaded.'")
            report['checks'].append(dict(name='file chooser restores both books without byte loss',passed=data()==expected));assert data()==expected
            # Invalid imports must leave the existing work available.
            invalid=output/'invalid.dat';invalid.write_bytes(b'invalid')
            with page.expect_file_chooser() as chooser:press('Open songbooks')
            chooser.value.set_files(invalid)
            page.wait_for_function("document.getElementById('status').textContent.includes('8,688')")
            report['checks'].append(dict(name='invalid file leaves both books unchanged',passed=data()==expected));assert data()==expected
            again=download('roundtrip-SONGS.DAT')
            report['checks'].append(dict(name='export after reload and import is byte-identical',passed=again.read_bytes()==expected));assert again.read_bytes()==expected
            page.screenshot(path=str(output/'completed.png'),full_page=True)
        except Exception as e:
            report['errors'].append(str(e));report['failure_state']=page.evaluate('()=>({song:Array.from(musicEditor.song),position:musicEditor.position,held:[...held],focus:document.activeElement?.id})');page.screenshot(path=str(output/'failure.png'),full_page=True)
        browser.close()
    report['passed']=not report['errors'] and len(report['playbacks'])==10 and all(c['passed'] for c in report['checks'])
    report['scope']='Fresh visible-control authoring/editing in both books, all five playback speeds, repeat/stop, contents, copy, erase decline/accept, full reload and actual download/file-chooser interchange. Reads observe state and pitch dispatch; no gameplay state installed. Native frame/timing and waveform equivalence are separate requirements.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),errors=report['errors']),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
