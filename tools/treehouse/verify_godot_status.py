"""Check STATUS.DAT byte preservation, decoded fields, editing and reload in Godot.

Includes the packaged file and two native-written saves; synthetic cases cover
all mapped sections, unknown/trailing data and unsafe inputs. This is save-format
and runtime integration evidence, not complete original load timing/RNG parity.
"""
import argparse,base64,hashlib,json,struct,subprocess
from pathlib import Path
from build_demo import ROOT

def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    assets=json.loads((ROOT/'treehouse-godot/data/original.json').read_text())
    original=base64.b64decode(assets['status']);cases=[]
    def add(name,data):
        (output/(name+'.dat')).write_bytes(data)
        cases.append(dict(name=name,sha256=hashlib.sha256(data).hexdigest()))
    add('packaged',original)
    for label,source in [('native-settings','research-settings/native/status-written.dat'),('native-theater','research-rewards/theater-persistence/status-written.dat')]:
        add(label,(ROOT/'testing/output/treehouse'/source).read_bytes())
    rich=bytearray(original)
    def put(offset,*values):struct.pack_into('<'+'H'*len(values),rich,offset,*[v&65535 for v in values])
    rich[:86]=bytes([0]*86);rich[0]=227;rich[43]=84
    rich[0x56:0x5a]=bytes([3,2,9,4])
    for offset,value in [(0x5a,1),(0x5c,1),(0x5e,1),(0x60,1),(0x62,0),(0x64,0),(0x66,1),(0x68,0xbeef),(0x6a,1),(0x6c,2),(0x6e,1),(0x70,0),(0x72,-1),(0x3a6,1),(0x3a8,1),(0x3b6,2),(0x3be,1),(0x3c0,1),(0x8e6,0xface),(0x8e8,5)]:put(offset,value)
    put(0x74,*([0]*7));put(0x3aa,0,1,2,2,0,1);put(0x3b8,1,0,1)
    put(0x3c2,0,1,2,3);put(0x8a2,3,1,0,2)
    for i in range(7):put(0x886+4*i,-5+i,8-i)
    put(0x8da,3,8,11,15,18,23)
    for i in range(24):put(0x8aa+2*i,2 if i in [3,8,11,15,18,23] else 0)
    for time in range(2):
        animals=[(i,a) for i,a in enumerate(assets['nature']['animals']) if a['active_time']==time][:2]
        put(0x82+2*time,len(animals))
        for i,(id,a) in enumerate(animals):
            slot=2*i+time;w,h=assets['shapes'][f'modules:{a["large"]}'][:2];x,y=135+i*20,10+i*20
            put(0x86+2*slot,id);put(0x126+8*slot,y,x,y+h,x+w)
    t=assets['theater']
    for place in range(6):
        put(0x3ca+2*place,1);slot=20*place;group=t['prop_group'][place];offset=t['prop_first'][place];pal=3175 if group else 3145
        w,h=assets['shapes'][f'modules:{pal+offset}'][:2];x,y=100+place,75+place
        put(0x796+2*slot,(group<<8)|offset);put(0x3d6+8*slot,y,x,y+h,x+w)
    put(0x8ea,5)
    for i,(type,state) in enumerate([(6,12),(7,5),(15,1),(14,4),(8,1)]):
        r=assets['room']['objects'][type]['inside']
        if type==14:r=[155,120,171,145]
        put(0x8ec+20*i,type,state,1,*r,0xbeef,0x1234,0x5678)
    rich.extend(b'opaque trailing bytes\x00\xff')
    add('rich',rich)
    filtered=bytearray(rich)
    struct.pack_into('<H',filtered,0x86,65535)
    struct.pack_into('<H',filtered,0x3ca,2)
    filtered[0x3de:0x3e6]=filtered[0x3d6:0x3de]
    filtered[0x798:0x79a]=filtered[0x796:0x798]
    struct.pack_into('<H',filtered,0x796,65535)
    struct.pack_into('<H',filtered,0x8ea,4)
    add('filtered',filtered)
    invalid=bytearray(rich)
    for offset in [0x5a,0x5c,0x5e,0x60,0x62,0x64,0x66,0x6a,0x6c,0x6e,0x70,0x72,0x82,0x84,0x3a6,0x3a8,0x3b6,0x3be,0x3c0,0x8e8,0x8ea]:struct.pack_into('<H',invalid,offset,65535)
    invalid[0x56:0x5a]=bytes([255]*4)
    for i in range(24):struct.pack_into('<H',invalid,0x8aa+2*i,65535)
    for i in range(6):struct.pack_into('<H',invalid,0x8da+2*i,3)
    for i in range(4):struct.pack_into('<H',invalid,0x8a2+2*i,0)
    add('invalid',invalid)
    (output/'fixture.json').write_text(json.dumps(cases),encoding='utf-8')
    with (output/'godot.log').open('w') as log:
        p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_status.gd','--',str(output.resolve())],stdout=log,stderr=subprocess.STDOUT,timeout=90)
    log=(output/'godot.log').read_text()
    if p.returncode or 'ERROR' in log:raise RuntimeError(log[:12000])
    actual=json.loads((output/'godot.json').read_text());checks=actual['checks']
    for c in cases:
        before=(output/(c['name']+'.dat')).read_bytes();after=(output/(c['name']+'-roundtrip.dat')).read_bytes()
        checks.append(dict(name=c['name']+': unchanged bytes including opaque/inactive/trailing',passed=before==after,sha256=c['sha256']))
        changed=(output/(c['name']+'-changed.dat')).read_bytes()
        different=[i for i,(a,b) in enumerate(zip(before,changed)) if a!=b]
        expected=bytearray(before);old=struct.unpack_from('<H',before,0x62)[0]
        struct.pack_into('<H',expected,0x62,1-int(bool(old) if old in (0,1) else True))
        checks.append(dict(name=c['name']+': sound-only mutation stays at word 0x62',passed=changed==expected,different_bytes=different))
    # Independently decode every simple scalar/array in the valid rich fixture.
    state=actual['rich'];u=lambda at:struct.unpack_from('<H',rich,at)[0];s=lambda at:struct.unpack_from('<h',rich,at)[0]
    expected=dict(pages=list(rich[0x56:0x5a]),composing=True,mode=1,repeating=True,settings=dict(advanced=True,sound=False,printing=False,printer=1,speed=True),cloud=2,nature_time=1,nature_attribute=0,nature_values=[u(0x74+2*i) for i in range(7)],board_mode=1,board_opponent=1,board_goals=[u(0x3aa+2*i) for i in range(6)],quiz_opponent=2,quiz_help=[True,False,True],theater_selection=[s(0x3c2+2*i) for i in range(4)],theater_order=[u(0x8a2+2*i) for i in range(4)],theater_actor=[[s(0x886+4*i),s(0x888+4*i)] for i in range(7)],theater_validation=5,maze_history=[i for i in range(24) if u(0x8aa+2*i)],maze_songs=[u(0x8da+2*i) for i in range(6)])
    expected['nature_category']=-1
    expected['nature_objects']=[[[u(0x86+2*(2*i+time)),s(0x128+8*(2*i+time)),s(0x126+8*(2*i+time))] for i in range(2)] for time in range(2)]
    expected['theater_flags']=[True,True]
    expected['theater_props']=[]
    for place in range(6):
        slot=20*place;code=u(0x796+2*slot);palette=3175 if code>>8 else 3145
        expected['theater_props'].append([dict(id=palette+(code&255),palette=palette,x=s(0x3d8+8*slot),y=s(0x3d6+8*slot))])
    expected['room_objects']=[dict(type=u(0x8ec+20*i),state=2 if i==0 else u(0x8ee+20*i),inside=True,rect=[s(0x8f2+20*i+2*j) for j in range(4)]) for i in [0,3,4]]
    for k,v in expected.items():checks.append(dict(name='rich decoded '+k,passed=state[k]==v,expected=v,actual=state[k]))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
    return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
