"""Replay long-held white/black keys and input during the original idle animation."""
from pathlib import Path
import argparse,hashlib,json
from verify_maze_navigation import DATA,verify
from verify_piano_hold_controls import verify as controls

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    native=verify(a.html,a.output/'native',DATA/'piano-held-native-c')
    inputs=controls(a.html,a.output/'controls')
    report=dict(demo_sha256=hashlib.sha256(a.html.read_bytes()).hexdigest(),passed=native and inputs,errors=[],checks=[dict(name='all 17 native held/interruption images and states',passed=native),dict(name='all 18 fresh mouse/keyboard/touch checks',passed=inputs)],native_report=str(a.output/'native/report.json'),controls_report=str(a.output/'controls/report.json'),scope='Paired original mouse journey plus three fresh browser input sessions. Image membership includes identified before-input boundary frames; exact presentation/audio latency remains open.')
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
