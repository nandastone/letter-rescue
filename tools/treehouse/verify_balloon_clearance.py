"""Character playback waits for original script-rectangle balloon clearance."""
from pathlib import Path
import argparse
import hashlib
import json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], errors=[])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        report['checks'] = page.evaluate('''()=>{
          const checks=[],check=(name,passed)=>checks.push({name,passed:!!passed});
          for(const who of ['boy','girl'])for(const pose of [0,1,2]){
            character=who;scene='inside';room.leave();room.speech=[];room.speechDue=0;
            const r=resident;
            Object.assign(r,{active:null,actionPreparation:null,after:null,queue:[],objectTask:null,
              objectMotion:null,ambientAnimation:null,drag:null,wakeTime:null,pose,tick:1000,
              ambientEnabled:false,hungerDue:Infinity,fatigueDue:Infinity});
            balloon.hidden=false;if(!r.objects.some(o=>o.type===6))r.create(6);
            const script=store.data.scripts[who+':20513'],b=script.bounds,
              dx=pose===1?59:pose===2?-132:0,dy=pose===1?-3:pose===2?4:0,
              top=b[0]+dy-31,left=b[1]+dx+5,label=who+' pose '+pose;
            balloon.x=left;balloon.y=top;
            let completed=0;r.action(13,()=>completed++);
            check(label+' clears before constructing animation',r.busy&&!r.active&&balloon.y===top-2);
            r.update(1001);check(label+' holds each step for two ticks',balloon.y===top-2&&!r.active);
            r.update(1002);check(label+' second upward step',balloon.y===top-4&&!r.active);
            for(let t=1003;t<=1009;t++)r.update(t);
            check(label+' relocated bounds plus two-pixel margin',balloon.x===left&&balloon.y===top-10&&!r.active&&r.pose===pose);
            r.update(1010);
            check(label+' starts script after final step',!!r.active&&r.active.startTick===1010&&!r.actionPreparation&&!r.clearingBalloon);
            r.action(31,()=>completed++);
            for(let n=0;n<6000&&r.busy;n++)r.update(r.tick+1);
            check(label+' queued actions and completion callbacks',!r.busy&&completed===2);
            for(const mode of ['horizontal-edge','vertical-edge','hidden','outside']){
              r.pose=pose;balloon.x=mode==='horizontal-edge'?b[3]+dx:left;
              balloon.y=mode==='vertical-edge'?b[0]+dy-40:top;
              balloon.hidden=mode==='hidden';scene=mode==='outside'?'outside':'inside';
              const oldY=balloon.y,start=r.tick;
              r.action(13);
              check(label+' '+mode+' starts immediately',!!r.active&&!r.actionPreparation&&balloon.y===oldY&&r.active.startTick===start);
              for(let n=0;n<6000&&r.busy;n++)r.update(r.tick+1);
              check(label+' '+mode+' completes',!r.busy);
            }
          }
          return checks;
        }''')
        browser.close()
    report['passed'] = not report['errors'] and len(report['checks']) == 84 and all(c['passed'] for c in report['checks'])
    report['scope'] = 'Controlled production character actions for both characters and all three standing poses. Checks relocated SCR bounds, two-pixel margin, movement cadence, delayed animation origin, queue callbacks and non-overlap/hidden/outside cases. Native image and uninterrupted journey comparisons are separate; this is not a presentation timestamp or waveform proof.'
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']), failed=[c['name'] for c in report['checks'] if not c['passed']], errors=report['errors']), indent=2))
    return report['passed']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
