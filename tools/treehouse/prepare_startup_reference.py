"""Pin the emulated BIOS clock before starting the unchanged original game.

DOSBox's INT 21h Set System Time does not implement nonzero times. A tiny DOS
launcher uses the supported BIOS Set System Time service before TREEHSE.EXE.
This changes only the test platform clock; game files remain byte-identical.
"""
from pathlib import Path
import copy,hashlib,json,zipfile

DATA=Path(__file__).resolve().parents[2]/'testing/output/treehouse'
digest=lambda data:hashlib.sha256(data).hexdigest()


def prepare():
    source=DATA/'source/reference-v1.zip';output=DATA/'source/reference-startup-v2.zip'
    assert digest(source.read_bytes())=='a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c'
    # CX:DX=0; AH=1; INT 1Ah; AX=4C00h; INT 21h. BIOS midnight, then exit.
    launcher=bytes.fromhex('31 c9 31 d2 b4 01 cd 1a b8 00 4c cd 21')
    records=[]
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(output,'x') as target:
        for info in original.infolist():
            original_payload=original.read(info.filename);payload=original_payload
            if info.filename=='dosbox.conf':
                text=payload.decode();assert text.count('time 12:00:00')==1
                payload=text.replace('time 12:00:00','clock.com').encode()
            target.writestr(copy.copy(info),payload)
            records.append(dict(name=info.filename,sha256=digest(payload),game_file_unchanged=payload==original_payload))
        info=zipfile.ZipInfo('TheTreeh/clock.com',date_time=(1992,1,1,0,0,0));target.writestr(info,launcher)
    assert all(r['game_file_unchanged'] for r in records if r['name']!='dosbox.conf')
    report=dict(passed=True,source_sha256=digest(source.read_bytes()),content_sha256=digest(output.read_bytes()),launcher_hex=launcher.hex(),records=records,
                scope=__doc__.strip(),initial_bios_ticks=0)
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))


if __name__=='__main__':prepare()
