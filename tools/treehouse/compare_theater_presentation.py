"""Compare exact native frame membership across two builds; no timing claim."""
from pathlib import Path
import argparse,hashlib,json

def compare(baseline,candidate,output):
    a=json.loads(baseline.read_text(encoding='utf-8'));b=json.loads(candidate.read_text(encoding='utf-8'))
    assert a['reference_sha256']==b['reference_sha256']
    assert [c['name'] for c in a['presentation_observations']]==[c['name'] for c in b['presentation_observations']]
    changes=[];restored=[]
    for old,new in zip(a['presentation_observations'],b['presentation_observations']):
        assert old['native_unique']==new['native_unique']
        old_missing={f['sha256']:f for f in old['missing']};new_missing={f['sha256']:f for f in new['missing']}
        gained=old_missing.keys()-new_missing.keys();lost=new_missing.keys()-old_missing.keys()
        restored.extend(dict(checkpoint=new['name'],**old_missing[h]) for h in sorted(gained))
        changes.append(dict(checkpoint=new['name'],before=old['represented'],after=new['represented'],restored=len(gained),lost=sorted(lost)))
    report=dict(demo_sha256=b['demo_sha256'],baseline_sha256=a['demo_sha256'],
        baseline_report_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),candidate_report_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
        original_run_sha256=a['reference_sha256'],passed=b['passed'] and not b['errors'] and not any(c['lost'] for c in changes),
        before=sum(c['before'] for c in changes),after=sum(c['after'] for c in changes),native_total=sum(c['native_unique'] for c in b['presentation_observations']),
        changes=changes,restored=restored,full_parity=False,scope=__doc__)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ['changes','restored']},indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['baseline','candidate','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if compare(a.baseline,a.candidate,a.output) else 1)
