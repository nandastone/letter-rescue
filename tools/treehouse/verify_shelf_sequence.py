"""Robot prize-shelf arrival and replay against ordered complete native frames."""
from pathlib import Path
from collections import defaultdict
from io import BytesIO
import argparse, base64, hashlib, json, struct
from PIL import Image, ImageChops
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT/'testing/output/treehouse/research-shelf-play'


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), errors=[], sequences={}, checks=[])
    rows = [json.loads(line) for line in (NATIVE/'frames.jsonl').read_text().splitlines()]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(); page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        for label, snapshot, start, end in [('arrival','arrived',3072,3310), ('replay','before-replay',3802,4040)]:
            ram = (NATIVE/'state'/f'{snapshot}.ram-0').read_bytes()
            py, px = struct.unpack_from('<hh', ram, 0x34454)
            page.evaluate('''m=>{setScene('telescope');resident.ambientEnabled=false;telescope=3;rewards.shelf=m.shelf;treehouseDemo.setPointer(...m.pointer);startTelescopeAnimation(m.replay);}''', dict(shelf=[bool(v) for v in ram[0x379e8:0x379ee]], pointer=[px,py], replay=label=='replay'))
            generated = page.evaluate('''async()=>{const states=[];let previous='';for(let i=0;i<2000&&telescopeBusy();i++){render();const rgb=new Uint8Array(192000);for(let p=0;p<64000;p++)rgb.set(screen.image.data.subarray(p*4,p*4+3),p*3);const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');if(hash!==previous){states.push({tick,hash,png:canvas.toDataURL().split(',')[1]});previous=hash;}advance();}return states;}''')
            native = [row for row in rows if start <= row['run'] <= end]
            lookup = defaultdict(list)
            for row in native:
                lookup[row['rgb_sha256']].append(row)
            last = -1
            for i, state in enumerate(generated):
                png = state.pop('png'); matches = [r for r in lookup[state['hash']] if r['run'] > last]
                state['exact'] = bool(matches)
                if matches:
                    last = matches[0]['run']; state['native_run'] = last
                else:
                    image = Image.open(BytesIO(base64.b64decode(png))).convert('RGB'); a = np.array(image)
                    best = None; seen = set()
                    for row in native:
                        if row['run'] <= last or row['image'] in seen:
                            continue
                        seen.add(row['image']); ref = Image.open(NATIVE/row['image']).convert('RGB')
                        count = int(np.any(a != np.array(ref), axis=2).sum())
                        if best is None or count < best[0]:
                            best = count, row['run'], ref
                    if best:
                        state.update(different_pixels=best[0], nearest_native=best[1])
                        image.save(output/f'{label}-{i}.png'); ImageChops.difference(image,best[2]).save(output/f'{label}-{i}-difference.png')
            report['checks'].append(dict(name=label+' completes all25 original displays',passed=page.evaluate('!telescopeBusy()&&animations[0].done&&animations[0].frameUpdates===25')))
            report['sequences'][label] = dict(total=len(generated), exact=sum(s['exact'] for s in generated), states=generated)
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks']) and all(s['total'] > 1 and s['total'] == s['exact'] for s in report['sequences'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report, 'sequences': {k:{a:v[a] for a in ['total','exact']} for k,v in report['sequences'].items()}},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); verify(args.html,args.output)
