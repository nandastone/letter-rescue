"""Verify reconstructed native print sheets and music completion controls."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'
def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        for folder,name in [('capture-a','long-print'),('capture-short','after-20'),('capture-compose','after-20')]:
            root=DATA/'research-print'/folder;meta=json.loads((root/'run.json').read_text())['states'][name];ram=(root/'state'/f'{name}.ram-0').read_bytes();y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
            meta.update(pointer=[x,y],busy=name=='after-20')
            raw=page.evaluate("""m=>{musicEditor.advanced=!!m.advanced;musicEditor.enabled=!!m.composing;const id=parseInt(m.selection.slice(0,2),16),raw=[...m.header,...m.notes.flat()];musicEditor.drawPrint(screen,raw,m.composing?m.title:ORIGINAL.strings['modules:101'][id],m.header[3],id);const data=m.busy?bytes(ORIGINAL.raw['th:CURS:1']):ORIGINAL.cursor,x=m.pointer[0]-s16(data,2),y=m.pointer[1]-s16(data,0);for(let row=0;row<16;row++)for(let col=0;col<16;col++)if(!(u16(data,4+row*2)&(0x8000>>>col)))screen.rect(x+col,y+row,1,1,(u16(data,36+row*2)&(0x8000>>>col))?0xff55ffff:0xff000000);ctx.putImageData(screen.image,0,0);return canvas.toDataURL().split(',')[1];}""",meta)
            image=Image.open(BytesIO(base64.b64decode(raw))).convert('RGB');ref=Image.open(root/'state'/f'{name}.png').convert('RGB');delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));label=folder+'-'+name;report['pixels'][label]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox());image.save(output/f'{label}.png');delta.save(output/f'{label}-difference.png')
        def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
        page.evaluate("setScene('music');musicEditor.enabled=false;setMusicComposing(true)")
        check('title editing starts blank',"(()=>{musicEditor.beginTitle(tick);return musicEditor.titleEntry.value==='';})()")
        check('title escape restores original without closing',"(()=>{const old=musicEditor.title;musicEditor.titleKey('x');musicEditor.titleKey('Escape');return musicEditor.titleEntry.value===old;})()")
        check('title accepts replacement',"(()=>{musicEditor.titleEntry.value='Luna song';musicEditor.titleKey('Enter');return musicEditor.title==='Luna song'&&!musicEditor.titleEntry;})()")
        check('contents blocks note writing',"(()=>{const before=JSON.stringify(musicEditor.song);showMusicContents(1);noteDown(4,'test');noteUp('test');return JSON.stringify(musicEditor.song)===before;})()")
        check('contents page selection returns to score',"(()=>{selectMusicPage(3);return musicEditor.index[0]===3&&musicEditor.contents===0;})()")
        check('held note advances on release',"(()=>{const n=musicEditor.position;noteDown(0,'test');const heldPosition=musicEditor.position;noteUp('test');return heldPosition===n&&musicEditor.position===n+1;})()")
        check('keyboard release force-stops the current original sample','(()=>{const stop=audio.stop,release=audio.release,calls=[];audio.stop=id=>calls.push(["stop",id]);audio.release=id=>calls.push(["release",id]);held.set("test-release",{pitch:0,voice:123});noteUp("test-release");audio.stop=stop;audio.release=release;return calls.length===1&&calls[0][0]==="stop"&&calls[0][1]===123&&!held.has("test-release");})()')
        check('editor preview release uses the same forced-stop driver path','(()=>{const stop=audio.stop,calls=[];audio.stop=id=>calls.push(id);musicEditor.release(456);audio.stop=stop;return JSON.stringify(calls)==="[456]";})()')
        check('print confirmation produces score surface',"(()=>{printMusic();if(musicDialog?.message!=='Print song?')return false;answerMusic(true);return musicPrint instanceof Surface;})()")
        check('clear all resets both books and preserves endings',"(()=>{setScene('music');musicEditor.clearAll();return musicEditor.books.every((b,m)=>b.slice(0,42).every(s=>s[m]===0)&&JSON.stringify(b[42])===JSON.stringify(music.end_songs[m]));})()")
        report['passed']=not report['errors'] and all(v['exact'] for v in report['pixels'].values()) and all(c['passed'] for c in report['checks']);browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
