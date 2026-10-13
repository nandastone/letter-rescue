"""Capture the unchanged original with STATUS.DAT absent and a fixed BIOS clock.

The input archive differs only by removing the save file. Ordinary F2/Escape
writes the original's resulting defaults; no game RAM or executable is patched.
"""
import argparse,copy,hashlib,json,struct,zipfile
from pathlib import Path
from capture import Recorder,digest

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'testing/output/treehouse'

def capture(output):
    output.mkdir(parents=True,exist_ok=False)
    source=DATA/'source/reference-startup-v2.zip'
    content=output/'reference-fresh.zip'
    removed=[];files=[]
    with zipfile.ZipFile(source) as z,zipfile.ZipFile(content,'x') as target:
        for info in z.infolist():
            if info.filename.lower()=='thetreeh/status.dat':
                removed.append(info.filename);continue
            raw=z.read(info.filename)
            target.writestr(copy.copy(info),raw)
            files.append(dict(name=info.filename,sha256=hashlib.sha256(raw).hexdigest()))
    assert len(removed)==1
    core=DATA/'trace-core-activity-backdrop-b/dosbox_pure_trace.dll'
    actions=[dict(frames=1800,capture='selection'),dict(frames=5,keys=['f2']),dict(frames=25,capture='preferences'),dict(frames=5,keys=['escape']),dict(frames=40,capture='saved')]
    report=dict(passed=False,scope=__doc__,source_sha256=digest(source),content_sha256=digest(content),core_sha256=digest(core),removed=removed,unchanged_files=files,actions=actions)
    native=None
    try:
        native=Recorder(core,content,output)
        assert native.capture_boundary_version==1 and native.snapshot_boundary_version==2
        native.perform(actions)
        report.update(complete=True,runs=native.frame_count,main_image_base=native.image_base,snapshot_boundary_version=native.snapshot_boundary_version)
    finally:
        if native:native.close()
        (output/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for name in ['selection','preferences','saved']:
        ram=(output/'state'/f'{name}.ram-0').read_bytes();base=report['main_image_base']
        shared=base+0x31690;ds=base+0x321d0
        count=struct.unpack_from('<H',ram,ds+0x556c)[0]
        raw=ram[shared+0x48:shared+0x932]+struct.pack('<H',count)+ram[ds+0x5830:ds+0x59d4]
        assert len(raw)==2704
        (output/f'{name}-memory-status.dat').write_bytes(raw)
        report.setdefault('states',{})[name]=dict(seed=struct.unpack_from('<I',ram,ds+0x5290)[0],objects=count,maze=struct.unpack_from('<6H',raw,0x8da),status_sha256=hashlib.sha256(raw).hexdigest())
    saves=list((output/'state').glob('*.pure.zip'))
    for save in saves:
        with zipfile.ZipFile(save) as z:
            for name in z.namelist():
                if name.upper().endswith('/STATUS.DAT'):
                    raw=z.read(name);(output/'status-written.dat').write_bytes(raw)
                    report['written_status_sha256']=hashlib.sha256(raw).hexdigest()
    report['passed']=(output/'status-written.dat').exists()
    (output/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],states=report['states']),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();raise SystemExit(0 if capture(args.output) else 1)
