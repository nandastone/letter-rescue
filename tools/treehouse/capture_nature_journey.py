"""Play a complete original animal game, prize and room return using mouse input."""
from pathlib import Path
import argparse, ctypes as C, json, struct
from capture import Recorder, digest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'


def capture(output,robot=False):
    output.mkdir(parents=True,exist_ok=False)
    core=DATA/'capture-core/dosbox_pure_libretro.dll';content=DATA/'source/reference-v1.zip'
    origin=DATA/'research-nature/quiz-roll-capture/state/quiz-ready.state'
    tables=json.loads((DATA/'research-nature/tables.json').read_text(encoding='utf-8'))
    rects=tables['quiz_rectangles'];options=tables['quiz_options_rectangles']
    report=dict(complete=False,passed=False,robot=robot,core_sha256=digest(core),content_sha256=digest(content),
                restore_source=str(origin),restore_sha256=digest(origin),tool_sha256=digest(Path(__file__)),
                adapter_sha256=digest(Path(__file__).with_name('libretro.py')),actions=[],checkpoints=[])
    native=None
    try:
        native=Recorder(core,content,output);native.perform([dict(frames=1800)])
        native.restore(origin);native.image_base=544
        def state():
            native.snapshot_boundary()
            data=next(C.string_at(ptr+offset,size) for start,ptr,offset,size in native.memory if start==0 and ptr)
            ds=0x323f0;w=lambda off:struct.unpack_from('<h',data,ds+off)[0]
            shared=(w(0x4ada)&65535)*16-0x1860
            words=lambda off,n:list(struct.unpack_from('<'+str(n)+'H',data,shared+off))
            cards=words(6,16)
            return dict(cards=[cards[:8],cards[8:]],secret=words(0x992,2),opponent=words(0x3fe,1)[0],
                        help=[bool(x) for x in words(0x400,3)],player=w(0x5250),asked=[w(0x52dc),w(0x52de)],
                        remaining=[w(0x52ee),w(0x52f0)],available=[i for i in range(8) if w(0x52a2+2*i)],
                        answered=w(0x529e),guessing=w(0x557c),win_phase=w(0x55ea),winner=w(0x57ca),
                        seed=struct.unpack_from('<I',data,ds+0x5290)[0],tick=struct.unpack_from('<I',data,ds+0x201e)[0],pointer=[w(0x2066),w(0x2064)],
                        idle_timer=w(0x201a),scene=words(0xb34,1)[0],
                        objects=[dict(type=w(0x5830+20*i),state=w(0x5832+20*i),inside=bool(w(0x5834+20*i)),rect=[w(0x5836+20*i+2*j) for j in range(4)]) for i in range(w(0x556c))],
                        prize_choices=[w(0x57cc+2*i) for i in range(6)],
                        shelf=[bool(data[ds+0x55f8+i]) for i in range(6)],visited_mask=w(0x52f6))
        def act(a):report['actions'].append(a);native.perform([a])
        def click(rect,name,wait=600):
            before=state();top,left,bottom,right=rect;x,y=(left+right)//2,(top+bottom)//2
            px,py=before['pointer'];act(dict(frames=10,mouse=dict(dx=2*(x-px),dy=2*(y-py))))
            input_tick=state()['tick']
            act(dict(frames=1,mouse=dict(left=True)));act(dict(frames=wait,capture=name))
            after=state();report['checkpoints'].append(dict(name=name,point=[x,y],input_tick=input_tick,wait_frames=wait,before=before,after=after))
            print(name,'player',after['player'],'answered',after['answered'],'guess',after['guessing'],'win',after['win_phase'],flush=True)
            return after
        click(rects[11],'setup-options',100);click(options[4 if robot else 3],'setup-robot' if robot else 'setup-friend',100)
        for role in [0,1]:
            if state()['help'][role]:click(options[5+role],f'setup-help-{role}',100)
        click(options[10],'initial',100)
        if robot:
            for turn in range(32):
                next_player=1-state()['player']
                s=click(rects[36],f'turn-{turn:02d}',2400 if next_player==1 else 350)
                if s['win_phase']:
                    break
                if s['player']==0:
                    s=click(rects[37],f'guess-entry-{turn:02d}',200)
                    assert s['guessing']
                    # A legal wrong guess keeps the human from winning while
                    # the original robot chooses questions and solves its hand.
                    wrong=next(i for i in range(8) if i!=s['secret'][0] and s['remaining'][0]&(1<<i))
                    s=click(rects[20+wrong],f'wrong-guess-{turn:02d}',1000)
                else:
                    assert s['answered']==1, 'Robot turn has not finished'
            assert s['winner']==1 and s['win_phase']==2, 'Robot did not win'
        else:
            s=click(rects[36],'first-turn',350)
            assert s['answered']==0 and s['available']
            click(rects[12+s['available'][0]],'question-answer',1200)
            click(rects[36],'second-turn',350)
            s=click(rects[37],'wrong-guess-entry',300)
            assert s['guessing']
            click(rects[20+(s['secret'][s['player']]+1)%8],'wrong-guess',600)
            click(rects[36],'third-turn',350)
            s=click(rects[37],'correct-guess-entry',300)
            assert s['guessing']
            s=click(rects[20+s['secret'][s['player']]],'victory',1200)
        assert s['win_phase']==2
        # Original reveal boxes: the other shrub can be inspected after winning.
        reveals=[[108,180,145,249],[151,251,188,320]]
        click(reveals[1-s['winner']],'other-animal',900)
        s=click(rects[36],'prize-chooser',200)
        choices=s['prize_choices'];slot=4 if robot else next((i for i,v in enumerate(choices) if v in [2,7]),0)
        report['selected_prize']=dict(slot=slot,type=choices[slot])
        prize_rects=[[54,32,76,62],[54,64,76,94],[54,96,76,126],[78,32,100,62],[78,64,100,94],[78,96,100,126]]
        click(prize_rects[slot],'prize-delivered',1200)
        click(rects[9],'back-to-nature',100)
        click(rects[0],'back-to-room',1800)
        if robot:
            assert state()['shelf'][slot] and state()['visited_mask']==7
            # Real room telescope hotspot, then the displayed shelf and return.
            s=click([129,194,131,196],'shelf-first-visit',1800)
            assert s['scene']==12 and s['visited_mask']==15
            click([79,159,81,161],'shelf-replay',1800)
            s=click([9,310,11,312],'shelf-return',1200)
            assert s['scene']==5 and s['shelf'][slot]
            # An activity visit must preserve the robot's session prize.
            click([119,54,121,56],'theater-visit',900)
            s=click([9,310,11,312],'theater-return',1500)
            assert s['scene']==5 and s['shelf'][slot]
        report.update(complete=True,passed=True,capture_boundary_version=native.capture_boundary_version,
                      snapshot_boundary_version=native.snapshot_boundary_version,video_callbacks=native.callback_index,
                      options={k.decode():v.decode() for k,v in native.values.items()})
    except Exception as error:
        report['error']=repr(error)
        raise
    finally:
        if native:native.close()
        if (output/'frames.jsonl').exists():report['timeline_sha256']=digest(output/'frames.jsonl')
        (output/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--robot',action='store_true')
    args=p.parse_args()
    raise SystemExit(0 if capture(args.output,args.robot) else 1)
