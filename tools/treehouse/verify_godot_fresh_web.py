"""Check real first-profile initialization, reload and native-save import in Edge.

Browser random choices vary with the platform clock. Every other byte in the
2282-byte persistent region is compared to the native missing-STATUS capture;
the six random song choices and their history are checked separately. No game
state is installed by JavaScript. This does not prove title/audio/startup timing.
"""
import argparse,functools,hashlib,http.server,json,struct,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from build_demo import ROOT

def verify(web,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[];errors=[]
    def check(value,name):checks.append(dict(name=name,passed=bool(value)))
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1280,'height':800},accept_downloads=True)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            def download(name):
                with page.expect_download(timeout=10000) as pending:
                    page.get_by_role('button',name='Save game',exact=True).click()
                pending.value.save_as(output/name)
                return (output/name).read_bytes()
            page.keyboard.press('F9')
            raw=download('fresh.dat');native=(reference/'status-written.dat').read_bytes()
            check(len(raw)==2704,'fresh profile has canonical STATUS length')
            check(raw[:0x8aa]==native[:0x8aa] and raw[0x8e6:0x8ec]==native[0x8e6:0x8ec],'all deterministic saved fields equal native defaults')
            songs=struct.unpack_from('<6H',raw,0x8da);history=struct.unpack_from('<24H',raw,0x8aa)
            check(len(set(songs))==6 and all(0<=v<24 for v in songs),'fresh maze chooses six distinct valid songs')
            check(history==tuple(int(i in songs) for i in range(24)),'fresh maze history marks exactly those six songs')
            for i in range(3):
                at=0x8ec+20*i
                check(raw[at:at+14]==native[at:at+14],f'fresh room object {i} matches native type/state/placement')
            check(raw[:86]==bytes(86),'fresh personal-book usage flags are empty')
            page.keyboard.press('Escape');page.wait_for_timeout(2000)
            page.reload();page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            page.keyboard.press('F9')
            check(download('reloaded.dat')==raw,'actual reload preserves all fresh profile bytes and chooser')
            with page.expect_file_chooser(timeout=10000) as pending:
                page.get_by_role('button',name='Load game',exact=True).click()
            pending.value.set_files(reference/'status-written.dat');page.wait_for_timeout(350)
            check(download('native-import.dat')==native,'native fresh save round-trips byte exactly including original timers')
            page.keyboard.press('Escape');page.wait_for_timeout(150)
            page.keyboard.press('F2');page.wait_for_timeout(200)
            page.screenshot(path=str(output/'fresh-preferences.png'))
            page.keyboard.press('Escape');page.wait_for_timeout(400)
            page.keyboard.press('F9');page.wait_for_timeout(200)
            check(download('after-preferences.dat')==native,'opening and closing preferences preserves native fresh save')
            browser.close()
    except Exception as error:errors.append(str(error))
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/fresh-startup-native-c')
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output,a.reference.resolve()) else 1)
