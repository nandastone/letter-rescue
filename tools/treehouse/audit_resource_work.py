"""Inventory resident work during resource cache calls; not timing parity."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
# Half-open original code ranges. Membership indicates where a component model
# exists, not proof that every caller's inputs or complete elapsed time match.
GROUPS=[
 ('near allocation wrapper',True,[(0x003d,0x0076)]),
 ('near allocation search',True,[(0x0590,0x060c)]),
 ('timer interrupt',True,[(0x6447,0x6488)]),
 ('handle lock wrapper',True,[(0x6510,0x652a)]),
 ('handle allocation wrapper',True,[(0x652a,0x6557),(0x6566,0x658a)]),
 ('discardable wrapper',True,[(0x659e,0x65b2)]),
 ('address without age refresh',True,[(0x6628,0x6652)]),
 ('first-fit allocation',True,[(0x6d47,0x6e8d)]),
 ('far allocation wrapper',True,[(0x6e8d,0x6ea3)]),
 ('block length and coalescing',True,[(0x6fa9,0x7011)]),
 ('address and age refresh',True,[(0x75c6,0x7668)]),
 ('resource file open',True,[(0x794c,0x79d0)]),
 ('resource cache entry',True,[(0x7a30,0x7ae8)]),
 ('resource read',True,[(0x7aef,0x7bc9)]),
 ('resource payload length',True,[(0xec14,0xec40)])]


def audit(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());work=trace['work']
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted probe control')
    if work['routine']!='resident:7A66+all' or len(work['calls'])!=2494:raise ValueError('Incomplete resource work inventory')
    base=trace['location']['main_base']+0xd510;counts=Counter()
    for c in work['counts']:counts[c['address']-base]+=c['entries']
    groups=[];unknown=[]
    for name,modeled,ranges in GROUPS:
        hits={a:n for a,n in counts.items() if any(lo<=a<hi for lo,hi in ranges)}
        groups.append(dict(name=name,has_component_model=modeled,instructions=sum(hits.values()),addresses=len(hits),ranges=[list(r) for r in ranges]))
    for a,n in sorted(counts.items()):
        matches=[g for g in groups if any(lo<=a<hi for lo,hi in g['ranges'])]
        if len(matches)>1:raise ValueError('Overlapping classification')
        if not matches:unknown.append(dict(address=a,entries=n))
    report=dict(passed=not unknown,full_resource_work_parity=False,calls=len(work['calls']),instruction_entries=sum(counts.values()),groups=groups,unknown=unknown,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Inventory of resident instructions observed during 2494 resource-cache calls. Classification marks routines with existing component models; it does not prove composition or per-call parity. Includes timer interrupts. DOS/BIOS work outside the resident address window and full scheduling are not counted here.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.trace,a.control,a.output)
