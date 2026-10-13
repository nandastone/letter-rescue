"""Compare Godot modal regions against original DOS captures and exercise input.

Native evidence covers 12 help panels, six preferences states and two status
messages. Other help contexts have source-derived context/control checks only.
These checks do not establish whole-game timing or STATUS.DAT compatibility.
"""
import argparse,json,struct,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT

def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    base=ROOT/'testing/output/treehouse'
    cases=[]
    for row in json.loads((base/'research-help/comparison.json').read_text()):
        if 'context' not in row or row.get('status'):continue
        label=row['label'];extra=label in ('board-active','theater-options')
        name='theater-both' if label=='theater-options' else label
        source=base/'research-help'/('extra' if extra else 'native')/'state'/(name+'-help')
        cases.append(dict(name='help-'+label,kind='help',context=row['context'],rectangle=row['rectangle'],source=str(source)))
    for name in ['preferences']+['row-'+str(i) for i in range(5)]:
        source=base/'research-settings/native/state'/name
        ram=source.with_suffix('.ram-0').read_bytes()
        word=lambda n:struct.unpack_from('<H',ram,0x318b0+n)[0]
        settings=dict(sound=bool(word(0xaa)),printing=bool(word(0xac)),printer=word(0xae),advanced=bool(word(0xa8)),speed=bool(word(0xb2)))
        cases.append(dict(name='settings-'+name,kind='settings',settings=settings,rectangle=[43,32,152,288],source=str(source)))
    for name,label in [('version','Version 1.1'),('sound-off','Sound is Off')]:
        cases.append(dict(name=name,kind='status',label=label,rectangle=[176,108,192,212],source=str(base/'research-help/native/state'/name)))
    for c in cases:
        ram=Path(c['source']+'.ram-0').read_bytes()
        y,x=struct.unpack_from('<hh',ram,0x34454);c['pointer']=[x,y]
        c['reference_sha256']=hashlib.sha256(Path(c['source']+'.png').read_bytes()).hexdigest()
    (output/'fixture.json').write_text(json.dumps(cases),encoding='utf-8')
    with (output/'godot.log').open('w') as log:
        p=subprocess.run([str(engine),'--headless','--verbose','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_preferences.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=90)
    log=(output/'godot.log').read_text()
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:12000])
    controls=json.loads((output/'controls.json').read_text())
    images=[]
    for c in cases:
        t,l,b,r=c['rectangle'];rect=(l,t,r,b)
        actual=Image.open(output/(c['name']+'.png')).convert('RGB').crop(rect)
        expected=Image.open(c['source']+'.png').convert('RGB').crop(rect)
        delta=ImageChops.difference(actual,expected)
        pixels=sum(a!=b for a,b in zip(actual.getdata(),expected.getdata()))
        if pixels:delta.save(output/(c['name']+'-diff.png'))
        images.append(dict(name=c['name'],different_pixels=pixels,bounds=delta.getbbox(),passed=pixels==0,reference_sha256=c['reference_sha256']))
    report=dict(passed=controls['passed'] and all(i['passed'] for i in images),controls=controls,images=images,scope=__doc__)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],controls=len(controls['checks']),images=len(images),failures=[i for i in images if not i['passed']]),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
