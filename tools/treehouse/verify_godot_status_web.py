"""Real browser file-picker/download and reload checks for the Godot export.

Game data is exchanged through F9 controls with ordinary keyboard/mouse input.
Downloaded STATUS.DAT and SONGS.DAT are compared as complete byte arrays.
"""
import argparse,functools,hashlib,http.server,io,json,threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from build_demo import ROOT

def verify(web,output,fixtures):
    output.mkdir(parents=True,exist_ok=False)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(web)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[];errors=[]
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text())
    songs=bytearray(8688)
    for m in range(2):
        for i in range(43):
            n=43*m+i
            raw=bytearray(65);raw[2]=3;raw[3]=9
            for j in range(30):raw[5+2*j]=127
            if i==42:raw=bytes(assets['music']['end_songs'][m])
            elif m==0 and i==0:raw[0]=1;raw[5]=7;raw[6]=4
            songs[65*n:65*(n+1)]=raw
            title=(f'My {"Long" if m else "Short"} Song #{i+1}').encode('cp437')
            if m==0 and i==0:title=b'Caf\x82 song'
            songs[0x15d6+36*n:0x15d6+36*n+len(title)]=title
    songs[0x21ee:]=b'\x24\x00'
    (output/'SONGS.DAT').write_bytes(songs)
    (output/'truncated.dat').write_bytes(b'bad')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1,accept_downloads=True)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            canvas=page.locator('#canvas')
            def ready():page.locator('#status').wait_for(state='hidden',timeout=60000);page.keyboard.press('Escape');page.wait_for_timeout(150) # Skip the logo through ordinary input.
            ready();bounds=canvas.bounding_box()
            def click(x,y):page.mouse.click(bounds['x']+x*bounds['width']/320,bounds['y']+y*bounds['height']/200)
            def shot(name):
                page.screenshot(path=str(output/(name+'.png')))
            def check(value,name):checks.append(dict(name=name,passed=bool(value)))
            def download(kind,name):
                with page.expect_download(timeout=10000) as pending:page.get_by_role('button',name='Save game' if kind=='status' else 'Save songbooks',exact=True).click()
                item=pending.value;item.save_as(output/name)
                check(item.suggested_filename==('STATUS.DAT' if kind=='status' else 'SONGS.DAT'),name+': original filename')
                page.wait_for_timeout(100)
                return (output/name).read_bytes()
            def upload(kind,path):
                try:
                    with page.expect_file_chooser(timeout=10000) as pending:page.get_by_role('button',name='Load game' if kind=='status' else 'Load songbooks',exact=True).click()
                except Exception:
                    shot('failed-file-picker')
                    raise
                pending.value.set_files(path)
                page.wait_for_timeout(350)
            page.keyboard.press('F9');page.wait_for_timeout(250);shot('file-controls')
            initial=download('status','initial-status.dat')
            check(len(initial)==2704,'new profile exports complete STATUS')
            original=(fixtures/'rich.dat').read_bytes()
            upload('status',fixtures/'rich.dat');shot('status-loaded')
            check(download('status','rich-downloaded.dat')==original,'import/export preserves all STATUS bytes and trailing data')
            upload('status',output/'truncated.dat');shot('invalid-rejected')
            check(download('status','after-rejected.dat')==original,'rejected import leaves existing saved game intact')
            with page.expect_file_chooser(timeout=10000) as pending:page.get_by_role('button',name='Load game',exact=True).click()
            pending.value.set_files([]);page.wait_for_timeout(200)
            check(page.locator('#treehouse-file-message').inner_text()=='No file selected.','cancelling a picker returns to file controls')
            for i in range(3):
                upload('status',fixtures/'rich.dat')
                check(download('status',f'repeated-{i}.dat')==original,f'repeated import/download {i+1} preserves saved bytes')
            upload('songs',output/'SONGS.DAT');shot('songs-loaded')
            check(download('songs','songs-downloaded.dat')==songs,'all 8688 SONGS bytes and CP437 title survive interchange')
            after_songs=download('status','after-songs.dat')
            page.keyboard.press('Escape');page.wait_for_timeout(1700)
            page.reload();ready();bounds=canvas.bounding_box();page.keyboard.press('F9');page.wait_for_timeout(250)
            check(download('status','reloaded-status.dat')==after_songs,'STATUS persists through actual browser reload')
            check(download('songs','reloaded-songs.dat')==songs,'SONGS persists through actual browser reload')
            page.keyboard.press('Escape');page.keyboard.press('F2');page.wait_for_timeout(250);shot('loaded-preferences')
            page.keyboard.press('Escape');page.keyboard.press('F9');page.wait_for_timeout(200)
            check(download('status','after-preferences.dat')==after_songs,'opening and closing original preferences preserves imported bytes')
            browser.close()
    except Exception as error:
        errors.append(str(error))
    finally:server.shutdown();server.server_close()
    report=dict(passed=not errors and all(c['passed'] for c in checks),checks=checks,errors=errors,scope=__doc__,web_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(web.iterdir()) if p.is_file()})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']],errors=errors),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--web',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.web.resolve(),a.output,a.fixtures.resolve()) else 1)
