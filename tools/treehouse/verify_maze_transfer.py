"""Verify the restored piano/maze transfer, retaining separate tutorial failures."""
from pathlib import Path
import argparse,hashlib,json
from verify_maze_entry import verify,DATA
from compare_maze_audio_events import compare


def main(html,output):
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],journeys={},errors=[],full_entry_parity=False)
    for variant in ['full','skip']:
        tag='' if variant=='full' else '-skip';ref=DATA/f'maze-entry{tag}-control-a';journey=output/variant
        verify(html,journey,ref)
        result=json.loads((journey/'report.json').read_text(encoding='utf-8'));report['errors']+=result['errors']
        sound=compare(html,DATA/f'maze-entry{tag}-audio-a',journey,ref,output/(variant+'-audio'))
        frames=result['transfer_frames'];last=-1;ordered=True
        for frame in frames:
            matches=[t for t in frame['native_ticks'] if t>=last]
            if not matches:ordered=False;break
            last=matches[0]
        stable=['initial','intro-39' if variant=='full' else 'tutorial-skipped','piano-return','reentered','second-settled','final-piano']
        states={c['name']:c for c in result['checkpoints']}
        checks=[dict(name=variant+': every generated transfer composition occurs in original order',passed=len(frames)>=56 and ordered and all(f['exact'] for f in frames)),
            dict(name=variant+': completed tutorial, return, interrupted reentry and final piano match RGB/state',passed=all(not states[n]['differences'] and result['pixels'][n]['exact'] for n in stable)),
            dict(name=variant+': observed original sound sources and rates between player inputs',passed=sound)]
        report['checks']+=checks;report['journeys'][variant]=dict(report=str(journey/'report.json'),strict_checkpoint_comparison_passed=result['passed'],transfer_frames=len(frames),matching_transfer_frames=sum(f['exact'] for f in frames),retained_visual_failures={k:v for k,v in result['pixels'].items() if not v['exact']},retained_state_failures={c['name']:c['differences'] for c in result['checkpoints'] if c['differences']})
    report['passed']=not report['errors'] and all(c['passed'] for c in report['checks'])
    report['scope']='Native piano smoke and child bucket animation frame order, audible source/rate coverage and stable entrance/return/skip state. Full first-entry reports retain every intermediate visual and RNG timing mismatch and are not marked passed by this bounded transfer check.'
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--html',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();raise SystemExit(0 if main(a.html,a.output) else 1)
