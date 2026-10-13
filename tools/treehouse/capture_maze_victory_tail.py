"""Continue the pinned ordinary maze win until its song finishes (no RAM writes)."""
from pathlib import Path
import argparse, json, struct
from capture import Recorder, digest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll'
    content=DATA/'source/reference-v1.zip'
    origin=DATA/'research-music-maze/playthrough/state/correct-7.state'
    actions=[dict(frames=200,capture=f'tail-{i}') for i in range(6)]
    report=dict(schema=1,complete=False,core_sha256=digest(core),content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),actions=actions,tool_sha256=digest(Path(__file__)),adapter_sha256=digest(Path(__file__).with_name('libretro.py')))
    native=None
    try:
        native=Recorder(core,content,output)
        native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        native.perform(actions)
        states={}
        for action in actions:
            name=action['capture'];ram=(output/'state'/f'{name}.ram-0').read_bytes()
            states[name]=dict(phase=struct.unpack_from('<H',ram,0x318b0+0xb34)[0],node=struct.unpack_from('<H',ram,0x318b0+0x9d4)[0],seed=struct.unpack_from('<I',ram,0x323f0+0x5290)[0])
        report.update(complete=True,states=states,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index,options={k.decode():v.decode() for k,v in native.values.items()})
    finally:
        if native:
            native.close()
        if (output/'frames.jsonl').exists():
            report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    capture(parser.parse_args().output)
