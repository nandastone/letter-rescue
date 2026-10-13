"""Compare the independent composer with ordinary-input DOS editor states."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,zipfile
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960));page.add_init_script('requestAnimationFrame=()=>0;');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        def snapshot(name,folder,state,code):
            ref=DATA/folder;run=json.loads((ref/'run.json').read_text());ram=(ref/'state'/f'{state}.ram-0').read_bytes();y,x=struct.unpack_from('<hh',ram,run.get('main_image_base',544)+0x321d0+0x2064)
            page.evaluate(f'treehouseDemo.setPointer({x},{y});'+code+';musicIdle.frame=-1;render()')
            original=Image.open(ref/'state'/f'{state}.png').convert('RGB')
            def capture():return Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB')
            image=capture();count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()));phase=-1
            # Align the independently reconstructed idle-eye animation phase,
            # retaining complete frames and reporting which phase was selected.
            if count:
                for frame in range(17):
                    page.evaluate(f'musicIdle.frame={frame};render()');candidate=capture();n=sum(a!=b for a,b in zip(candidate.getdata(),original.getdata()))
                    if n<count:image,count,phase=candidate,n,frame
                    if n==0:break
            delta=ImageChops.difference(image,original)
            report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),idle_phase=phase);image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        def check(name,code):
            result=page.evaluate(code);report['checks'].append(dict(name=name,passed=bool(result)))
        page.evaluate("setScene('music');setMusicComposing(true)")
        snapshot('blank-short','research-music-followup/compose','click-0','')
        snapshot('short-c','research-music-followup/compose','click-1',"noteDown(0,'test');noteUp('test')")
        snapshot('short-c-dsharp','research-music-followup/compose','click-2',"noteDown(3,'test');noteUp('test')")
        snapshot('short-dotted-selection','research-music-followup/compose','click-3','musicEditor.click(178,124)')
        snapshot('short-c-dsharp-f','research-music-followup/compose','click-4',"noteDown(5,'test');noteUp('test')")
        snapshot('blank-long','research-music-followup/menus','click-2','setMusicScore(true)')
        edit='research-music-editor/edit-capture';actions='research-music-editor/actions-capture'
        snapshot('editor-short-blank',edit,'blank-short','setMusicScore(false);musicEditor.clear();musicEditor.duration[0]=4')
        snapshot('editor-short-c',edit,'short-c',"noteDown(0,'test');noteUp('test')")
        snapshot('editor-short-ce',edit,'short-ce',"noteDown(4,'test');noteUp('test')")
        snapshot('marker-to-first',actions,'marker-to-first','musicEditor.click(165,33);musicEditor.move(121,34);musicEditor.end()')
        snapshot('replace-first',actions,'replace-first-d',"noteDown(2,'test');noteUp('test')")
        check('replacement preserves second note and span','musicEditor.song[0]===2&&musicEditor.song[5]===2&&musicEditor.song[7]===4&&musicEditor.position===1')
        snapshot('flat-default',actions,'toggle-flat',"activate(111,124,'test')")
        snapshot('flat-note',actions,'new-flat-note',"noteDown(1,'test');noteUp('test')")
        snapshot('eraser-tool',actions,'eraser-tool','musicEditor.click(98,108)')
        snapshot('erase-hole',actions,'erase-first','musicEditor.click(125,75)')
        check('erase preserves hole and later note','musicEditor.song[0]===2&&musicEditor.song[5]===127&&musicEditor.song[7]===129')
        snapshot('eraser-leaves-score',actions,'eraser-left-score','musicEditor.move(150,126)')
        snapshot('erase-dialog',actions,'erase-dialog','eraseMusicSong();advance(12)')
        snapshot('erased',actions,'erased-song','answerMusic(true)')
        check('erase retains default notation','musicEditor.song[0]===0&&musicEditor.song[4]===1&&musicEditor.position===0')
        snapshot('random-dialog',actions,'random-dialog',"askMusic('Create new song?',()=>musicEditor.randomize(tick));advance(12)")
        page.evaluate('answerMusic(true);advance(200)')
        check('random short book obeys recovered pitch and duration sets','musicEditor.song[0]===8&&musicEditor.song[20]===0&&Array.from({length:8},(_,i)=>musicEditor.song[5+2*i]).every(p=>[128,130,133,135,137,140,142].includes(p))')
        page.evaluate('setMusicScore(true);musicEditor.clear();repeatSong=true')
        snapshot('long-c',edit,'long-c',"noteDown(0,'test');noteUp('test')")
        snapshot('long-rest',edit,'rest-entry','musicEditor.click(187,135);musicEditor.move(123,39);musicEditor.end()')
        check('palette rest stores pitch5 and duration12','musicEditor.song[1]===2&&musicEditor.song[7]===5&&musicEditor.song[8]===12&&musicEditor.position===2')
        snapshot('long-after-rest',edit,'after-rest-key',"noteDown(4,'test');noteUp('test')")
        check('rest duration selection keeps keyboard note duration','musicEditor.song[9]===4&&musicEditor.song[10]===4')
        page.evaluate('setMusicScore(false);musicEditor.clear();musicEditor.song[4]=0;musicEditor.write(0);musicEditor.write(4);musicEditor.duration[0]=3;musicEditor.write(2)')
        snapshot('pitch-drag',edit,'pitch-drag','musicEditor.click(153,80);musicEditor.move(153,66);musicEditor.end()')
        check('pitch drag keeps marker and slot','musicEditor.position===3&&musicEditor.song[7]===9&&musicEditor.song[8]===4')
        snapshot('page40','research-music-editor/last-page-capture','page40','repeatSong=false;musicEditor.duration[0]=4;selectMusicPage(39)')
        snapshot('page41','research-music-editor/last-page-capture','page41',"activate(300,14,'test')")
        snapshot('page42','research-music-editor/last-page-capture','page42',"activate(300,14,'test')")
        snapshot('the-end','research-music-editor/last-page-capture','last-page',"activate(300,14,'test');advance(5000)")
        check('terminal page is read only',"(()=>{const a=JSON.stringify(musicEditor.song);noteDown(0,'test');noteUp('test');musicEditor.clear();return JSON.stringify(musicEditor.song)===a&&!musicEditor.editable;})()")
        page.evaluate('selectMusicPage(0);musicEditor.clear();musicEditor.rename("A tune for tomorrow");musicEditor.write(7);musicEditor.song[2]=1;musicEditor.save()')
        check('named blank page is occupied','musicEditor.used(0,0)')
        check('new instance restores both books and title',"(()=>{const e=new MusicEditor(store);return e.books[0][0][5]===7&&e.books[0][0][2]===1&&e.titleAt(0,0)==='A tune for tomorrow'&&e.books[1][0][1]===3;})()")
        for archive in [DATA/'source/The_Treehouse_1991.zip',DATA/'research-music-editor/edit-capture/state/reference-v1.pure.zip']:
            with zipfile.ZipFile(archive) as z:raw=z.read(next(n for n in z.namelist()if n.lower().endswith('/songs.dat')))
            result=page.evaluate('(raw)=>{const e=new MusicEditor(store);e.importData(Uint8Array.from(raw));return [...e.exportData()];}',list(raw))
            report['checks'].append(dict(name=f'lossless native SONGS.DAT round trip: {archive.parent.name}',passed=bytes(result)==raw))
        check('invalid import is atomic',"(()=>{const before=JSON.stringify(musicEditor.books);let errors=0;try{musicEditor.importData(new Uint8Array(10))}catch(e){errors++}const data=musicEditor.exportData();data[3]=255;try{musicEditor.importData(data)}catch(e){errors++}return errors===2&&JSON.stringify(musicEditor.books)===before;})()")
        page.evaluate("musicEditor.books=Array.from({length:2},()=>Array.from({length:43},()=>musicEditor.blank()));musicEditor.titles=Array.from({length:2},(_,m)=>Array.from({length:43},(_,i)=>musicEditor.encodeTitle(musicEditor.defaultTitle(m,i))));setMusicComposing(false);songId=20;instrument=11;setScene('music');musicEditor.books[0][0][0]=1;copyMusicSong()")
        # These reference captures show Yes87/No89: the second native face phase.
        snapshot('copy-dialog','research-music-editor/copy-capture','copy-dialog','advance(12)')
        snapshot('copied-song','research-music-editor/copy-capture','copied-lion','answerMusic(true)')
        check('copy chooses first free page and names song','musicEditor.index[0]===1&&musicEditor.title==="My Lion Theme"&&musicEditor.song[3]===11')
        check('full book refuses copy',"(()=>{for(let i=0;i<42;i++)musicEditor.books[0][i][0]=1;return musicEditor.firstFree()===-1;})()")
        snapshot('robot-shelf','research-room-followup/telescope-a','view-0',"rewards.visited=7;setScene('telescope')")
        for mode,capacity in [(0,8),(1,30)]:
            check(f'all 42 editable {capacity}-note pages and last-slot replacement',f'''(()=>{{const e=new MusicEditor(store);e.enabled=true;e.advanced={str(bool(mode)).lower()};for(let p=0;p<42;p++){{e.select(p);e.clear();for(let i=0;i<{capacity};i++)e.write(i%17);e.write(16);if(e.song[{mode}]!=={capacity}||e.position!=={capacity-1}||(e.song[{5+2*(capacity-1)}]&127)!==16)return false;}}return true;}})()''')
        page.evaluate("musicEditor.enabled=true;musicEditor.advanced=false;longScore=false;musicEditor.select(0);musicEditor.clear();musicEditor.song[4]=0;setScene('music')")
        page.locator('#song-title').fill('My keyboard song');page.locator('#song-title').press('Tab')
        page.locator('#game').focus();page.keyboard.press('z')
        check('real keyboard enters composer note','musicEditor.song[0]===1&&musicEditor.song[5]===0')
        page.get_by_role('button',name='Add a rest',exact=True).click()
        check('readable rest control enters rest','musicEditor.song[0]===2&&musicEditor.song[7]===5&&musicEditor.song[8]>=8')
        with page.expect_download()as pending:page.get_by_role('button',name='Download songbooks',exact=True).click()
        download=pending.value;download.save_as(output/'SONGS.DAT')
        report['checks'].append(dict(name='browser download writes original-size SONGS.DAT',passed=download.suggested_filename=='SONGS.DAT'and(output/'SONGS.DAT').stat().st_size==8688))
        page.reload();page.evaluate("setScene('music');setMusicComposing(true)")
        check('page reload retains title and entered notes','musicEditor.title==="My keyboard song"&&musicEditor.song[0]===2&&musicEditor.song[5]===0&&musicEditor.song[7]===5')
        page.get_by_role('button',name='Erase this song',exact=True).click();page.get_by_role('button',name='No',exact=True).click()
        check('readable No preserves the song','musicEditor.song[0]===2&&!musicDialog')
        page.locator('#songbook-file').set_input_files(output/'SONGS.DAT');page.wait_for_function("document.getElementById('status').textContent==='Both songbooks loaded.'")
        check('file picker imports both books','musicEditor.title==="My keyboard song"&&musicEditor.song[0]===2')
        page.get_by_role('button',name='Erase this song',exact=True).click();page.get_by_role('button',name='Yes',exact=True).click()
        check('readable Yes clears and resets title','musicEditor.song[0]===0&&musicEditor.title==="My Short Song #1"&&!musicDialog')
        report['all_reference_frames_exact']=all(v['exact']for v in report['pixels'].values());report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and report['all_reference_frames_exact'];browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
