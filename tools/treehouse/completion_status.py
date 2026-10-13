"""Report remaining Treehouse issues; fail unless integrated fidelity is proven.

This is deliberately stricter than verify_all.py, which checks gameplay and
selected frames. Component fixtures and an unchecked top-level `passed` flag
cannot establish completion.
"""
from pathlib import Path
import argparse, hashlib, json, sys

ROOT=Path(__file__).resolve().parents[2]


def evaluate(ledger, verification, html):
    work=json.loads(ledger.read_text(encoding='utf-8'))
    evidence=json.loads(verification.read_text(encoding='utf-8'))
    digest=hashlib.sha256(html.read_bytes()).hexdigest()
    issues=work['issues'];ids=[i['id'] for i in issues]
    if not issues or len(ids)!=len(set(ids)):raise ValueError('Empty or duplicate issue list')
    checks=[]
    for issue in issues:
        if issue['status'] not in ['open','in_progress','closed']:raise ValueError('Unknown issue status')
        if any(d not in ids for d in issue.get('depends_on',[])):raise ValueError('Unknown dependency')
        accepted=issue['status']=='closed' and bool(issue.get('evidence'))
        for proof in issue.get('evidence',[]):
            path=(ROOT/proof['path']).resolve()
            valid=path.is_relative_to(ROOT) and path.is_file()
            valid=valid and hashlib.sha256(path.read_bytes()).hexdigest()==proof['sha256']
            if valid:
                result=json.loads(path.read_text(encoding='utf-8'))
                valid=result.get('passed') is True
                if proof.get('scope')=='playable':valid=valid and result.get('demo_sha256')==digest
            accepted=accepted and valid
        accepted=accepted and all(next(i for i in issues if i['id']==d)['status']=='closed' for d in issue.get('depends_on',[]))
        checks.append(dict(name=issue['id']+' '+issue['title'],passed=bool(accepted),status=issue['status']))
    suites=evidence.get('suites',{})
    checks.extend([
        dict(name='verification identifies current playable file',passed=evidence.get('demo_sha256')==digest and evidence.get('build_unchanged') is True),
        dict(name='every reported regression suite passes on this build',passed=bool(suites) and all(s.get('passed') is True and s.get('result',{}).get('demo_sha256')==digest for s in suites.values())),
        dict(name='complete native journey comparisons pass on this build',passed=bool(evidence.get('native_journeys')) and all(j.get('passed') is True and j.get('demo_sha256')==digest for j in evidence.get('native_journeys',{}).values())),
        dict(name='strict unshifted timing passes on this build',passed=evidence.get('strict_timing',{}).get('demo_sha256')==digest and evidence.get('strict_timing',{}).get('strict_timing_parity') is True and evidence.get('strict_timing',{}).get('unrepresented_native_displays')==0),
        dict(name='full parity evidence accepted',passed=evidence.get('full_clone_parity') is True),
        dict(name='delivery identifies verified build',passed=evidence.get('served_sha256')==digest)
    ])
    return dict(demo_sha256=digest,checks=checks,remaining=[i['id'] for i in issues if i['status']!='closed'],passed=all(c['passed'] for c in checks))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger',type=Path,default=ROOT/'testing/treehouse/remaining-work.json')
    p.add_argument('--verification',type=Path,default=ROOT/'testing/treehouse/completion_verification.json')
    p.add_argument('--html',type=Path,help='Explicit opt-in to the historical JavaScript gate with a legacy verification file')
    p.add_argument('--output',type=Path);a=p.parse_args()
    if a.html:
        report=evaluate(a.ledger,a.verification,a.html)
    else:
        from godot_completion import evaluate as evaluate_godot
        report=evaluate_godot(a.ledger,a.verification)
    if a.output:
        # Preserve every previous decision and the evidence it was based on.
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2));sys.exit(0 if report['passed'] else 1)
