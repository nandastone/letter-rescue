"""Native family-menu and advanced-score comparisons, plus every instrument."""
from pathlib import Path
import argparse,base64,hashlib,json,struct
from io import BytesIO
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0;');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        def check(value,label):
            report['checks'].append(dict(name=label,passed=bool(value)))
            if not value:raise AssertionError(label)
        def snapshot(label,folder,state,code,region=None):
            ref=DATA/'research-music-followup'/folder;run=json.loads((ref/'run.json').read_text());ram=(ref/'state'/f'{state}.ram-0').read_bytes()
            y,x=struct.unpack_from('<hh',ram,run.get('main_image_base',544)+0x321d0+0x2064)
            page.evaluate(code+f';treehouseDemo.setPointer({x},{y});treehouseDemo.render()')
            image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB');native=Image.open(ref/'state'/f'{state}.png').convert('RGB')
            if label=='long-score-room':
                frames=page.evaluate('''()=>{const out=[];for(let i=0;i<17;i++){render();out.push(document.querySelector('#game').toDataURL().split(',')[1]);advance(4);}return out;}''')
                candidates=[Image.open(BytesIO(base64.b64decode(f))).convert('RGB')for f in frames]
                counts=[sum(a!=b for a,b in zip(im.getdata(),native.getdata()))for im in candidates];index=min(range(17),key=counts.__getitem__);image=candidates[index];report['idle_reference_step']=index
            image.save(output/f'{label}.png')
            if region:image=image.crop(region);native=native.crop(region)
            delta=ImageChops.difference(image,native);count=sum(a!=b for a,b in zip(image.getdata(),native.getdata()));delta.save(output/f'{label}-difference.png')
            report['pixels'][label]=dict(different_pixels=count,exact=count==0,bounds=delta.getbbox(),region=region)
        page.evaluate("setScene('music');instrument=11;songId=20;")
        snapshot('family-menu','ensemble','click-0','musicSelector.show()')
        snapshot('animals','ensemble','click-1','musicSelector.show(0)')
        snapshot('home-made','homemade','click-0','musicSelector.show(1)')
        snapshot('long-score','menus','click-1',"musicSelector.leave('music');longScore=true",[88,27,300,102])
        # Native capture lands during the original 17-step idle eye animation.
        # The matched animation state is independent of DOS wall-clock alignment.
        snapshot('long-score-room','menus','click-1','musicIdle.due=tick;advance(1)')
        for category in range(7):
            page.evaluate('c=>{musicSelector.show(c);musicSelector.select(c);advance(1000);render();}',category)
            check(page.evaluate('musicSelector.category===instrument'),'Combined family '+str(category))
            members=page.evaluate('musicSelector.tables.members[musicSelector.category]')
            for member in members:
                page.evaluate('id=>{musicSelector.select(id);advance(1000);render();musicSelector.nextFact();render();}',member)
                check(page.evaluate('!musicSelector.performance||musicSelector.performance.done'),'Individual instrument '+str(member))
        page.evaluate('musicSelector.show()');page.get_by_role('button',name='Animals',exact=True).click();page.get_by_role('button',name='Lamb',exact=True).click()
        check(page.evaluate('instrument===30'),'Readable family buttons select Lamb')
        page.get_by_role('button',name='Back to the piano',exact=True).click()
        check(page.evaluate("!musicSelector.open&&scene==='music'"),'Returns to piano with selected instrument')
        page.locator('#score-size').select_option('1');check(page.evaluate('longScore'),'Readable score control selects two staffs')
        page.set_viewport_size(dict(width=390,height=844));page.get_by_role('button',name='Explore instrument families',exact=True).click()
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Family controls fit mobile width')
        page.screenshot(path=str(output/'families-mobile.png'),full_page=True)
        check(not report['errors'],'No browser exceptions');browser.close()
    report['passed']=all(c['passed']for c in report['checks']);report['all_reference_frames_exact']=all(c['exact']for c in report['pixels'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items()if k!='checks'},indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--html',required=True,type=Path);a.add_argument('--output',required=True,type=Path);args=a.parse_args();verify(args.html,args.output)
