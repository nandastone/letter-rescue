"""Compare a whole native collage editing journey from one initial snapshot."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
import browser_audio_observation as audio_observation

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def verify(html,output,reference,observe_audio=False):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert native['complete'] and native['passed']
    checkpoints=native['checkpoints'];initial=checkpoints[0]['after']
    assert not any(initial['objects'])
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(reference),
        reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),checks=[],pixels={},checkpoints=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport=dict(width=1360,height=960))
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        if observe_audio:audio_observation.install(page)
        page.evaluate('''async m=>{
          await audio.unlock();setScene('nature');nature.mode='explore';
          for(const k of ['time','attribute','category','values'])nature[k]=m[k];
          nature.objects=[[],[]];nature.selected=-1;nature.factOpen=false;
          gameplayRandom.reset(m.seed);gameplayRandom.trace=[];
          naturePanel();treehouseDemo.setPointer(...m.pointer);render();
          window.observeEditing=n=>{const frames=[],seen=new Set();for(let i=0;i<=n;i++){
            render();const data=canvas.toDataURL().split(',')[1];
            if(!seen.has(data)){seen.add(data);frames.push({tick,data});}if(i<n)advance();}return frames;};
        }''',initial)
        held=False
        try:
            for checkpoint in checkpoints:
                name=checkpoint['name'];expected=checkpoint['after'];frames=[]
                if observe_audio:audio_observation.checkpoint(page,name)
                for action in checkpoint['inputs']:
                    x,y=action['point'];box=page.locator('#game').bounding_box()
                    page.mouse.move(box['x']+(x+.1)*box['width']/320,box['y']+(y+.1)*box['height']/200)
                    if action['left']!=held:
                        page.mouse.down() if action['left'] else page.mouse.up();held=action['left']
                        page.evaluate('()=>new Promise(resolve=>setTimeout(resolve,0))')
                    frames.extend(page.evaluate('n=>observeEditing(n)',action['to_tick']-action['from_tick']))
                if not frames:frames=page.evaluate('observeEditing(0)')
                actual=page.evaluate('''()=>({scene,seed:gameplayRandom.seed,time:nature.time,attribute:nature.attribute,
                  category:nature.category,values:nature.values,selected:nature.selected,factIndex:nature.factIndex,
                  factOpen:nature.factOpen,objects:nature.objects.map(list=>list.map(o=>{const s=store.shape('modules',nature.tables.animals[o.id].large);return {id:o.id,rect:[o.y,o.x,o.y+s.h,o.x+s.w]};})),
                  randomCalls:gameplayRandom.trace})''')
                fields=['seed','time','attribute','category','values','objects']
                differences={k:dict(expected=expected[k],actual=actual[k]) for k in fields if expected[k]!=actual[k]}
                if actual['scene']!='nature':differences['scene']=dict(expected='nature',actual=actual['scene'])
                original=Image.open(reference/'state'/f'{name}.png').convert('RGB');chosen=None;matched=None
                for frame in frames:
                    generated=Image.open(BytesIO(base64.b64decode(frame['data']))).convert('RGB')
                    if generated.tobytes()==original.tobytes():chosen=generated;matched=frame['tick'];break
                if chosen is None:chosen=Image.open(BytesIO(base64.b64decode(frames[-1]['data']))).convert('RGB')
                delta=ImageChops.difference(chosen,original);count=sum(a!=b for a,b in zip(chosen.getdata(),original.getdata()))
                chosen.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
                report['checks'].append(dict(name=name+' state/random sequence',passed=not differences))
                report['pixels'][name]=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox(),generated_tick=matched)
                report['checkpoints'].append(dict(name=name,differences=differences,actual=actual))
                print(name,'PASS' if not differences and not count else 'FAIL',list(differences),count,flush=True)
        except Exception as e:report['errors'].append(str(e))
        if observe_audio:audio_observation.collect(page,report)
        browser.close()
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']) and all(v['exact'] for v in report['pixels'].values())
    report['scope']='One initial empty nature snapshot, then native ordinary canvas inputs and held drags. Full RGB checkpoint membership and active filter/collage/RNG comparison. No subsequent gameplay resets. Exact presentation time, audio and reload are separate requirements.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=DATA/'nature-edit-native-a');p.add_argument('--observe-audio',action='store_true');a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,a.reference,a.observe_audio) else 1)
