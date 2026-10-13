"""Check original calendar panels and live date/clock room interactions."""
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
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=1000));page.add_init_script('requestAnimationFrame=()=>0;');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("room.now=()=>new Date(1992,0,1,12,39);room.date=room.now();setScene('inside')")
        page.evaluate('''window.settleCalendar=()=>{let n=0;while((room.calendarRead||room.height!==room.target)&&n++<5000)advance();if(room.calendarRead||room.height!==room.target)throw new Error('Calendar did not finish');render();};''')
        def check(name,code):report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
        def snapshot(name,native,code,region):
            page.evaluate(code+';pointerVisible=false;render()');image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB');original=Image.open(DATA/native).convert('RGB');actual=image.crop(region);expected=original.crop(region);delta=ImageChops.difference(actual,expected);n=sum(a!=b for a,b in zip(actual.getdata(),expected.getdata()));report['pixels'][name]=dict(exact=n==0,different_pixels=n,region=region,bounds=delta.getbbox());image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        snapshot('january-first','research-room-followup/room-clicks-a/state/hotspot-18.png','room.toggle();advance(14)',(162,28,283,110))
        check('calendar opens over seven native steps','room.open&&room.height===98&&room.story.heading==="DEAR DIARY"')
        snapshot('january-second','research-room-followup/room-clicks-a/state/hotspot-17.png','room.browse(1);settleCalendar()',(162,28,283,110))
        check('next day retains open calendar','room.date.getDate()===2&&room.height===98&&room.story.heading==="MISSED THE MOON"')
        check('cloud blocked behind open calendar','(()=>{const before=room.cloud;room.nextCloud();return room.cloud===before;})()')
        page.evaluate('room.toggle();advance(14)')
        check('closing restores roller position','!room.open&&room.height===28')
        # Read cloud X from the original room model. Account for the restored
        # core's segment displacement using the known music-geometry address.
        ref=DATA/'research-room-followup/room-clicks-a/state/hotspot-4';ram=ref.with_suffix('.ram-0').read_bytes();y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        adjustment=0x2f3a0-16*struct.unpack_from('<H',ram,0x323f0+0x4a54)[0];room_state=16*struct.unpack_from('<H',ram,0x323f0+0x49e0)[0]+adjustment;cloud_x=struct.unpack_from('<h',ram,room_state+0xa18)[0]
        page.evaluate(f'room.nextCloud();room.cloudX={cloud_x};treehouseDemo.setPointer({x},{y});render()')
        original=Image.open(ref.with_suffix('.png')).convert('RGB');region=(163,40,283,80);best=None
        image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('(c)=>c.toDataURL()').split(',')[1]))).convert('RGB');delta=ImageChops.difference(image.crop(region),original.crop(region));n=sum(a!=b for a,b in zip(image.crop(region).getdata(),original.crop(region).getdata()));report['pixels']['next-cloud']=dict(exact=n==0,different_pixels=n,region=region,native_model_x=cloud_x,bounds=delta.getbbox());image.save(output/'next-cloud.png');delta.save(output/'next-cloud-difference.png')
        check('all seven clouds cycle','(()=>{const a=room.cloud;for(let i=0;i<7;i++)room.nextCloud();return room.cloud===a;})()')
        check('all leap-year daily entries exist','(()=>{for(let m=0;m<12;m++){const days=new Date(1992,m+1,0).getDate();for(let d=1;d<=days;d++){room.date=new Date(1992,m,d);if(!room.story.heading||!room.story.body)return false;}}return true;})()')
        check('day navigation crosses month and leap day','(()=>{room.height=28;room.target=28;room.date=new Date(1992,1,28);room.browse(1);settleCalendar();const leap=room.date.getDate()===29;room.browse(1);settleCalendar();return leap&&room.date.getMonth()===2&&room.date.getDate()===1;})()')
        check('history lower limit is January 1980','(()=>{room.date=new Date(1980,0,1);room.browse(-1);return room.date.getFullYear()===1980&&room.date.getMonth()===0&&room.date.getDate()===1;})()')
        check('browsing does not change time provider','room.now().getFullYear()===1992&&room.now().getDate()===1&&room.now().getHours()===12')
        page.evaluate('room.height=28;room.target=28;room.now=()=>new Date(2026,8,27,0,5);room.date=room.now();render()')
        check('live clock minute invalidates renderer','room.update(tick)&&room.minute==="0:5"')
        check('current date uses original month text','room.dateLabel.includes("2026")&&room.dateLabel.includes("27")')
        page.get_by_role('button',name='Read the calendar',exact=True).click();page.evaluate('settleCalendar()')
        check('readable calendar shows original daily text','document.querySelector("#calendar-panel h3").textContent===room.story.heading&&document.querySelector("#calendar-panel .reading").textContent===room.story.body')
        page.get_by_role('button',name='Next day',exact=True).click();page.evaluate('settleCalendar()')
        check('readable day navigation works','room.date.getDate()===28')
        page.get_by_role('button',name='Today',exact=True).click();page.evaluate('settleCalendar()')
        check('Today restores host date','room.date.getDate()===27')
        page.get_by_role('button',name='What time is it?',exact=True).click()
        check('clock has readable time announcement','document.getElementById("status").textContent.startsWith("It is ")')
        page.set_viewport_size(dict(width=390,height=844));page.screenshot(path=str(output/'mobile-calendar.png'),full_page=True)
        check('calendar fits narrow screens','document.documentElement.scrollWidth<=window.innerWidth')
        page.get_by_role('button',name='Close the calendar',exact=True).click();page.evaluate('advance(14)')
        check('readable close removes the panel','!document.getElementById("calendar-panel")&&room.height===28')
        page.evaluate("activate(270,190,'test')");check('original ladder leaves the room','scene==="outside"')
        report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
