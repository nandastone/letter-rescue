"""Export instruction boundaries for the recovered heap work model."""
from pathlib import Path
import argparse, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SOURCE_SHA='f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f'

def export(source,output):
    data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched original executable')
    instructions=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(data[0xd510+0x6b06:0xd510+0x7079],0x6b06))
    if instructions[-1].address+instructions[-1].size!=0x7079:raise ValueError('Incomplete instruction decoding')
    output.write_text('// Instruction boundaries recovered from pinned DOS 1.1 resident code; no timing fixtures.\nconst OriginalHeapInstructionAddresses = '+str([i.address for i in instructions])+';\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.source,a.output)
