"""Need counters/deadlines at actual warning-script start and completion."""
from pathlib import Path
import argparse
import hashlib
import json
from playwright.sync_api import sync_playwright


def verify(html, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=[], cases=[], errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri())
        report['cases']=page.evaluate('''async()=>{
          await audio.unlock();const out=[];
          for(const who of ['boy','girl'])for(const where of ['inside','outside'])
          for(const name of ['hunger','fatigue'])for(const value of [2,3,4,5])for(const otherValue of [2,3,5]){
            character=who;scene=where;room.leave();room.speech=[];room.speechDue=0;
            const r=resident,other=name==='hunger'?'fatigue':'hunger',start=1000;
            Object.assign(r,{active:null,after:null,queue:[],objectTask:null,objectMotion:null,ambientAnimation:null,
              windowAnimation:null,drag:null,wakeTime:null,pose:1,tick:start,ambientEnabled:false,selected:true,
              windowDue:Infinity,hungerDue:Infinity,fatigueDue:Infinity});
            r[name]=value;r[other]=otherValue;r[name+'Due']=start;
            r[other+'Due']=otherValue>=3?start+90:Infinity;
            const warn=value===3||value>=4&&otherValue!==5;
            r.update(start);
            const before={value:r[name],due:r[name+'Due'],otherDue:r[other+'Due'],busy:r.busy};
            let limit=0;while(r.busy&&limit++<6000)r.update(r.tick+1);
            const after={tick:r.tick,value:r[name],due:r[name+'Due'],otherDue:r[other+'Due'],busy:r.busy};
            const expectedValue=value>=4&&otherValue===5?value:Math.min(5,value+1);
            const long=name==='hunger'?7200:14400;
            out.push({who,where,name,value,otherValue,warn,before,after,
              checks:{warningOwnsOldValue:warn?before.busy&&before.value===value:!before.busy&&before.value===expectedValue,
                initialDeadline:before.due===start+(value>=4&&!warn?3600:long),
                completes:!after.busy&&after.value===expectedValue,
                deadlineAfterCompletion:after.due===(value>=4?after.tick+3600:start+long),
                postponeOtherAfterWarning:!warn||otherValue<3||after.otherDue>=after.tick+600,
                noEarlyOtherPostponement:!warn||before.otherDue===(otherValue>=3?start+90:Infinity)}});
            audio.stopAll();
          }return out;
        }''')
        browser.close()
    for case in report['cases']:
        label=f"{case['who']} {case['where']} {case['name']}={case['value']} other={case['otherValue']}"
        report['checks'].extend(dict(name=label+' '+name,passed=passed) for name,passed in case['checks'].items())
    report['passed']=not report['errors'] and len(report['cases'])==96 and all(c['passed'] for c in report['checks'])
    report['scope']='96 controlled initial-state branches use production RoomCharacter.update and original character/window animation scripts and sound durations. Checks operation order and relative deadlines for both characters, both locations and hunger/fatigue, including suppressed warnings. Not a fresh-input journey, native presentation-time or waveform comparison.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(report['checks']),failed=[c['name'] for c in report['checks'] if not c['passed']],errors=report['errors']),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
