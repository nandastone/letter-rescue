"""Record visible room/object state transitions during an existing native input journey."""
from pathlib import Path
import argparse,json
from capture_prize_object_journey import DATA,state
from capture import Recorder,digest

def observe(reference,output):
    output.mkdir(parents=True,exist_ok=False)
    original=json.loads((reference/'run.json').read_text(encoding='utf-8'))
    assert original['passed']
    native=Recorder(DATA/'capture-core/dosbox_pure_libretro.dll',DATA/'source/reference-v1.zip',output)
    events=[];last=None
    def record():
        nonlocal last
        m=state(native)
        key=dict(seed=m['seed'],ambientDue=m['ambientDue'],cloudX=m['cloudX'],objects=[o for o in m['objects'] if o['type']in[0,6]])
        if key!=last:events.append(dict(tick=m['tick'],**key));last=key
    try:
        native.perform([dict(frames=1800)]);native.restore(reference/'state/initial.state');native.image_base=544
        record()
        for action in original['actions']:
            for i in range(action['frames']):
                mouse=dict(action['mouse'])
                if i:mouse.update(dx=0,dy=0)
                native.perform([dict(frames=1,mouse=mouse)]);record()
    finally:native.close()
    report=dict(reference=str(reference),reference_sha256=digest(reference/'run.json'),events=events)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(events,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();observe(a.reference,a.output)
