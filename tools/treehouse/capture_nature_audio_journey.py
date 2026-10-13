"""Observe original nature sound sources through an unchanged input journey."""
from pathlib import Path
import argparse,importlib,json
from capture import digest
from capture_theater_audio_journey import AudioRecorder

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--journey',choices=['quiz','editing'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    journey=importlib.import_module('capture_nature_journey' if a.journey=='quiz' else 'capture_nature_editing')
    journey.Recorder=AudioRecorder;passed=journey.capture(a.output)
    path=a.output/'run.json';report=json.loads(path.read_text(encoding='utf-8'));report['audio_capture_tool_sha256']=digest(Path(__file__));path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if passed else 1)
