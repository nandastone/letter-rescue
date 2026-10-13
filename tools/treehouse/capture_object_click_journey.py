"""Capture original click-only object gestures without modifying original memory."""
from pathlib import Path
import argparse,json
from capture import Recorder,digest
from capture_prize_object_journey import DATA,state
CASES={
 'nuts':(9,'entry-verified-a/state/after-click.state'),
 'basket':(10,'entry-verified-a/state/after-click.state'),
 'open-basket':(10,'research-object-completion/basket/state/basket-open.state'),
 'bird':(15,'research-object-completion/basket/state/basket-open.state'),
 'broken-flower':(7,'research-object-completion/clicks/state/flower-drop.state'),
 'pile':(14,'research-object-completion/outdoor/state/outside.state'),
 'food':(16,'research-object-completion/outdoor/state/outside.state'),
 'outside-plane':(1,'research-object-completion/flight-prizes/state/room-1.state'),
}
def capture(output,case,hold):
 output.mkdir(parents=True,exist_ok=False);kind,source=CASES[case];origin=DATA/source
 report=dict(complete=False,passed=False,case=case,hold_frames=hold,restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),actions=[],checkpoints=[])
 native=Recorder(DATA/'capture-core/dosbox_pure_libretro.dll',DATA/'source/reference-v1.zip',output);pending=[]
 def action(frames,point=None,left=False):
  before=state(native);mouse=dict(left=left)
  if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
  entry=dict(frames=frames,mouse=mouse);report['actions'].append(entry);native.perform([entry]);after=state(native)
  pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
 def checkpoint(name):
  native.save(name,ram=True);m=state(native);report['checkpoints'].append(dict(name=name,inputs=pending[:],after=m));pending.clear()
  print(name,m['seed'],[(o['type'],o['state']) for o in m['objects']],flush=True);return m
 try:
  native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544;native.perform([dict(frames=60)])
  if case=='outside-plane':
   m=state(native);r=next(o['rect']for o in m['objects']if o['type']==1)
   action(30,[(r[1]+r[3])//2,(r[0]+r[2])//2]);action(25,left=True);action(20,[305,185],left=True);action(350)
   action(30,[275,190]);action(8,left=True);action(600)
   report['setup_actions']=report['actions'];report['actions']=[];pending.clear()
  initial=checkpoint('initial');assert initial['selected'] and initial['scene']in[4,5]
  if case=='outside-plane':assert initial['scene']==4 and any(o['type']==1 and not o['inside']for o in initial['objects'])
  object=next(o for o in initial['objects']if o['type']==kind);r=object['rect'];point=[(r[1]+r[3])//2,(r[0]+r[2])//2]
  action(30,point);action(8,left=True);checkpoint('pressed')
  if hold>8:action(hold-8,left=True);checkpoint('held')
  action(20);checkpoint('released');action(800);final=checkpoint('settled')
  if case=='pile':assert not any(o['type']==14 for o in final['objects'])
  if case=='bird':assert not any(o['type']==15 for o in final['objects'])
  if case=='outside-plane':assert not any(o['type']==1 for o in final['objects'])
  report.update(complete=True,passed=True,snapshot_boundary_version=native.snapshot_boundary_version)
 finally:
  native.close();report['timeline_sha256']=digest(output/'frames.jsonl');(output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report['passed']
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=CASES,required=True);p.add_argument('--hold',type=int,choices=[8,30,60],default=8);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if capture(a.output,a.case,a.hold)else 1)
