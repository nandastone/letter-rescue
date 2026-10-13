"""Play the original board game to its ending through mouse inputs only."""
from pathlib import Path
import argparse,ctypes as C,json,struct
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture(output,seek_loss=False,chips=False):
    if seek_loss and chips:raise ValueError('Select money loss or chip win')
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/('research-boardgame/chip-carry-a/state/chip-started.state' if chips else 'research-boardgame/turn-b/state/started.state')
    code=(DATA/'research-resources/unpacked.bin').read_bytes()
    adjacency=[struct.unpack_from('<4b',code,0x308e0+0x264+4*i) for i in range(24)]
    rects=[struct.unpack_from('<4h',code,0x308e0+0x174+8*i) for i in range(24)]
    report=dict(schema=1,complete=False,passed=False,seek_loss=seek_loss,chips=chips,core_sha256=digest(core),content_sha256=digest(content),restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),adapter_sha256=digest(Path(__file__).with_name('libretro.py')),actions=[],decisions=[])
    exchange_attempt=0
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        def ram():
            return next(C.string_at(ptr+offset,size) for start,ptr,offset,size in native.memory if start==0 and ptr)
        def state():
            data=ram();ds=0x323f0;w=lambda at:struct.unpack_from('<h',data,ds+at)[0]
            shared=(w(0x4ad6)&65535)*16-0x1860
            return dict(player=w(0x52d8),nodes=[w(0x52c4+2*i) for i in range(2)],balances=[w(0x5a0c+2*i) for i in range(2)],remaining=w(0x5276),gameover=w(0x5810),types=[w(0x59da+2*i) for i in range(24)],coins=[[w(0x5554+12*i+2*j) for j in range(6)] for i in range(2)],scene=struct.unpack_from('<h',data,shared+0xb34)[0],pointer=[w(0x2066),w(0x2064)],seed=struct.unpack_from('<I',data,ds+0x5290)[0])
        def perform(actions):
            report['actions'].extend(actions);native.perform(actions)
        def paths(node,left):
            if left==0:
                return [[]]
            return [[next]+rest for next in adjacency[node] if next>=0 for rest in paths(next,left-1)]
        def click(x,y,name,wait=2000):
            px,py=state()['pointer']
            perform([dict(frames=10,mouse=dict(dx=2*(x-px),dy=2*(y-py))),dict(frames=1,mouse=dict(left=True)),dict(frames=wait,capture=name)])
        if seek_loss:
            # Ordinary options inputs: both human seats, highest money goal.
            # This avoids the low goal ending the game before payments deplete it.
            click(293,9,'setup-options',100)
            click(154,56,'setup-friend',100)
            click(154,108,'setup-goal-0',100)
            click(154,147,'setup-goal-1',100)
            click(160,167,'setup-play')
        perform([dict(frames=100,capture='initial')])
        report['initial']=state()
        for index in range(200 if seek_loss else 100):
            before=state()
            if before['gameover']:
                report['ending']=before;report['passed']=not seek_loss or 0 in before['balances'];break
            if chips and before['scene']==25:
                # Each stack is an ordinary legal mouse target. Wrong-stack
                # attempts are retained, so the replay also checks rejection.
                x,y=[286,262,238][exchange_attempt%3],58
                exchange_attempt+=1;action='exchange-'+str(x)
            elif before['scene']==(24 if chips else 16):
                amounts=[sum(n*v for n,v in zip(coins,[100,50,25,10,5,1])) for coins in before['coins']]
                choice=(0 if amounts[0]>=amounts[1] else 1) if before['player']==0 and not seek_loss else (0 if amounts[0]<=amounts[1] else 1)
                if chips:choice=0
                x,y=(244,132) if chips else (266,60 if choice==0 else 146);action='choose-'+str(choice)
            elif before['remaining']>0:
                options=paths(before['nodes'][before['player']],before['remaining'])
                options.sort(key=lambda path:before['types'][path[-1]],reverse=seek_loss)
                node=options[0][0];top,left,bottom,right=rects[node]
                x,y=(left+right)//2,(top+bottom)//2;action='move-'+str(node)
            else:
                x,y=94,58;action='roll'
            px,py=before['pointer'];name=f'step-{index:02d}'
            perform([dict(frames=10,mouse=dict(dx=2*(x-px),dy=2*(y-py))),dict(frames=1,mouse=dict(left=True)),dict(frames=2000,capture=name)])
            after=state();report['decisions'].append(dict(name=name,action=action,point=[x,y],before=before,after=after))
            print(name,action,'player',after['player'],'balances',after['balances'],'scene',after['scene'],'over',after['gameover'],flush=True)
        report.update(complete=True,capture_boundary_version=native.capture_boundary_version,snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index,options={k.decode():v.decode() for k,v in native.values.items()})
    finally:
        if native:
            native.close()
        if (output/'frames.jsonl').exists():
            report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('COMPLETE' if report['passed'] else 'NO ENDING',flush=True)
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--seek-loss',action='store_true');parser.add_argument('--chips',action='store_true')
    args=parser.parse_args()
    raise SystemExit(0 if capture(args.output,args.seek_loss,args.chips) else 1)
