"""Change listening settings through ordinary browser controls and revisit them."""
from pathlib import Path
import argparse, hashlib, json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport=dict(width=1360, height=960))
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())

        def press(name):
            page.get_by_role('button', name=name, exact=True).click()
            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            assert page.evaluate('()=>{let n=0;while((entering||roomTravel||resident.busy||room.busy)&&n++<30000)advance();render();return n<30000;}')

        def select(name, value):
            option = page.locator(f'#{name} option[value="{value}"]').element_handle()
            page.locator('#'+name).select_option(element=option)
            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')

        def check(name, expected):
            actual = page.evaluate('()=>({song:songId,mode:Number(longScore),tempo,instrument,notation:currentMusicSong()[4]})')
            ok = actual == expected
            report['checks'].append(dict(name=name, expected=expected, actual=actual, passed=ok))
            assert ok, name

        def state(song, mode, tempo, instrument, notation):
            return dict(song=song, mode=mode, tempo=tempo, instrument=instrument, notation=notation)

        try:
            press('Choose the girl'); press('Make some music')
            select('song', 21)
            check('next original song loads its settings', state(21, 0, 4, 24, 0))
            select('tempo', 0); select('instrument', 9)
            select('song', 20)
            check('previous original song retains its own defaults', state(20, 0, 3, 11, 1))
            select('song', 21)
            check('return restores edited settings', state(21, 0, 0, 9, 0))
            select('score-size', 1)
            check('long score starts with separate settings', state(21, 1, 4, 24, 0))
            select('tempo', 1); select('instrument', 7)
            box = page.locator('#game').bounding_box()
            page.mouse.click(box['x']+111.1*box['width']/320, box['y']+124.1*box['height']/200)
            page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
            check('long notation changes through canvas', state(21, 1, 1, 7, 1))
            select('score-size', 0)
            check('short settings remain independent', state(21, 0, 0, 9, 0))
            select('score-size', 1)
            check('long settings are restored', state(21, 1, 1, 7, 1))
            select('music-book', 1); select('instrument', 15); select('tempo', 2)
            select('music-book', 0)
            check('composition settings do not overwrite listening', state(21, 1, 1, 7, 1))
            press('Back'); press('Make some music')
            check('room visit retains session listening settings', state(21, 1, 1, 7, 1))
            page.reload(); press('Choose the girl'); press('Make some music')
            check('restart restores saved page with original session defaults', state(21, 1, 4, 24, 0))
            select('song', 20); select('score-size', 0)
            check('song selection is shared across score modes', state(20, 0, 3, 11, 1))
        except Exception as e:
            report['errors'].append(str(e))
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Fresh ordinary UI; no gameplay state installed. Separate listening settings persist within the session. Full playback audio and exact presentation timing are separate.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL', len(report['checks']), report['errors'])
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output) else 1)
