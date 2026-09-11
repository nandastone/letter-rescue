"""Execute WR1's original timestamp code with controlled DOS date/TZ inputs.

Research only. Requires Unicorn in testing/output/python_packages or Python's
environment. Relocates an in-memory image exactly as an MZ loader would; never
modifies the executable. Only getenv("TZ") is replaced with the supplied input.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'testing/output/python_packages'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *

EXE_SHA256='b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f'
LOAD=0x1000
def timestamp(executable,date,tz=None):
    EXE=executable
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,2*1024*1024)
    header=struct.unpack_from('<H',EXE,8)[0]*16
    code=bytearray(EXE[header:])
    count=struct.unpack_from('<H',EXE,6)[0];table=struct.unpack_from('<H',EXE,24)[0]
    for i in range(count):
        off,seg=struct.unpack_from('<HH',EXE,table+i*4);p=seg*16+off
        struct.pack_into('<H',code,p,(struct.unpack_from('<H',code,p)[0]+LOAD)&65535)
    u.mem_write(LOAD*16,bytes(code))
    ds=LOAD+0x2255;ss=0x9000;stop=0x80000
    u.reg_write(UC_X86_REG_DS,ds);u.reg_write(UC_X86_REG_ES,ds)
    u.reg_write(UC_X86_REG_SS,ss);u.reg_write(UC_X86_REG_SP,0xff00)
    # far return address, followed by pointers to DOS date/time structures.
    u.mem_write(ss*16+0xff00,struct.pack('<6H',0,0x8000,0x100,ss,0x200,ss))
    y,m,d,h,mi,s=date
    u.mem_write(ss*16+0x100,struct.pack('<HBB',y,d,m))
    u.mem_write(ss*16+0x200,bytes([mi,h,0,s]))
    if tz is not None:u.mem_write(ss*16+0x300,tz.encode('ascii')+b'\0')
    def hook(u,address,size,data):
        if address==stop:u.emu_stop()
        # getenv("TZ") is the only external input; all conversion code executes.
        if address==LOAD*16+0x2116*16+2:
            u.reg_write(UC_X86_REG_AX,0x300 if tz is not None else 0)
            u.reg_write(UC_X86_REG_DX,ss if tz is not None else 0)
            sp=u.reg_read(UC_X86_REG_SP)
            ip,cs=struct.unpack('<HH',u.mem_read(ss*16+sp,4))
            u.reg_write(UC_X86_REG_SP,(sp+4)&65535)
            u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
    u.hook_add(UC_HOOK_CODE,hook)
    u.reg_write(UC_X86_REG_CS,LOAD+0x21da);u.reg_write(UC_X86_REG_IP,0xe)
    u.emu_start(LOAD*16+0x21da*16+0xe,stop+1,count=100000)
    assert u.reg_read(UC_X86_REG_CS)*16+u.reg_read(UC_X86_REG_IP)==stop
    return u.reg_read(UC_X86_REG_DX)*65536+u.reg_read(UC_X86_REG_AX)

if __name__=='__main__':
    import calendar,datetime
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    executable=args.exe.read_bytes()
    if hashlib.sha256(executable).hexdigest()!=EXE_SHA256:raise ValueError('Unsupported WR1.EXE')
    dates=set()
    for year in (1980,1984,1986,1987,1992,2000,2026,2038,2099):
        dates.update([(year,1,1,0,0,0),(year,12,31,23,59,59),
                      (year,2,calendar.monthrange(year,2)[1],23,59,59),(year,3,1,0,0,0)])
        for month in (4,10):
            sundays=[d for d in range(1,calendar.monthrange(year,month)[1]+1)
                     if datetime.date(year,month,d).weekday()==6]
            for day in (sundays[0],sundays[-1]):
                dates.update((year,month,day,*time) for time in ((1,59,59),(2,0,0),(2,0,1)))
    rng=random.Random(1992)
    for unused in range(50):
        year=rng.randrange(1980,2100);month=rng.randrange(1,13)
        dates.add((year,month,rng.randrange(1,calendar.monthrange(year,month)[1]+1),
                   rng.randrange(24),rng.randrange(60),rng.randrange(60)))
    cases=[]
    for date in sorted(dates):
        for tz in (None,'UTC0','EST5EDT','JST-9','AEST-10','ABC+3','ABC5x','ABC5--XYZ'):
            value=timestamp(executable,date,tz)
            cases.append({'date':list(date),'tz':tz,'timestamp':value,'seed':value&65535})
    result={'source_exe_sha256':EXE_SHA256,'conversion_file_offset':'0x247ae',
            'timezone_file_offset':'0x24b67','daylight_file_offset':'0x24d4c',
            'method':'Original relocated x86 instructions executed in Unicorn 2.1.4; only getenv(TZ) stubbed. No instruction timing claim.',
            'cases':cases}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(cases)} original-code timestamp/seed cases to {args.output}')
