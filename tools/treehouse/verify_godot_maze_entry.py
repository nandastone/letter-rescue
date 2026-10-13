"""Replay recorded piano/maze entry, tutorial, exit and reentry inputs in Godot.

One native initial piano fixture. Every subsequent pointer input and tick interval
comes from the recording. Full checkpoint images and selected maze/RNG state are
reported, including transient mismatches. Transfers are separately checked for
complete RGB frame membership and order; neither check proves exact timing.
"""
import argparse,base64,hashlib,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from build_demo import ROOT
from compare_nature_audio_events import rate


def verify(engine,output,reference):
    output.mkdir(parents=True,exist_ok=False)
    native=json.loads((reference/'run.json').read_text(encoding='utf-8'));assert native['passed']
    initial=dict(native['checkpoints'][0]['after']);ram=(reference/'state/initial.ram-0').read_bytes()
    initial['idleCountdown']=struct.unpack_from('<I',ram,0x323f0+0x56c4)[0]-initial['tick']
    fixture=dict(initial=initial,checkpoints=native['checkpoints'],reference=str(reference.resolve()))
    (output/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/replay_maze_entry.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=240)
    log=p.stdout+p.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'));checks=[]
    for a,e in zip(actual['checkpoints'],fixture['checkpoints']):
        keys=['seed','songs','history','hard']
        if e['after']['phase']==8 and not e['after']['first_intro']:keys+=['secret','node','type','correct','choices','typeHistory','patternHistory','familyHistory']
        diff={k:dict(actual=a['actual'].get(k),expected=e['after']['maze'][k]) for k in keys if a['actual'].get(k)!=e['after']['maze'][k]}
        image=Image.open(output/(a['name']+'.png')).convert('RGB');original=Image.open(reference/'state'/(a['name']+'.png')).convert('RGB')
        delta=ImageChops.difference(image,original);pixels=sum(x!=y for x,y in zip(image.getdata(),original.getdata()))
        if pixels:delta.save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,bounds=delta.getbbox(),differences=diff,matched_tick=a['matched_tick'],passed=not pixels and not diff))
    lookup={}
    for line in (reference/'frames.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('original_tick') is not None:lookup.setdefault(row.get('rgb_sha256'),[]).append(row['original_tick'])
    last=-1;ordered=True
    for frame in actual['frames']:
        frame['native_ticks']=lookup.get(frame['hash'],[])
        available=[t for t in frame['native_ticks'] if t>=last]
        frame['passed']=bool(available)
        if available:last=available[0]
        else:ordered=False
    stable=['initial','tutorial-skipped' if 'skip' in reference.name else 'intro-39','piano-return','reentered','second-settled','final-piano']
    stable_passed=all(c['passed'] for c in checks if c['name'] in stable) and all(any(c['name']==n for c in checks) for n in stable)
    # The older browser collector retained duplicates at checkpoint boundaries.
    # Compare changed compositions, rather than imposing its inflated count.
    previous=ROOT/'testing/output/treehouse/maze-transfer-frames-b/report.json'
    expected_frames=[]
    for frame in json.loads(previous.read_text(encoding='utf-8'))['transfer_frames']:
        if not expected_frames or frame['hash']!=expected_frames[-1]:expected_frames.append(frame['hash'])
    # Full and skipped tutorials leave different pointer positions at transfer
    # boundaries. Their expected changed-frame count is the same; pixel identity
    # and order must match this route's own native recording above.
    transfer_passed=ordered and len(actual['frames'])==len(expected_frames)
    audio_reference=reference.with_name(reference.name.replace('control','audio'))
    observations=json.loads((audio_reference/'sound-observations.json').read_text(encoding='utf-8'))['rows']
    pcm=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))['pcm']
    hashes={key:hashlib.sha256(base64.b64decode(value['pcm'])).hexdigest() for key,value in pcm.items()}
    groups=[];previous_tick=initial['tick']
    for a,e in zip(actual['checkpoints'],fixture['checkpoints']):
        if not groups or any(action['left'] for action in e['inputs']):groups.append(dict(checkpoints=[],native=[],godot=[]))
        group=groups[-1];group['checkpoints'].append(e['name'])
        group['godot'].extend(a['sounds'])
        group['native'].extend(dict(tick=r['tick'],pcm_sha256=r['pcm_sha256'],rate=rate(r['header'][1])) for r in observations if r['active'] and previous_tick<r['tick']<=e['after']['tick'])
        previous_tick=e['after']['tick']
    for group in groups:
        cursor=0;matches=[];used=set()
        for event in group['native']:
            match=next((i for i in range(cursor,len(group['godot'])) if hashes.get(group['godot'][i]['key'])==event['pcm_sha256'] and group['godot'][i]['rate']==event['rate']),None)
            matches.append(match)
            if match is not None:cursor=match+1;used.add(match)
        group['matches']=matches;group['passed']=all(i is not None for i in matches)
        group['unmatched_godot']=[event for i,event in enumerate(group['godot']) if i not in used]
    paired=all(hashlib.sha256((audio_reference/p).read_bytes()).digest()==hashlib.sha256((reference/p).read_bytes()).digest() for p in ['frames.jsonl','state/audio.wav'])
    audio_passed=paired and all(g['passed'] for g in groups)
    report=dict(passed=len(checks)==len(native['checkpoints']) and all(c['passed'] for c in checks) and transfer_passed and audio_passed,checks=checks,transfer_frames=actual['frames'],transfer_passed=transfer_passed,expected_changed_transfer_frames=len(expected_frames),stable_passed=stable_passed,audio_source_passed=audio_passed,audio_intervals=groups,audio_scope='Paired original observation/control timeline and WAV hashes match. Observed PCM sources/effective rates must occur in order between player inputs; unmatched Godot starts remain explicit. This does not prove exact sound timing or waveform/mixer parity.',scope=__doc__,reference_sha256=hashlib.sha256((reference/'run.json').read_bytes()).hexdigest(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),transfer_frames=len(actual['frames']),transfer_passed=report['transfer_passed'],stable_passed=stable_passed,audio_source_passed=audio_passed,failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=ROOT/'testing/output/treehouse/maze-entry-skip-control-a')
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output,a.reference) else 1)
