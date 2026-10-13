"""Compare source-derived DOS transfer debits with the pinned core observer."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,output):
    output.mkdir(parents=True,exist_ok=False)
    trace=json.loads(trace_path.read_text());rows=trace['dos'];work=trace['work']
    if not rows or not work or work['routine']!='resident:7AEF' or len(work['calls'])!=33:raise ValueError('Incomplete DOS/read observations')
    base=trace['location']['main_base']+0xd510;expected=[]
    for call in work['calls']:
        payload=sum(c['entries'] for c in work['counts'] if c['call']==call['ordinal'] and c['address']==base+0x7b80)
        if not payload or payload>0xfff0:raise ValueError('Route is not the researched single-chunk read sequence')
        expected.extend([1,payload])
    if [r['bytes'] for r in rows]!=expected:raise ValueError('Observed DOS transfers do not equal all 33 checksum/payload read pairs')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
        results=page.evaluate('rows=>rows.map(r=>{const m=OriginalResourceWork.dosTransfer(r.bytes,r.cycles_before,r.io_before);return {...r,model:m,passed:m.cycles===r.cycles_after&&m.io===r.io_after};})',rows)
        checks=page.evaluate('''()=>{
          const f=(bytes,cycles,io=0)=>OriginalResourceWork.dosTransfer(bytes,cycles,io);
          return [
            {name:'strict threshold retains five cycles and accounts for the full old budget',passed:f(3,17,20).cycles===5&&f(3,17,20).io===37},
            {name:'above threshold deducts four cycles per byte',passed:f(3,18,20).cycles===6&&f(3,18,20).io===32},
            {name:'exhausted budget can increase to five cycles',passed:f(100,2,20).cycles===5&&f(100,2,20).io===22},
            {name:'zero-byte reads retain the original branch boundary',passed:f(0,5).io===5&&f(0,6).io===0&&f(0,6).cycles===6},
            {name:'negative residual budget is preserved in I/O accounting',passed:f(1,-1,20).cycles===5&&f(1,-1,20).io===19},
            {name:'64-bit I/O accumulator does not truncate to 32 bits',passed:f(1,100,4294967296).io===4294967300}
          ];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),transfers=results,checks=checks,
        exact_transfers=sum(r['passed'] for r in results),total_transfers=len(results),
        saturated_transfers=sum(4*r['bytes']+5>=r['cycles_before'] for r in rows),
        model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-work.js').read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),core_sha256=trace['core_sha256'],
        scope='DOS transfer-cycle and I/O accounting only. All 33 checksum/payload read pairs are covered. Incoming CPU budgets and I/O counters are explicit offline component fixtures, not a generated elapsed-time scheduler.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'transfers':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.output) else 1)
