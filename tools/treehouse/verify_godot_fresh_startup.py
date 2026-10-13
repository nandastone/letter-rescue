"""Compare fresh-profile defaults with an ordinary cold boot of the original.

The component fixture pins the platform RNG seed before the empty resident
constructor. It compares the complete 2282-byte persistent region and every
active object field, plus the native preferences panel. Native object handles,
session deadlines, unused object records, title/audio timing and full cold-boot
RNG ordering are outside this evidence; byte-exact native-file import is tested
separately by verify_godot_status.py.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT

def verify(engine,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    capture=json.loads((reference/'run.json').read_text())
    assert capture['passed'] and capture['snapshot_boundary_version']==2
    result=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_fresh_startup.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=90)
    log=result.stdout+result.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if result.returncode or 'ERROR' in log:raise RuntimeError(log)
    checks=json.loads((output/'godot.json').read_text())['checks']
    native=(reference/'status-written.dat').read_bytes();actual=(output/'fresh.dat').read_bytes()
    assert hashlib.sha256(native).hexdigest()==capture['written_status_sha256']
    checks.append(dict(name='complete persistent region equals native missing-file initialization',passed=actual[:0x8ea]==native[:0x8ea],bytes=0x8ea))
    count=struct.unpack_from('<H',native,0x8ea)[0]
    checks.append(dict(name='original normalized object count',passed=actual[0x8ea:0x8ec]==native[0x8ea:0x8ec]))
    for i in range(count):
        at=0x8ec+20*i
        checks.append(dict(name=f'object {i}: type/state/room/full rectangle',passed=actual[at:at+14]==native[at:at+14]))
    region=(32,44,284,156)
    a=Image.open(output/'preferences.png').convert('RGB').crop(region)
    n=Image.open(reference/'state/preferences.png').convert('RGB').crop(region)
    delta=ImageChops.difference(a,n);pixels=sum(x!=y for x,y in zip(a.getdata(),n.getdata()))
    delta.save(output/'preferences-diff.png')
    checks.append(dict(name='complete native preferences panel including pointer',region=region,different_pixels=pixels,passed=pixels==0))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,scope=__doc__,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),source_files={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('treehouse-godot/scripts').glob('*.gd')})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/fresh-startup-native-c')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.reference) else 1)
