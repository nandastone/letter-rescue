"""Compare all eight original room/activity transition sequences in Godot.

Supplies an initial native room fixture per sequence. Every generated changed
full RGB frame must occur in original order. This checks rendered stages, not
strict presentation timestamps or an uninterrupted activity journey.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from verify_room_transitions import model,NATIVE,ROOT


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    driver=json.loads((NATIVE/'driver.json').read_text(encoding='utf-8'))
    timeline={r['run']:r for r in map(json.loads,(NATIVE/'frames.jsonl').read_text(encoding='utf-8').splitlines())}
    fixtures=[]
    for event in driver['events']:
        branch=event['branch'];name=branch.split('-')[0];returning=branch.endswith('-return')
        fixture=model(NATIVE/'state'/f'{name}-before.ram-0')
        ram=(NATIVE/'state'/f"{name}-{'return-settled' if returning else 'inside'}.ram-0").read_bytes()
        py,px=struct.unpack_from('<hh',ram,0x34454)
        fixtures.append(dict(fixture,name=branch,returning=returning,variant=['music','nature','theater','board'].index(name),pointer=[px,py]))
    (output/'fixtures.json').write_text(json.dumps(fixtures),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_room_transitions.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=180)
    log=p.stdout+p.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:
        raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    checks=[]
    for name,sequence in actual.items():
        native=[timeline[r['run']] for r in driver['rows'] if r['branch']==name and r['run'] in timeline]
        last=-1
        for frame in sequence['frames']:
            matches=[row for row in native if row['run']>last and row['rgb_sha256']==frame['sha256']]
            frame['passed']=bool(matches)
            if matches:
                last=matches[0]['run'];frame['native_run']=last
        checks.append(dict(name=name,passed=sequence['finished'] and all(f['passed'] for f in sequence['frames']),matched=sum(f['passed'] for f in sequence['frames']),**sequence))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],sequences=[dict(name=c['name'],matched=c['matched'],total=len(c['frames'])) for c in checks]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
