"""Room object lifecycles and nested character/environment completion checks."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[])
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        page.evaluate('''()=>{resident.ambientEnabled=false;resident.hungerDue=resident.fatigueDue=Infinity;window.finishObject=()=>{for(let n=0;n<6000&&(resident.busy||room.busy);n++){advance();if(n%30===0)render();}return !resident.busy&&!room.busy;};setScene('inside');}''')
        def check(name,code):
            try:report['checks'].append(dict(name=name,passed=bool(page.evaluate(code))))
            except Exception as e:report['checks'].append(dict(name=name,passed=False,error=str(e)))
        for kind in [0,1,5]:
            check(f'prize {kind} leaves through both sides without stalled motion',f'''()=>{{for(const left of [50,220]){{const o=resident.create({kind});o.rect=[80,left,100,left+25];resident.clickObject(o);if(!finishObject()||resident.objects.includes(o))return false;}}return true;}}''')
        check('magnifier click completes four-frame cycle','()=>{const o=resident.create(2);resident.clickObject(o);return finishObject()&&o.state===1;}')
        check('flower cycles four stages and broken flower stays broken','()=>{const o=resident.create(7);for(let i=0;i<4;i++)resident.clickObject(o);if(o.state!==1)return false;o.state=5;resident.clickObject(o);return o.state===5;}')
        check('third balloon click removes balloon','()=>{const o=resident.create(6);for(let i=0;i<3;i++)resident.clickObject(o);return !resident.objects.includes(o)&&balloon.hidden;}')
        check('nut bag settles nut then flashes existing nut without duplicating','()=>{const b=resident.create(9);resident.clickObject(b);if(!finishObject())return false;const n=resident.objects.find(o=>o.type===11);if(!n||b.state!==1)return false;resident.clickObject(b);return finishObject()&&resident.objects.filter(o=>o.type===11).length===1&&!n.hidden;}')
        check('basket summons bird then makes a worm','()=>{const b=resident.create(10);resident.clickObject(b);if(!finishObject()||!resident.objects.some(o=>o.type===15))return false;resident.clickObject(b);return finishObject()&&resident.objects.some(o=>o.type===12)&&b.state===1;}')
        check('worm feeds bird and completes nest path','()=>{const o=resident.objects.find(o=>o.type===12);const saved=gameplayRandom.int;gameplayRandom.int=()=>0;resident.clickObject(o);const done=finishObject();gameplayRandom.int=saved;return done&&!resident.objects.includes(o)&&!resident.objects.some(o=>o.type===15);}')
        check('offered worm completes character and nested bird sequence','()=>{resident.create(15);resident.offer(resident.create(12));return finishObject()&&!resident.objects.some(o=>o.type===12||o.type===15);}')
        check('offered caterpillar finishes callback flight and character','()=>{resident.offer(resident.create(5));return finishObject()&&!resident.objects.some(o=>o.type===5);}')
        check('ordinary fall settles and high flower drop breaks','()=>{const o=resident.create(7),from=[30,100,55,120],to=[145,100,170,120];resident.runObject(resident.fall(o,from,to));return finishObject()&&o.state===5&&!o.hidden&&JSON.stringify(o.rect)===JSON.stringify(to);}')
        check('paper airplane zigzag settles at destination','()=>{const o=resident.create(1),from=[30,100,45,120],to=[160,100,175,120];resident.runObject(resident.fall(o,from,to));return finishObject()&&!o.hidden&&JSON.stringify(o.rect)===JSON.stringify(to);}')
        check('outdoor bird takes worm and leaves','()=>{setScene("outside");const o=resident.create(13,false);resident.clickObject(o);return finishObject()&&!resident.objects.includes(o)&&!resident.objects.some(o=>o.type===15);}')
        check('outdoor food animation consumes the correct object','()=>{const o=resident.create(16,false);resident.playAmbient(1300,1300,o);return finishObject()&&!resident.objects.includes(o);}')
        check('squirrel takes exactly one nut from pile','()=>{const o=resident.create(14,false);o.state=3;resident.playAmbient(1402,1400,o);return finishObject()&&o.state===2;}')
        check('indoor squirrel retrieves dropped nut','()=>{setScene("inside");const o=resident.create(11);resident.playAmbient(1403,1400,o);return finishObject()&&!resident.objects.includes(o);}')
        check('every ambient branch settles indoors and outdoors','()=>{const saved=gameplayRandom.int;for(const next of ["inside","outside"]){setScene(next);for(let choice=0;choice<8;choice++){gameplayRandom.int=n=>n===7?choice:0;resident.ambient();if(!finishObject()){gameplayRandom.int=saved;return false;}}}gameplayRandom.int=saved;return true;}')
        check('outdoor worm ignores an open indoor calendar','()=>{setScene("inside");room.height=room.target=98;setScene("outside");const o=resident.create(13,false);resident.clickObject(o);return finishObject()&&!resident.objects.includes(o);}')
        check('outdoor flyby preserves indoor perched bird','()=>{room.height=room.target=28;const bird=resident.create(15,true),saved=gameplayRandom.int;gameplayRandom.int=()=>0;resident.runObject(resident.flyby());const done=finishObject();gameplayRandom.int=saved;return done&&resident.objects.includes(bird);}')
        check('outside chute converts ground worm to indoor worm','()=>{const o=resident.create(13,false),r=resident.tables.surfaces[0][2];o.rect=[r[0],r[1],r[0]+1,r[1]+1];resident.place(o);return finishObject()&&!resident.objects.includes(o)&&resident.objects.some(o=>o.type===12&&o.inside);}')
        check('open basket hands its worm into the current held pointer gesture','()=>{setScene("inside");for(const o of [...resident.objects])if(o.type===12)resident.remove(o);const b=resident.create(10);b.state=3;const r=resident.bounds(b);resident.begin((r[1]+r[3])/2,(r[0]+r[2])/2);const pending=resident.drag?.object===b&&!resident.objects.some(o=>o.type===12);advance(15);const worm=resident.objects.find(o=>o.type===12),active=resident.drag?.object===worm;advance(16);resident.move(70,155);const moved=resident.drag?.moved;resident.end();return pending&&active&&moved&&finishObject()&&!resident.drag;}')
        check('room chute does not duplicate an outdoor worm','()=>{const outside=resident.create(13,false),inside=resident.create(12),r=resident.tables.surfaces[1][9];inside.rect=[180,300,192,317];resident.place(inside);return finishObject()&&!resident.objects.includes(inside)&&resident.objects.filter(o=>o.type===13).length===1&&resident.objects.includes(outside);}')
        check('outdoor discard region flies to native offscreen endpoint and removes object','()=>{setScene("outside");const o=resident.create(2,false);o.rect=[70,40,90,60];const flight=resident.flight,ends=[];resident.flight=function*(from,to,...rest){ends.push(to);yield* flight.call(this,from,to,...rest);};resident.place(o);const done=finishObject();resident.flight=flight;return done&&!resident.objects.includes(o)&&JSON.stringify(ends.at(-1))==="[50,170]";}')
        check('paper airplane falls straight through indoor chute','()=>{setScene("inside");const o=resident.create(1);o.rect=[150,300,165,320];const flight=resident.flight,ends=[];resident.flight=function*(from,to,...rest){ends.push(to);yield* flight.call(this,from,to,...rest);};resident.place(o);const done=finishObject();resident.flight=flight;return done&&ends.length===1&&!o.inside&&JSON.stringify(o.rect)===JSON.stringify(resident.tables.objects[1].outside);}')
        report['passed']=not report['errors']and all(c['passed']for c in report['checks']);browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
