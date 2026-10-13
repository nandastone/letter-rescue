"""Ensure allocator observers preserve the original board redraw outputs."""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output, control=None, observers=None):
    legacy=control is None and observers is None
    control=control or DATA/'board-cursor-relocation-control-a'
    reference=json.loads((control/'run.json').read_text(encoding='utf-8'))
    assert reference['passed'] and reference['control']
    checks=[];inputs={}
    def check(name,passed):checks.append(dict(name=name,passed=bool(passed)))
    def inventory(path):
        return {str(p.relative_to(path)).replace('\\','/'):digest(p) for p in path.rglob('*')
                if p.is_file() and 'live' not in p.relative_to(path).parts
                and (p.suffix in ('.png','.wav') or '.ram-' in p.name)}
    expected=inventory(control)
    assert expected
    for folder in observers or [DATA/'board-cursor-allocation-a',DATA/'board-background-loading-a']:
        name=folder.name;path=folder/'run.json'
        run=json.loads(path.read_text(encoding='utf-8'));inputs[name]=digest(path)
        check(name+' completed',run['passed'])
        for key in ['actions','origin_sha256','content_sha256','capture_boundary_version','snapshot_boundary_version']:
            check(name+' '+key,run[key]==reference[key])
        actual=inventory(folder)
        check(name+' ordinary file inventory',set(actual)==set(expected))
        for path,sha in expected.items():check(name+' '+path,actual.get(path)==sha)
        check(name+' callback timeline',(folder/'frames.jsonl').read_bytes()==(control/'frames.jsonl').read_bytes())
        if legacy:check(name+' original step-21 image',digest(folder/'state/final.png')==digest(DATA/'board-native-loss-a/state/step-21.png'))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,inputs=inputs,control_sha256=digest(control/'run.json'),
                full_game_parity=False,scope='Compare completed allocation/shape observers against the plain control, including all ordinary PNG/WAV/RAM files, callback timeline, inputs and source snapshot. Diagnostic live images and heap snapshots are outside the ordinary output inventory.')
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--control',type=Path);p.add_argument('--observer',type=Path,action='append')
    a=p.parse_args();raise SystemExit(0 if verify(a.output,a.control,a.observer) else 1)
