"""Exercise first-use drawer decoding and warm reuse through ordinary controls.

This checks only intrinsic decoder work, not full resource-load timing or cache
eviction. Expected work is calculated independently from the pinned DAT stream.
"""
from pathlib import Path
import argparse, hashlib, json, math, zipfile
from playwright.sync_api import sync_playwright
from build_demo import ROOT, SOURCE_SHA
from resources import parse_archive
from sound import decode_sound_with_info
import browser_audio_observation as audio_observation


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
    with zipfile.ZipFile(source) as z:
        data=z.read('TheTreeh/digisnd.dat');costs={}
        for r in parse_archive(data):
            if r['tag']=='SND' and r['id'] in [1003,1004]:
                info,_=decode_sound_with_info(data[r['payload_offset']:r['payload_offset']+r['size']])
                costs[r['id']]=math.ceil(info.decode_cycles*(1193181/19886)/10000000)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],errors=[],decoder_wait_ticks=costs)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for touch in [False,True]:
            label='touch' if touch else 'desktop'
            context=browser.new_context(viewport=dict(width=390 if touch else 1360,height=960),has_touch=touch,is_mobile=touch)
            page=context.new_page();page.set_default_timeout(5000)
            page.add_init_script("requestAnimationFrame=()=>0;{const D=Date,fixed=D.parse('2026-09-28T10:00:00+10:00');Date=class extends D{constructor(...a){super(...(a.length?a:[fixed]));}static now(){return fixed;}};}")
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.goto(html.resolve().as_uri())
            def press(name):
                b=page.get_by_role('button',name=name,exact=True)
                b.tap() if touch else b.click()
                page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            def settle():
                assert page.evaluate("()=>{let n=0;const busy=()=>entering||roomTravel||resident.busy||room.busy||scene==='maze'&&maze.busy;while(busy()&&n++<30000)advance();render();return !busy();}")
            def check(name, passed):report['checks'].append(dict(name=label+': '+name,passed=bool(passed)))
            try:
                press('Choose the girl' if touch else 'Choose the boy');settle()
                press('Make some music');settle();press('Play the musical maze');settle()
                direction=page.evaluate('maze.correct')
                name=page.get_by_role('button').all_text_contents()
                press(next(n for n in name if n.startswith(['Left:','Up:','Right:','Down:'][direction])))
                settle();check('ordinary correct answer earns one note',page.evaluate('maze.earned===1&&maze.canGuess'))
                audio_observation.install(page)
                for name,rid,open_ in [('Guess the song',1004,True),('Keep exploring',1003,False),('Guess the song',1004,True),('Keep exploring',1003,False)]:
                    warm=page.evaluate('id=>soundEvents.some(e=>e.type==="start"&&e.key===`digisnd:${id}`)',rid)
                    before=page.evaluate('tick');count=page.evaluate('soundEvents.length');press(name)
                    wait=0 if warm else costs[rid]
                    starts=lambda:page.evaluate('a=>soundEvents.slice(a.count).filter(e=>e.type==="start"&&e.key===`digisnd:${a.id}`)',dict(count=count,id=rid))
                    if not warm:
                        check(f'{rid}: first-use sound waits for decoder',not starts())
                        check(f'{rid}: previous drawer remains during decoding',page.evaluate('maze.chooser') != open_)
                        canvas=page.locator('#game');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
                        px=box['x']+210*box['width']/320;py=box['y']+180*box['height']/200
                        page.touchscreen.tap(px,py) if touch else page.mouse.click(px,py)
                        check(f'{rid}: canvas interruption preserves pending load',page.evaluate('maze.loadingSound&&maze.busy') and not starts())
                        page.evaluate('n=>advance(n)',wait-1)
                        check(f'{rid}: no early sound before work finishes',not starts())
                        page.evaluate('advance()')
                    events=starts()
                    check(f'{rid}: {"warm" if warm else "cold"} start follows decoder budget',len(events)==1 and events[0]['tick']==before+wait)
                    settle();check(f'{rid}: completed drawer state',page.evaluate('maze.chooser')==open_)
                check('opening and closing preserve earned notes',page.evaluate('maze.earned===1&&!maze.busy'))
            except Exception as error:report['errors'].append(label+': '+str(error))
            context.close()
        browser.close()
    report.update(passed=not report['errors'] and len(report['checks'])==36 and all(c['passed'] for c in report['checks']),scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c['name'] for c in report['checks'] if not c['passed']],errors=report['errors']),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
