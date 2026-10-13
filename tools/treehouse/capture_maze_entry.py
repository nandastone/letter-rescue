"""Capture first maze tutorial, piano return, and interrupted second entrance."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest
from capture_theater_audio_journey import AudioRecorder
from capture_title_midi import MusicRecorder
from verify_maze_generation import model

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'


def capture(output,observe=False,skip=False,observe_midi=False,trace_core=False):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    if observe_midi or trace_core:
        core=DATA/'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    origin=DATA/'research-music-followup/menus/state/click-1.state'
    report=dict(complete=False,passed=False,actions=[],checkpoints=[],core_sha256=digest(core),content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),skip_tutorial=skip)
    native=None
    try:
        native=(MusicRecorder if observe_midi else AudioRecorder if observe else Recorder)(core,content,output)
        native.perform([dict(frames=1800)]);native.restore(origin);native.image_base=544
        if observe_midi:
            native.events.clear()
        def ram():
            native.snapshot_boundary()
            return next(C.string_at(p+o,l) for s,p,o,l in native.memory if s==0 and p)
        def state():
            b=ram();d=0x323f0;s=0x318b0
            w=lambda p:struct.unpack_from('<H',b,p)[0]
            handle=w(d+0x528e);off,seg=struct.unpack_from('<HH',b,d+handle)
            adjust=16*w(d+0x4a54)-(544+0x2f180);song=seg*16+(off&15)+6-adjust
            return dict(tick=struct.unpack_from('<I',b,d+0x201e)[0],pointer=[w(d+0x2066),w(d+0x2064)],phase=w(s+0xb34),first_intro=w(544+0x2f9f0+0x5d3),
                song=list(b[song:song+65]),selection=list(b[s+0x9e:s+0xa2]),composing=bool(w(s+0xa2)),advanced=bool(w(s+0xa4)),
                earned=b[s+0x9e6],actor=list(struct.unpack_from('<4h',b,s+0x9ba)),frog=list(struct.unpack_from('<4h',b,s+0x9c2)))
        pending=[]
        def action(frames,point=None,left=False):
            before=state();mouse=dict(left=left)
            if point:mouse.update(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))
            a=dict(frames=frames,mouse=mouse);report['actions'].append(a);native.perform([a]);after=state()
            pending.append(dict(from_tick=before['tick'],to_tick=after['tick'],point=after['pointer'],left=left))
        def checkpoint(name):
            native.save(name,ram=True);after=state();after['maze']=model(output/'state'/f'{name}.ram-0')
            report['checkpoints'].append(dict(name=name,inputs=pending[:],after=after));pending.clear()
            print(name,'phase',after['phase'],'node',after['maze']['node'],'first',after['first_intro'],flush=True)
        def click(point,wait=10):
            action(30,point);action(10,left=True);action(wait)
        native.perform([dict(frames=40)]);checkpoint('initial')
        click([31,157]);checkpoint('entered')
        for i in range(40 if not skip else 12):action(80);checkpoint(f'intro-{i:02}')
        if skip:
            click([160,190],1800);checkpoint('tutorial-skipped')
        click([291,10],300);checkpoint('piano-return')
        click([31,157],160);checkpoint('reentered')
        click([160,190],2000);checkpoint('second-settled')
        click([291,10],300);checkpoint('final-piano')
        report.update(complete=True,passed=True,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version)
        if observe_midi:
            report['midi_events']=native.events
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--observe-audio',action='store_true');parser.add_argument('--skip-tutorial',action='store_true')
    parser.add_argument('--observe-midi',action='store_true')
    parser.add_argument('--trace-core',action='store_true',help='Use the same core without MIDI observation for a paired control')
    a=parser.parse_args();raise SystemExit(0 if capture(a.output,a.observe_audio,a.skip_tutorial,a.observe_midi,a.trace_core) else 1)
