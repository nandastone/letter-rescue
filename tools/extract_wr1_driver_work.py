"""Extract static instruction boundaries for the recovered AdLib work planner.

The runtime catalogue has no operands, executable bytes or recorded event paths.
Live state chooses the paths in wr1_driver_work; this table only expands spans
into their original instruction boundaries for DOSBox block accounting.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'testing/output/python_packages'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16


def extract(executable):
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest!='b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
        raise ValueError('Unsupported WR1 executable')
    decoder = Cs(CS_ARCH_X86,CS_MODE_16)
    instructions = {}
    for start,end in [(0x50d9,0x510f),(0x56d9,0x579e),(0x57c4,0x59a0),
                      (0x59f7,0x5c57),(0x5c69,0x5ceb),(0x5feb,0x6319)]:
        for ins in decoder.disasm(data[0x19580+start:0x19580+end],start):
            instructions[str(ins.address)] = [ins.mnemonic,ins.address+ins.size]
    irq_instructions = {str(ins.address):[ins.mnemonic,ins.address+ins.size]
                        for ins in decoder.disasm(data[0x4344:0x4434],0x224)}
    main_instructions = {}
    for start,end in [(0x34ba,0x37a7),(0x40d2,0x40d5)]:
        for ins in decoder.disasm(data[start:end],start):
            branch = int(ins.op_str,16) if ins.mnemonic.startswith('j') else None
            main_instructions[str(ins.address)] = [ins.mnemonic,ins.address+ins.size,branch]
    keyboard_instructions = {}
    for start,end in [(0xc714,0xc7e2),(0xc882,0xc960)]:
        for ins in decoder.disasm(data[start:end],start):
            keyboard_instructions[str(ins.address)] = [ins.mnemonic,ins.address+ins.size]
    keyboard_targets = [0xc710+int.from_bytes(data[0xc7e2+2*i:0xc7e4+2*i],'little') for i in range(80)]
    movement_instructions = {}
    for start,end in [(0x37a4,0x3ba1),(0x3bd5,0x3d7e)]:
        for ins in decoder.disasm(data[start:end],start):
            movement_instructions[str(ins.address)] = [ins.mnemonic,ins.address+ins.size]
    movement_tables = {name:[int.from_bytes(data[0x24f50+offset+2*i:0x24f52+offset+2*i],'little') for i in range(8)]
                       for name,offset in [('left_walk',0x1cd),('right_walk',0x1e1),('poses',0x1f5)]}
    graphics_instructions = {}
    for start,end in [(0xf3f5,0xf456),(0x190ef,0x1919a),(0x1934e,0x19378),
                      (0x138d8,0x13aed),(0x13c91,0x14140),(0x163b6,0x163d9),(0x1919a,0x191d8),
                      (0x164e2,0x165fb),(0x167f6,0x16998),(0x18c5a,0x18ce9),(0x18dbe,0x18dce),
                      (0x17606,0x17698),(0xab25,0xc1aa),(0xf174,0xf3d1),(0xf508,0xf55a),
                      (0xce38,0xcf2e),(0xd2d1,0xd3a3),(0x3da3,0x3dad),(0x409b,0x40d2),
                      (0xc1aa,0xc6f9),(0xf6c8,0xf6f2),(0xf715,0xf73f),(0xdb86,0xdbd2),
                      (0x103d3,0x1058a),(0x10739,0x1075d),(0x107b2,0x10889),(0x22460,0x2247b),
                      (0x10296,0x10341),(0xa333,0xa34e)]:
        for ins in decoder.disasm(data[start:end],start):
            graphics_instructions[str(ins.address)] = [ins.mnemonic,ins.address+ins.size]
    return {'exe_sha256':digest,'instructions':instructions,'irq_file_base':0x4120,'irq_instructions':irq_instructions,
            'main_file_base':0x3360,'main_instructions':main_instructions,
            'movement_instructions':movement_instructions,'movement_tables':movement_tables,
            'keyboard_file_base':0xc710,'keyboard_instructions':keyboard_instructions,'keyboard_targets':keyboard_targets,
            'graphics_instructions':graphics_instructions}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--output',type=Path,default=Path('assets/audio/original/driver_work.json'))
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.executable),separators=(',',':'))+'\n')
