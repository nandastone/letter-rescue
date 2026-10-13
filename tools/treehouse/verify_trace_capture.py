"""Require exact pixels, PIT timestamps, audio and clocks in probe/control runs."""
from pathlib import Path
import argparse, hashlib, json, sys
from PIL import Image


def read(folder):
    trace=json.loads((folder/'trace.json').read_text())
    rows=[json.loads(line) for line in (folder/'frames.jsonl').read_text().splitlines()]
    if not rows or len(rows)!=1800+sum(a['frames'] for a in trace['actions']):raise ValueError('Incomplete capture')
    if not trace['no_probe'] and not trace['events']:raise ValueError('Probe did not observe any instructions')
    seen=set()
    for i,row in enumerate(rows):
        if row['callback']!=i or row['run']!=i:raise ValueError('Missing/reordered callback')
        path=(folder/row['image']).resolve()
        if not path.is_relative_to(folder.resolve()):raise ValueError('Frame outside capture')
        if path not in seen:
            image=Image.open(path).convert('RGB')
            if image.size!=(row['width'],row['height']) or hashlib.sha256(image.tobytes()).hexdigest()!=row['rgb_sha256']:raise ValueError('Corrupt frame')
            seen.add(path)
    return trace,rows


def verify(reference,candidate,output):
    if output.exists():raise ValueError('Evidence already exists')
    a,x=read(reference);b,y=read(candidate)
    fields=['callback','run','width','height','rgb_sha256','original_tick']
    mismatches=[dict(index=i,fields=[k for k in fields if u[k]!=v[k]]) for i,(u,v) in enumerate(zip(x,y)) if any(u[k]!=v[k] for k in fields)]
    provenance=[k for k in ['core_sha256','origin_sha256','actions','snapshot_boundary'] if a[k]!=b[k]]
    clocks=a['boundaries']==b['boundaries'];audio=(reference/'state/audio.wav').read_bytes()==(candidate/'state/audio.wav').read_bytes()
    same_mode=a['no_probe']==b['no_probe'];events=not same_mode or a['events']==b['events']
    report=dict(reference=str(reference),candidate=str(candidate),callback_count=[len(x),len(y)],mismatches=mismatches,provenance_differences=provenance,clocks_and_live_frames_equal=clocks,audio_identical=audio,event_trace_equal=events if same_mode else None,
        passed=not mismatches and not provenance and len(x)==len(y) and clocks and audio and events)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args();sys.exit(0 if verify(a.reference,a.candidate,a.output) else 1)
