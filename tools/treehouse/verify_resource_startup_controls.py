"""Compare startup observers with the plain original run."""
from pathlib import Path
import argparse,hashlib,json

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output,reference_suffix='d',control_suffix='d',capture_names=None,control_name=None):
    control=DATA/(control_name or f'resource-startup-control-{control_suffix}');reference=json.loads((control/'run.json').read_text(encoding='utf-8'))
    assert reference['passed'];checks=[];inputs={}
    def check(name,passed):checks.append(dict(name=name,passed=bool(passed)))
    def ordinary(folder):
        return {p.relative_to(folder).as_posix():digest(p) for p in folder.rglob('*') if p.is_file()
                and 'live' not in p.relative_to(folder).parts and (p.suffix in ['.png','.wav'] or '.ram-' in p.name)}
    expected=ordinary(control);assert expected
    captures=[]
    names=capture_names or [f'resource-startup-{stage}-{reference_suffix}' for stage in ['near','heap']]
    for stage in names:
        folder=DATA/stage;path=folder/'run.json'
        run=json.loads(path.read_text(encoding='utf-8'));captures.append(run);inputs[stage]=digest(path)
        check(stage+' completed',run['passed'])
        for key in ['core_sha256','content_sha256','actions','main_base','capture_boundary_version','snapshot_boundary_version']:
            check(stage+' '+key,run[key]==reference[key])
        actual=ordinary(folder);check(stage+' ordinary inventory',set(actual)==set(expected))
        for name,sha in expected.items():check(stage+' '+name,actual.get(name)==sha)
        check(stage+' callback timeline',(folder/'frames.jsonl').read_bytes()==(control/'frames.jsonl').read_bytes())
    labels=set.intersection(*(set(e['label'] for e in run['events']) for run in captures))
    timelines=[[e for e in run['events'] if e['label'] in labels] for run in captures]
    check('independent startup event timelines for all common observers',len(timelines)>=2 and bool(labels) and all(t==timelines[0] for t in timelines[1:]))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,inputs=inputs,control_sha256=digest(control/'run.json'),reference_suffix=reference_suffix,control_suffix=control_suffix,
                compared_event_labels=sorted(labels),capture_names=names,
                scope='Independently booted startup observers match all ordinary image/audio/RAM outputs and callbacks of the plain original run. Operation event timelines agree for every observer label present in all captures; additional observer labels are reported by their individual captures. Heap snapshots are offline observer outputs.',full_game_parity=False)
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-suffix',default='d');p.add_argument('--control-suffix',default='d')
    p.add_argument('--capture',nargs='+');p.add_argument('--control')
    a=p.parse_args();raise SystemExit(0 if verify(a.output,a.reference_suffix,a.control_suffix,a.capture,a.control) else 1)
