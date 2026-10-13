"""Compare Godot startup pixels to DOS and bounded SCR behavior to the JS reference.

The interpreter cross-check has no gameplay callbacks or palette loading; it is
port regression evidence, not proof of native scheduling or all activity states.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(engine: Path, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    project = ROOT/'treehouse-godot'

    def run(script, argument):
        process = subprocess.run([str(engine),'--headless','--path',str(project),'--script',script,'--',str(argument)],
                                 capture_output=True, text=True, encoding='utf-8', timeout=180)
        log = process.stdout+process.stderr
        (output/(Path(script).stem+'.log')).write_text(log, encoding='utf-8')
        if process.returncode or 'ERROR' in log or 'Unicode parsing error' in log:
            raise RuntimeError(log)

    run('testing/capture_startup.gd',output.resolve())
    run('testing/trace_scripts.gd',(output/'scripts-godot.json').resolve())
    report = dict(scope='Godot startup port; native pixels and separate bounded interpreter regression',
                  checks=json.loads((output/'godot.json').read_text())['checks'], native_pixels=[],
                  interpreter=[], source_sha256=digest(project/'data/original.json'))
    for scene, reference in [('outside','entry-verified-a/state/title.png'),('inside-boy','entry-verified-a/state/after-click.png')]:
        original = ROOT/'testing/output/treehouse'/reference
        expected = Image.open(original).convert('RGB')
        actual = Image.open(output/(scene+'.png')).convert('RGB')
        changed = sum(a!=b for a,b in zip(expected.getdata(),actual.getdata()))
        ImageChops.difference(expected,actual).save(output/(scene+'-diff.png'))
        report['native_pixels'].append(dict(scene=scene,reference=reference,reference_sha256=digest(original),
                                           pixels=64000,different_pixels=changed,passed=changed==0))
    assets = json.loads((project/'data/original.json').read_text(encoding='utf-8'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge',headless=True)
        page = browser.new_page()
        page.add_script_tag(content=(ROOT/'treehouse-demo/engine.js').read_text(encoding='utf-8'))
        reference = page.evaluate('''scripts=>{
            const store={data:{scripts},prepareAnimation:()=>[]},results={};
            for(const [key,script]of Object.entries(scripts)){
                const [archive,id]=key.split(':'),events=[];let tick=0;
                const a=new Animation(store,archive,Number(id),0,{
                    onSound:id=>events.push([tick,'sound',id]),
                    onCallback:(slot,arg)=>events.push([tick,'callback',slot,arg]),
                    onDisplay:a=>events.push([tick,'display',...a.display.flatMap(s=>['shape','first','end','flags','x','y','vx','vy','ax','ay','sc','mc'].map(k=>s[k]))])
                });
                for(tick=0;tick<=10000;tick++){a.update(tick);if(a.done)break;}
                results[key]={events,done:a.done,tick:Math.min(tick,10000),pc:a.pc};
            }return results;
        }''', assets['scripts'])
        browser.close()
    (output/'scripts-js.json').write_text(json.dumps(reference,separators=(',',':')),encoding='utf-8')
    actual = json.loads((output/'scripts-godot.json').read_text(encoding='utf-8'))
    for key, expected in reference.items():
        value = actual.get(key)
        report['interpreter'].append(dict(script=key,events=len(expected['events']),terminated=expected['done'],
                                          last_tick=expected['tick'],passed=value==expected))
    report['files'] = {str(p.relative_to(ROOT)):digest(p) for p in sorted(project.rglob('*.gd'))}
    report['files']['tools/treehouse/build_godot.py'] = digest(ROOT/'tools/treehouse/build_godot.py')
    report['limits'] = ['Initial room composition only: object interactions, ambient events and activities await porting.',
                        'Interpreter runs without activity callbacks; matching JS does not prove native timing.',
                        'Godot PCM output is preliminary: native mixer, rate and waveform comparisons remain open.',
                        'No claim of full-game completion or strict timing parity.']
    report['passed'] = all(c['passed'] for group in ['checks','native_pixels','interpreter'] for c in report[group])
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],native_pixels=report['native_pixels'],
                         scripts=len(report['interpreter']),failed_scripts=[s for s in report['interpreter'] if not s['passed']]),indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.godot,args.output) else 1)
