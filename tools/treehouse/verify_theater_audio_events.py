"""Check theater's original observed cues through the full playable journey."""
from pathlib import Path
import argparse,hashlib,json
from verify_theater_native_journey import verify,DATA
from compare_theater_audio_events import compare

def main(html,output):
    output.mkdir(parents=True,exist_ok=False)
    reference=DATA/'theater-native-journey-e'
    journey_pass=verify(html,output/'journey',reference,True,True)
    audio_pass=compare(html,DATA/'theater-audio-native-a',output/'journey',reference,output/'audio')
    journey=json.loads((output/'journey/report.json').read_text(encoding='utf-8'))
    displays=journey['presentation_observations']
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),passed=journey_pass and audio_pass,
        checks=[dict(name='all native checkpoint images and gameplay states, with safe room return',passed=journey_pass),
                dict(name='every observed original sound source dispatched in checkpoint order',passed=audio_pass)],
        journey_report=str(output/'journey/report.json'),audio_report=str(output/'audio/report.json'),
        scope='Complete ordinary-input theater journey from one initial snapshot, comparing image membership, gameplay state and the ordered observed original sound sources. Native observer control matches full recording and checkpoints. Repeated starts between native observations, exact event timing and rendered whole-journey waveform remain unproven.',
        presentation=dict(represented=sum(v['represented'] for v in displays),native_unique=sum(v['native_unique'] for v in displays),unrepresented=sum(v['unrepresented'] for v in displays),full_parity=False),
        full_audio_parity=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raise SystemExit(0 if main(a.html,a.output) else 1)
