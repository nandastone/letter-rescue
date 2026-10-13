"""Lossless DOS saves, browser restart persistence, and native preferences pixels."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct,zipfile
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
    with zipfile.ZipFile(DATA/'source/The_Treehouse_1991.zip') as z:original=z.read('TheTreeh/status.dat')
    native=(DATA/'research-settings/native/status-written.dat').read_bytes()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        def check(name,code,arg=None):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code,arg))))
        for name,data in [('packaged',original),('native-written',native),('opaque-and-trailing',original+b'preserve trailing data')]:
            check(name+' byte-exact import/export','raw=>{gameSave.importData(new Uint8Array(raw));const out=gameSave.exportData();return out.length===raw.length&&out.every((v,i)=>v===raw[i]);}',list(data))
        check('truncated input rejected without replacing game','()=>{const before=gameSave.file;try{gameSave.importData(new Uint8Array(2703));return false;}catch(e){return gameSave.file===before;}}')
        check('one preference changes only its original word','raw=>{gameSave.importData(new Uint8Array(raw));audio.enabled=!audio.enabled;const out=gameSave.exportData();return out.every((v,i)=>i===0x62?v!==raw[i]:v===raw[i]);}',list(original))
        check('untouched imported opaque values survive normalised runtime','raw=>{const d=new Uint8Array([...raw,71,82]);d[0x68]=187;d[0x69]=204;d[0x8e6]=201;d[0]=84;d[0x62]=99;gameSave.importData(d);return gameSave.exportData().every((v,i)=>v===d[i]);}',list(original))
        page.evaluate('raw=>{gameSave.importData(new Uint8Array(raw));resident.ambientEnabled=false;}',list(original))
        for label in ['preferences','row-0','row-1','row-2','row-3','row-4']:
            ram=(DATA/f'research-settings/native/state/{label}.ram-0').read_bytes();word=lambda at:struct.unpack_from('<H',ram,0x318b0+at)[0];py,px=struct.unpack_from('<hh',ram,0x34454)
            page.evaluate('v=>{if(!preferences)openPreferences();Object.assign(gameSave.preferences,v);audio.enabled=v.sound;treehouseDemo.setPointer(v.x,v.y);render();}',dict(sound=bool(word(0xaa)),printing=bool(word(0xac)),printer=word(0xae),advanced=bool(word(0xa8)),speed=bool(word(0xb2)),x=px,y=py))
            image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB').crop((32,43,288,152));ref=Image.open(DATA/f'research-settings/native/state/{label}.png').convert('RGB').crop((32,43,288,152));delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));report['pixels'][label]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox(),region=[32,43,288,152]);image.save(output/f'{label}.png');delta.save(output/f'{label}-difference.png')
        check('modal suspends activity and closes with Escape','()=>{const before=resident.tick;advance(20);return resident.tick===before&&!!preferences;}')
        page.keyboard.press('Escape');check('Escape restores controls without leaving scene','()=>!preferences&&scene==="outside"')
        check('collage and theater modifications serialize','()=>{setScene("nature");nature.time=0;nature.addAnimal(nature.tables.animals.find(a=>a.active_time===0).id,210,115);setScene("theater");theater.selection=[0,0,1,-1];theater.propsEnabled=true;theater.addProp(0,[180,90]);theater.actorDrag[1]=[-4,8];setScene("boardgame");boardgame.levels=[2,1];gameSave.save();return true;}')
        expected=page.evaluate('()=>({objects:nature.objects.map(a=>a.map(o=>[o.id,o.x,o.y])),selection:theater.selection,props:theater.props,actor:theater.actorDrag,levels:boardgame.levels})')
        page.reload();check('browser reload restores creations and preferences','expected=>{setScene("nature");setScene("theater");setScene("boardgame");return JSON.stringify({objects:nature.objects.map(a=>a.map(o=>[o.id,o.x,o.y])),selection:theater.selection,props:theater.props,actor:theater.actorDrag,levels:boardgame.levels})===JSON.stringify(expected);}',expected)
        check('STATUS export retains live balloon position after following pointer','()=>{const o=resident.create(6);balloon.x=181;balloon.y=-8;const data=gameSave.exportData(),v=new DataView(data.buffer);const i=resident.objects.indexOf(o);return v.getInt16(0x8ec+20*i+6,true)===-8&&v.getInt16(0x8ec+20*i+8,true)===181;}')
        check('loading a game cancels an in-progress animal erase','raw=>{setScene("nature");nature.objects=[[],[]];nature.time=0;nature.addAnimal(0,200,100);nature.requestClear();answerQuestion(true);const started=!!nature.eraseTask;gameSave.importData(new Uint8Array(raw));advance(20);return started&&!nature.eraseTask&&!nature.eraseEffect&&!nature.drag&&!nature.undo;}',list(original))
        check('unvisited imported activities export byte-exact','raw=>{gameSave.importData(new Uint8Array(raw));return gameSave.exportData().every((v,i)=>v===raw[i]);}',list(native))
        report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values());browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
