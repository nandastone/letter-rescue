"""Require restored complete native curtain/preview images; full parity stays separate."""
from pathlib import Path
import hashlib,json
from PIL import Image

def check(journey):
    fixture=json.loads(Path(__file__).with_name('fixtures').joinpath('theater-curtain-frames.json').read_text(encoding='utf-8'))
    reference=Path(journey['reference'])
    assert fixture['original_run_sha256']==hashlib.sha256((reference/'run.json').read_bytes()).hexdigest()==journey['reference_sha256']
    intervals={c['name']:{f['sha256'] for f in c['browser_frames']} for c in journey['presentation_observations']}
    checks=[]
    for f in fixture['frames']:
        original=Image.open(reference/f['image']).convert('RGB')
        assert hashlib.sha256(original.tobytes()).hexdigest()==f['sha256']
        checks.append(dict(name=f"complete {f['checkpoint']} image at original tick {f['tick']}",passed=f['sha256'] in intervals[f['checkpoint']],sha256=f['sha256']))
    assert len(checks)==37
    return checks
