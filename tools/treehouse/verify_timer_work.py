"""Check IRQ0 state and resident instructions without claiming delivery timing."""
from pathlib import Path
import argparse, hashlib, json, sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def verify(trace_path, control_path, output):
    output.mkdir(parents=True, exist_ok=False)
    trace = json.loads(trace_path.read_text())
    control = json.loads(control_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve() != trace_path.parent.resolve():
        raise ValueError('Missing accepted same-core control')
    work = trace['work']
    if work['routine'] != 'resident:6447' or not work['timer_states']:
        raise ValueError('Missing timer profile')
    states = work['timer_states']
    if [s['call'] for s in states] != [c['ordinal'] for c in work['calls']]:
        raise ValueError('Incomplete timer observations')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_script_tag(path=str(ROOT/'treehouse-demo/timer-work.js'))
        generated = page.evaluate('''states=>{
          const state=w=>({ticks:w[0]+65536*w[1],countdowns:w.slice(2,6),biosStep:w[6]+65536*w[7],biosPhase:w[8]});
          const words=s=>[s.ticks&65535,s.ticks>>>16,...s.countdowns,s.biosStep&65535,s.biosStep>>>16,s.biosPhase];
          const continuous=new OriginalTimerWork(state(states[0].before));
          const rows=[],writes=[];
          for(const row of states){
            const local=new OriginalTimerWork(state(row.before)),work=local.tick();
            for(let i=0;i<4;i++)if(continuous.countdowns[i]!==row.before[i+2]){
              writes.push({call:row.call,index:i,previous:continuous.countdowns[i],value:row.before[i+2]});
              continuous.setCountdown(i,row.before[i+2]);
            }
            const before=words(continuous.snapshot());continuous.tick();
            rows.push({call:row.call,work,after:words(local.snapshot()),continuousBefore:before,continuousAfter:words(continuous.snapshot())});
          }
          const make=(extra={})=>new OriginalTimerWork({ticks:0,countdowns:[0,1,2,65535],biosStep:19886,biosPhase:0,...extra});
          const a=make({ticks:65535});const aw=a.tick();
          const b=make({ticks:0xffffffff});b.tick();
          const c=make({biosPhase:65535});const cw=c.tick();
          const d=make({biosStep:65536});const dw=d.tick();
          const e=make({biosStep:0xffffffff,biosPhase:1});const ew=e.tick();
          let badState=false,badWrite=false;
          try{make({countdowns:[-1,0,0,0]});}catch(e){badState=true;}
          try{make().setCountdown(4,2);}catch(e){badWrite=true;}
          return {rows,writes,checks:[
            {name:'low-word carry increments high tick word',passed:a.ticks===65536&&aw.entries[0x6458]===1},
            {name:'32-bit tick wraps',passed:b.ticks===0},
            {name:'countdowns saturate at zero',passed:JSON.stringify(a.countdowns)==='[0,0,1,65534]'},
            {name:'phase carry chains BIOS',passed:cw.chainBios&&!cw.acknowledgePic&&c.biosPhase===19885},
            {name:'nonzero high step chains BIOS',passed:dw.chainBios&&d.biosPhase===0},
            {name:'ADC high word wraps before branch',passed:!ew.chainBios&&e.biosPhase===0},
            {name:'invalid timer state rejected',passed:badState},
            {name:'invalid countdown write rejected',passed:badWrite}
          ]};
        }''', states)
        browser.close()
    base = trace['location']['main_base']+0xd510
    counts = {c['ordinal']: {} for c in work['calls']}
    for c in work['counts']:
        counts[c['call']][str(c['address']-base)] = c['entries']
    results = []
    for observed, model in zip(states, generated['rows']):
        actual, expected = counts[observed['call']], model['work']['entries']
        differences = {a: dict(expected=expected.get(a, 0), actual=actual.get(a, 0)) for a in actual.keys()|expected.keys() if actual.get(a, 0) != expected.get(a, 0)}
        state_equal = model['after'] == observed['after']
        continuous_equal = model['continuousBefore'] == observed['before'] and model['continuousAfter'] == observed['after']
        results.append(dict(ordinal=observed['call'], instructions=model['work']['instructions'], chain_bios=model['work']['chainBios'], differences=differences, state_equal=state_equal, continuous_equal=continuous_equal, passed=state_equal and continuous_equal and not differences))
    report = dict(passed=all(r['passed'] for r in results+generated['checks']), matching_calls=sum(r['passed'] for r in results), calls=results, instructions=sum(r['instructions'] for r in results), bios_chains=sum(r['chain_bios'] for r in results), countdown_writes=generated['writes'], checks=generated['checks'], initial_state=states[0]['before'], final_state=generated['rows'][-1]['continuousAfter'], model_sha256=hashlib.sha256((ROOT/'treehouse-demo/timer-work.js').read_bytes()).hexdigest(), trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(), control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(), scope='Resident IRQ0 instructions and all nine timer state words. Tick and BIOS phase evolve continuously from one initial fixture. Countdown writes between IRQs are explicit observed game inputs. IRQ delivery times, chained BIOS code, PIC/OUT costs and live CPU scheduling remain unmodeled.')
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({**report, 'calls': [r for r in results if not r['passed']], 'countdown_writes': len(report['countdown_writes'])}, indent=2))
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trace', type=Path, required=True)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    sys.exit(0 if verify(a.trace, a.control, a.output) else 1)
