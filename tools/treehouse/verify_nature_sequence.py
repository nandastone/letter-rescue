"""Complete human-to-robot nature turn against ordered original native frames."""
from pathlib import Path
from collections import defaultdict
from io import BytesIO
import argparse, base64, hashlib, json, struct
from PIL import Image, ImageChops
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT/'testing/output/treehouse/research-nature-final-audit/robot-roll'


def verify(html, output, retain_frames=False):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), errors=[], sequences={}, checks=[])
    rows = [json.loads(line) for line in (NATIVE/'frames.jsonl').read_text().splitlines()]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(); page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        for label, start, end in [('robot-turn',1815,3116)]:
            ram = (NATIVE/'state/before.ram-0').read_bytes()
            u=lambda at:struct.unpack_from('<H',ram,at)[0]
            cards=struct.unpack_from('<16H',ram,0x318b6);py,px=struct.unpack_from('<hh',ram,0x34454)
            model=dict(cards=[cards[:8],cards[8:]],secret=list(struct.unpack_from('<2H',ram,0x32242)),player=u(0x37640),asked=list(struct.unpack_from('<2H',ram,0x376cc)),remaining=list(struct.unpack_from('<2H',ram,0x376de)),available=[i for i in range(8)if u(0x37692+2*i)],pointer=[px,py],seed=struct.unpack_from('<I',ram,0x37680)[0])
            page.evaluate('''m=>{resident.ambientEnabled=false;setScene('nature');nature.mode='quiz';nature.quiz=new NatureQuiz(nature,{character:()=>character,speak:theaterSpeech,stopSound:()=>audio.stopAll()});const q=nature.quiz;Object.assign(q,m,{tick,phase:'answered',options:false,visibleQuestions:[],selectedAttribute:1});q.answer=nature.strings(5201)[q.attributes(q.cards[q.player][q.secret[q.player]])[1]];gameplayRandom.reset(m.seed);treehouseDemo.setPointer(...m.pointer);q.roll();}''', model)
            generated = page.evaluate('''async()=>{const states=[];let previous='';for(let i=0;i<2500;i++){render();const rgb=new Uint8Array(192000);for(let p=0;p<64000;p++)rgb.set(screen.image.data.subarray(p*4,p*4+3),p*3);const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),x=>x.toString(16).padStart(2,'0')).join('');if(hash!==previous){states.push({tick,hash,phase:nature.quiz.phase,player:nature.quiz.player,hintControl:!!nature.quiz.hintControl,remaining:[...nature.quiz.remaining],actorFrame:nature.quiz.actorScript?.frameUpdates??null,png:canvas.toDataURL().split(',')[1]});previous=hash;}if(nature.quiz.player===1&&nature.quiz.phase==='answered'&&!nature.quiz.busy)break;advance();}return states;}''')
            native = [row for row in rows if start <= row['run'] <= end]
            lookup = defaultdict(list)
            for row in native:
                lookup[row['rgb_sha256']].append(row)
            last = -1
            for i, state in enumerate(generated):
                png = state.pop('png'); matches = [r for r in lookup[state['hash']] if r['run'] > last]
                if retain_frames:
                    state['image']=f'{label}-{i}.png'
                    (output/state['image']).write_bytes(base64.b64decode(png))
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
            after=(NATIVE/'state/after.ram-0').read_bytes()
            expected=dict(player=struct.unpack_from('<H',after,0x37640)[0],remaining=list(struct.unpack_from('<2H',after,0x376de)),asked=list(struct.unpack_from('<2H',after,0x376cc)),seed=struct.unpack_from('<I',after,0x37680)[0],phase='answered',busy=False)
            actual=page.evaluate('()=>({player:nature.quiz.player,remaining:nature.quiz.remaining,asked:nature.quiz.asked,seed:gameplayRandom.seed,phase:nature.quiz.phase,busy:nature.quiz.busy})')
            report['checks'].append(dict(name='complete turn reaches native final cards, answers and RNG',passed=actual==expected,expected=expected,actual=actual))
            lit=next(r for r in native if r['run']==2789)
            report['checks'].append(dict(name='native end-of-turn lit die is present before final restored die',passed=len(generated)>1 and generated[-2]['hash']==lit['rgb_sha256'] and generated[-1]['tick']-generated[-2]['tick']==8,native_run=lit['run']))
            report['sequences'][label] = dict(total=len(generated), exact=sum(s['exact'] for s in generated), states=generated)
        browser.close()
    report['passed'] = not report['errors'] and all(c['passed'] for c in report['checks']) and all(s['total'] > 1 and s['total'] == s['exact'] for s in report['sequences'].values())
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report, 'sequences': {k:{a:v[a] for a in ['total','exact']} for k,v in report['sequences'].items()}},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); verify(args.html,args.output)
