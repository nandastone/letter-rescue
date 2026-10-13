"""Cold-start the actual Web export with SONGS.DAT and no STATUS/legacy JSON.

One disposable browser profile is prepared through the ordinary songbook file
picker, then its persisted STATUS/JSON files are removed while Godot is unloaded.
This explicit storage fixture represents a missing STATUS, not an ordinary-input
native journey. All subsequent startup, downloads and reload use the real game.
"""
import argparse
import functools
import hashlib
import http.server
import json
import struct
import threading
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(web, output, reference):
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(reference/'reference-fresh.zip') as archive:
        songs = archive.read('TheTreeh/songs.dat')
    (output/'SONGS.DAT').write_bytes(songs)
    native = (reference/'status-written.dat').read_bytes()
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            if self.path=='/__storage_fixture':
                content=b'<!doctype html><title>Storage fixture</title><link rel="icon" href="data:,">'
                self.send_response(200)
                self.send_header('Content-Type','text/html')
                self.send_header('Content-Length',str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                super().do_GET()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(web)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks, errors, storage = [], [], []
    def check(value, name): checks.append(dict(name=name, passed=bool(value)))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width':1280,'height':800}, accept_downloads=True)
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type=='error' else None)
            url = f'http://127.0.0.1:{server.server_port}/'
            def boot():
                page.goto(url)
                page.locator('#status').wait_for(state='hidden', timeout=60000)
                page.keyboard.press('Escape')
                page.wait_for_timeout(150)
                page.keyboard.press('F9')
            def download(label, name):
                with page.expect_download(timeout=10000) as pending:
                    page.get_by_role('button', name=label, exact=True).click()
                pending.value.save_as(output/name)
                return (output/name).read_bytes()
            boot()
            with page.expect_file_chooser(timeout=10000) as pending:
                page.get_by_role('button',name='Load songbooks',exact=True).click()
            pending.value.set_files(output/'SONGS.DAT')
            page.wait_for_timeout(2000)
            check(download('Save songbooks','imported-songs.dat')==songs, 'native songbook imports without byte changes')
            # Navigate away before editing persisted storage: no live engine can
            # flush a stale STATUS back over the prepared startup fixture.
            page.goto(url+'__storage_fixture')
            storage = page.evaluate('''async () => {
                const result = [];
                for (const info of await indexedDB.databases()) {
                    const db = await new Promise((resolve,reject) => {
                        const request=indexedDB.open(info.name);
                        request.onsuccess=()=>resolve(request.result);
                        request.onerror=()=>reject(request.error);
                    });
                    for (const storeName of db.objectStoreNames) {
                        const tx=db.transaction(storeName,'readwrite'), store=tx.objectStore(storeName);
                        await new Promise((resolve,reject) => {
                            const request=store.openCursor();
                            request.onerror=()=>reject(request.error);
                            request.onsuccess=()=>{
                                const cursor=request.result;
                                if(!cursor) return;
                                const name=String(cursor.key), leaf=name.split('/').pop();
                                const removed=['STATUS.DAT','preferences.json','nature.json','theater.json','board.json'].includes(leaf);
                                result.push({database:info.name,store:storeName,key:name,removed,
                                    songs:leaf==='SONGS.DAT'?Array.from(cursor.value.contents):null});
                                if(removed) cursor.delete();
                                cursor.continue();
                            };
                            tx.oncomplete=resolve;
                            tx.onerror=()=>reject(tx.error);
                            tx.onabort=()=>reject(tx.error||new Error('storage transaction aborted'));
                        });
                    }
                    db.close();
                }
                return result;
            }''')
            retained = [bytes(row['songs']) for row in storage if row['songs'] is not None]
            check(retained==[songs], 'cold-start storage retains exactly the original SONGS bytes')
            check(any(row['removed'] and row['key'].endswith('/STATUS.DAT') for row in storage), 'cold-start fixture removes existing STATUS while engine is unloaded')
            boot()
            raw = download('Save game','songs-only-status.dat')
            check(len(raw)==2704, 'SONGS-only startup writes canonical STATUS length')
            check(raw[:0x8aa]==native[:0x8aa] and raw[0x8e6:0x8ec]==native[0x8e6:0x8ec], 'SONGS-only deterministic settings equal native missing-STATUS defaults')
            check(raw[:86]==bytes(86), 'SONGS-only original usage flags start empty')
            chosen = struct.unpack_from('<6H',raw,0x8da)
            history = struct.unpack_from('<24H',raw,0x8aa)
            check(len(set(chosen))==6 and all(0<=v<24 for v in chosen) and history==tuple(int(i in chosen) for i in range(24)), 'fresh chooser/history follow original distinct-song rules')
            for i in range(3):
                at=0x8ec+20*i
                check(raw[at:at+14]==native[at:at+14], f'fresh room object {i} matches original fields')
            check(download('Save songbooks','retained-songs.dat')==songs, 'fresh STATUS preserves all separate song bytes')
            page.wait_for_timeout(2000)
            boot()
            check(download('Save game','reload-status.dat')==raw, 'actual reload preserves new STATUS bytes')
            check(download('Save songbooks','reload-songs.dat')==songs, 'actual reload preserves original song bytes')
            page.screenshot(path=str(output/'reloaded-file-controls.png'))
            browser.close()
    except Exception as error:
        errors.append(str(error))
    finally:
        server.shutdown(); server.server_close()
    for row in storage:
        if row['songs'] is not None:
            row['songs_sha256']=hashlib.sha256(bytes(row.pop('songs'))).hexdigest()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,
                scope=__doc__,storage_fixture=storage,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),
                web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/fresh-startup-native-c')
    args=parser.parse_args()
    raise SystemExit(0 if verify(args.web.resolve(),args.output,args.reference.resolve()) else 1)
