"""Require complete native shuffle frames, including the caption during token motion."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from verify_theater_native_journey import DATA, verify
from verify_theater_curtain_frames import check as curtain_frames


def check(html, output, journey_report=None):
    output.mkdir(parents=True, exist_ok=False)
    reference=DATA/'theater-native-journey-e'
    if journey_report is None:
        verify(html, output/'journey', reference, observe_presentation=True)
        journey_report=output/'journey/report.json'
    journey=json.loads(journey_report.read_text(encoding='utf-8'))
    fixture=json.loads((Path(__file__).parent/'fixtures/theater-shuffle-frames.json').read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert journey['demo_sha256']==digest(html)
    assert fixture['original_run_sha256']==digest(reference/'run.json')==journey['reference_sha256']
    observation=next(c for c in journey['presentation_observations'] if c['name']==fixture['checkpoint'])
    generated={f['sha256'] for f in observation['browser_frames']}
    checks=[]
    for frame in fixture['frames']:
        original=Image.open(reference/frame['image']).convert('RGB')
        assert hashlib.sha256(original.tobytes()).hexdigest()==frame['sha256']
        checks.append(dict(name='complete shuffle image at original tick '+str(frame['tick']),passed=frame['sha256'] in generated,sha256=frame['sha256']))
    restored=curtain_frames(journey)
    report=dict(demo_sha256=digest(html),passed=journey['passed'] and all(c['passed'] for c in checks+restored),checks=checks,curtain_preview_checks=restored,errors=journey['errors'],
        journey_report=str(journey_report),journey_report_sha256=digest(journey_report),required_frames=len(checks),
        shuffle_represented=observation['represented'],shuffle_native=observation['native_unique'],
        presentation_represented=sum(c['represented'] for c in journey['presentation_observations']),presentation_native=sum(c['native_unique'] for c in journey['presentation_observations']),
        full_presentation_parity=all(not c['unrepresented'] for c in journey['presentation_observations']),
        scope='One original snapshot followed by all recorded theater inputs. Require 35 restored complete shuffle images and 37 restored curtain/preview images over all RGB pixels, plus all 29 endpoint images and gameplay/random states. Remaining intermediate frames and exact timestamps are still separate failures.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['html','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--journey-report',type=Path)
    a=p.parse_args();raise SystemExit(0 if check(a.html,a.output,a.journey_report) else 1)
