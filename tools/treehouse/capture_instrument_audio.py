"""Capture original piano attacks, sustained notes and forced releases via UI."""
from pathlib import Path
import argparse, ctypes as C, json, struct, zipfile
from resources import parse_archive
from images import decode_shape
from capture import Recorder, digest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'testing/output/treehouse'


def capture(output, ids):
    output.mkdir(parents=True, exist_ok=False)
    core = DATA/'capture-core/dosbox_pure_libretro.dll'
    content = DATA/'source/reference-v1.zip'
    origin = DATA/'demo-piano/state/piano.state'
    tables = json.loads((ROOT/'testing/treehouse/music-followup-tables.json').read_text(encoding='utf-8'))
    # Portrait hit rectangles overlap. Choose a point belonging only to this
    # portrait so the original's first matching rectangle cannot select a neighbor.
    with zipfile.ZipFile(DATA/'source/The_Treehouse_1991.zip') as archive:
        data=archive.read('TheTreeh/modules.dat')
    shapes={}
    for record in parse_archive(data):
        if record['tag']=='SHAP' and 2400<=record['id']<2470:
            at=record['payload_offset'];shapes[record['id']]=decode_shape(data[at:at+record['size']])[:2]
    points={}
    for category,members in enumerate(tables['members']):
        rects=[]
        for index,id in enumerate(members):
            w,h=shapes[2401+10*category+index];x=tables['portrait_x'][id];y=tables['portrait_y'][id]
            rects.append((x-6,y-6,x+w+6,y+h+6))
        for index,id in enumerate(members):
            left,top,right,bottom=rects[index];cx=(left+right)//2;cy=(top+bottom)//2
            choices=[(x,y) for y in range(max(1,top),min(125,bottom)) for x in range(max(1,left),min(304,right))
                     if not any(l<=x<r and t<=y<b for j,(l,t,r,b) in enumerate(rects) if j!=index)]
            assert choices,('no unique portrait point',id)
            points[id]=min(choices,key=lambda xy:(xy[0]-cx)**2+(xy[1]-cy)**2)
    report = dict(passed=False, complete=False, core_sha256=digest(core), content_sha256=digest(content),
                  restore_source=str(origin), restore_sha256=digest(origin), tool_sha256=digest(Path(__file__)),
                  ids=ids, portrait_points=points, cases=[], actions=[])
    native = None
    try:
        native = Recorder(core, content, output)
        native.perform([dict(frames=1800)]); native.restore(origin); native.image_base=544

        def state():
            native.snapshot_boundary()
            ptr = next(p+o for s,p,o,l in native.memory if s==0 and p)
            ds = ptr+0x323f0
            word = lambda off: struct.unpack('<h', C.string_at(ds+off,2))[0]
            uint = lambda off: struct.unpack('<I', C.string_at(ds+off,4))[0]
            off,seg = struct.unpack('<HH', C.string_at(ds+0x2120,4))
            address = ptr+seg*16+off-0x1860
            handle = word(0x528e)&65535
            songoff,songseg = struct.unpack('<HH', C.string_at(ds+handle,4))
            song = C.string_at(ptr+songseg*16+(songoff&15)+6-0x1860,65)
            active = word(0x211c)
            return dict(run=native.run_index, audio_sample=len(native.audio)//4,
                        tick=uint(0x201e), pointer=[word(0x2066),word(0x2064)],
                        instrument=song[3], active=active, release=word(0x211e),
                        header=list(struct.unpack('<BHBHHH',C.string_at(address,10))) if active else None)

        def frames(count, rows=None):
            if rows is None:
                native.perform([dict(frames=count)])
            else:
                for _ in range(count):
                    native.perform([dict(frames=1)]); rows.append(state())

        def click(point, wait=80):
            before=state()
            actions=[dict(frames=10,mouse=dict(dx=2*(point[0]-before['pointer'][0]),dy=2*(point[1]-before['pointer'][1]))),
                     dict(frames=1,mouse=dict(left=True)),dict(frames=wait,mouse=dict(left=False))]
            report['actions'].extend(actions); native.perform(actions)

        def center(rect):return [(rect[1]+rect[3])//2,(rect[0]+rect[2])//2]

        frames(120)
        for id in ids:
            category=id if id<7 else next(i for i,members in enumerate(tables['members']) if id in members)
            click([22,124]);click(center(tables['menu_rectangles'][2+category]))
            point=center(tables['instrument_rectangles'][3]) if id<7 else points[id]
            click(point,1000);click(center(tables['instrument_rectangles'][1]),150)
            selected=state();assert selected['instrument']==id,(id,selected)
            for label,key,held in [('short','n',12),('long','n',180),('high','/',90)]:
                rows=[];frames(60)
                case=dict(instrument=id,label=label,key=key,held_frames=held,start=state(),rows=rows)
                native.key(key,True);frames(held,rows);case['keyup']=state()
                native.key(key,False);frames(150,rows);case['end']=state()
                assert any(row['active'] for row in rows),(id,label,'no sounding note')
                assert not case['end']['active'],(id,label,'note did not stop')
                report['cases'].append(case)
                print(id,label,'captured',flush=True)
            native.save(f'instrument-{id}',ram=True)
        report.update(passed=True,complete=True,snapshot_boundary_version=native.snapshot_boundary_version,
                      sample_rate=native.av.timing.sample_rate,fps=native.av.timing.fps)
    finally:
        if native:native.close()
        if (output/'state/audio.wav').exists():report['audio_sha256']=digest(output/'state/audio.wav')
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ids',type=int,nargs='+',default=list(range(42)))
    a=p.parse_args();raise SystemExit(0 if capture(a.output,a.ids) else 1)
