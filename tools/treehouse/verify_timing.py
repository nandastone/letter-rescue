"""Compare actual native presentation times with an independently rendered replay.

Never shift individual frames to obtain a match. Native video callbacks sample
the integer game clock, including partially completed drawing operations.
The input callback fixes time zero; ordered matching is reported separately.
"""
from pathlib import Path
from bisect import bisect_right
import argparse, json, sys
from verify_nature_sequence import verify, NATIVE


def run(html, output, strict=False):
    output.mkdir(parents=True, exist_ok=False)
    verify(html, output/'sequence')
    sequence=json.loads((output/'sequence/report.json').read_text(encoding='utf-8'))
    states=sequence['sequences']['robot-turn']['states']
    native=[json.loads(line) for line in (NATIVE/'frames.jsonl').read_text().splitlines()]
    by_run={row['run']:row for row in native}
    anchor=by_run[1815]['original_tick']
    ticks=[s['tick'] for s in states]
    transitions=[]
    for index,state in enumerate(states):
        row=by_run.get(state.get('native_run'))
        transitions.append(dict(index=index,browser_tick=state['tick'],native_tick=row['original_tick']-anchor if row else None,
            native_run=row['run'] if row else None,delta_ticks=row['original_tick']-anchor-state['tick'] if row else None))
    # Fixed native endpoint: first fully restored die after the cleanup flash.
    # Never shorten the observation window to the last frame the clone matches.
    end=2798
    comparisons=[]
    native_displays=[]
    browser_hashes={s['hash'] for s in states}
    for row in native:
        if not 1815<=row['run']<=end:continue
        elapsed=row['original_tick']-anchor
        index=max(0,bisect_right(ticks,elapsed)-1)
        comparisons.append(dict(native_run=row['run'],elapsed_tick=elapsed,browser_state=index,exact=row['rgb_sha256']==states[index]['hash']))
        if not native_displays or native_displays[-1]['hash']!=row['rgb_sha256']:
            native_displays.append(dict(start_run=row['run'],end_run=row['run'],start_tick=elapsed,end_tick=elapsed,
                hash=row['rgb_sha256'],image=str(NATIVE/row['image']),represented_in_browser=row['rgb_sha256'] in browser_hashes))
        else:
            native_displays[-1].update(end_run=row['run'],end_tick=elapsed)
    # Seven automatic eliminations run through the real question generator.
    eliminations=[i for i,s in enumerate(states) if i and s['player']==states[i-1]['player']==1 and s['remaining'][1]!=states[i-1]['remaining'][1]]
    browser_intervals=[states[b]['tick']-states[a]['tick'] for a,b in zip(eliminations,eliminations[1:])]
    native_intervals=[transitions[b]['native_tick']-transitions[a]['native_tick'] for a,b in zip(eliminations,eliminations[1:])]
    checks=[dict(name='seven actual help eliminations observed',passed=len(eliminations)==7),
            dict(name='successive elimination intervals match native game ticks',passed=browser_intervals==native_intervals,browser=browser_intervals,native=native_intervals)]
    cadence_passed=sequence['passed'] and all(c['passed'] for c in checks)
    strict_passed=cadence_passed and all(c['exact'] for c in comparisons)
    report=dict(demo_sha256=sequence['demo_sha256'],anchor=dict(native_run=1815,native_tick=anchor,browser_tick=0),
        checks=checks,transitions=transitions,callback_comparisons=comparisons,
        exact_callbacks=sum(c['exact'] for c in comparisons),total_callbacks=len(comparisons),
        native_displays=native_displays,unrepresented_native_displays=sum(not d['represented_in_browser'] for d in native_displays),
        strict_timing_parity=strict_passed,ordered_frame_parity=sequence['passed'],cadence_passed=cadence_passed,
        acceptance='strict' if strict else 'cadence',passed=strict_passed if strict else cadence_passed,
        scope='Cadence acceptance covers explicit checks only. Strict acceptance requires every unshifted callback, including partial redraws. Integer PIT samples do not establish sub-tick alignment; input delivered at callback N is consumed in the following emulation interval.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['transitions','callback_comparisons','native_displays']},indent=2))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--strict',action='store_true',help='Fail on any unshifted native callback mismatch, including partial redraws.')
    args=parser.parse_args();sys.exit(0 if run(args.html,args.output,args.strict) else 1)
