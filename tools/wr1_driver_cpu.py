"""Bounded 16-bit driver interpreter for research instruction counts.

Only executes WR1's embedded MIDI handlers. OPL busy waits are observed as a
separate primitive. This research tool is not part of the Godot runtime.
"""
from pathlib import Path
import hashlib
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'testing/output/python_packages'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_REG, CS_OP_IMM, CS_OP_MEM


def account_blocks(start_cycle,timeline,opl_intervals):
    """Predict non-IO timing, treating supplied OPL durations as opaque work.

    This diagnostic isolates instruction accounting; native OPL intervals are
    supplied by tests. It is not a complete prediction of driver duration.
    """
    cursor,block,index,lost = start_cycle,0,0,0
    boundary = (cursor//27000+1)*27000
    for operation,_ in timeline:
        if operation=='opl':
            cursor += opl_intervals[index]
            index += 1
            # The endpoint is before RET, with four POP instructions still
            # pending in the dynamic block. They can extend into the next ms.
            boundary = ((cursor-4)//27000+1)*27000
            cursor += 1
            finish = True
        else:
            cursor += 1
            block += 1
            finish = operation.startswith('j') or operation in ('call','ret','loop') or block==32
        if finish:
            block = 0
            if cursor>=boundary:
                lost += cursor-boundary
                cursor = boundary
                boundary += 27000
    if index!=len(opl_intervals):
        raise ValueError('OPL intervals do not match the executed path')
    return cursor,lost


class DriverCPU:
    def snapshot(self):
        result = {name:self.memory[offset] for name,offset in
                  [('mode',0x994),('rhythm',0x9a1),('percussion',0x749),('transpose',0x982)]}
        for name,offset,width,count in [('voices',0x791,2,9),('programs',0x7a3,1,16),
                                       ('volumes',0x7b3,1,16),('notes',0x7c3,1,9),
                                       ('levels',0x7cc,1,9),('bends',0x781,1,16)]:
            result[name] = [int.from_bytes(self.memory[offset+i*width:offset+(i+1)*width],'little') for i in range(count)]
        return result

    def __init__(self, executable, cmf, initial):
        if hashlib.sha256(executable).hexdigest()!='b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f':
            raise ValueError('Unsupported WR1 executable')
        if cmf[:4]!=b'CTMF' or initial['mode']!=1:
            raise ValueError('This research interpreter requires CMF / AdLib mode')
        self.code = executable[0x19580:0x19580+65536].ljust(65536,b'\0')
        self.memory = bytearray(self.code)
        self.decoder = Cs(CS_ARCH_X86,CS_MODE_16)
        self.decoder.detail = True
        self.cache = {}
        self.regs = {k:0 for k in ('ax','bx','cx','dx','si','di','bp','sp','cs','ds','es','ss')}
        self.flags = {'z':False,'c':False,'s':False,'o':False}
        for name,offset in [('mode',0x994),('rhythm',0x9a1),('percussion',0x749),('transpose',0x982)]:
            self.memory[offset] = initial[name]
        for name,offset,width in [('voices',0x791,2),('programs',0x7a3,1),('volumes',0x7b3,1),
                                  ('notes',0x7c3,1),('levels',0x7cc,1),('bends',0x781,1)]:
            for i,value in enumerate(initial[name]):
                self.memory[offset+i*width:offset+(i+1)*width] = value.to_bytes(width,'little')
        start = struct.unpack_from('<H',cmf,6)[0]
        for i in range(struct.unpack_from('<H',cmf,36)[0]):
            self.memory[0x12f+11*i:0x12f+11*(i+1)] = cmf[start+16*i:start+16*i+11]

    def reg(self,name,value=None):
        if len(name)==2 and name[1] in 'hl':
            base,shift = name[0]+'x',8 if name[1]=='h' else 0
            if value is not None:
                mask = 255<<shift
                self.regs[base] = (self.regs[base]&~mask)|((value&255)<<shift)
            return (self.regs[base]>>shift)&255
        if value is not None:
            self.regs[name] = value&65535
        return self.regs[name]

    def address(self,ins,operand):
        m = operand.mem
        return (m.disp+(self.reg(ins.reg_name(m.base)) if m.base else 0)+
                (self.reg(ins.reg_name(m.index))*m.scale if m.index else 0))&65535

    def read(self,ins,operand):
        if operand.type==CS_OP_IMM:
            return operand.imm
        if operand.type==CS_OP_REG:
            return self.reg(ins.reg_name(operand.reg))
        if operand.type==CS_OP_MEM:
            address = self.address(ins,operand)
            return int.from_bytes(self.memory[address:address+operand.size],'little')
        raise ValueError('Unsupported operand')

    def write(self,ins,operand,value):
        value &= (1<<(8*operand.size))-1
        if operand.type==CS_OP_REG:
            self.reg(ins.reg_name(operand.reg),value)
        elif operand.type==CS_OP_MEM:
            address = self.address(ins,operand)
            self.memory[address:address+operand.size] = value.to_bytes(operand.size,'little')
        else:
            raise ValueError('Invalid destination')

    def arithmetic(self,kind,a,b,bits):
        mask = (1<<bits)-1
        if kind in ('sub','cmp','dec','neg'):
            result = a-b
            self.flags['c'] = a<b
            self.flags['o'] = bool(((a^b)&(a^result))&(1<<(bits-1)))
        elif kind in ('add','inc'):
            result = a+b
            self.flags['c'] = result>mask
            self.flags['o'] = bool((~(a^b)&(a^result))&(1<<(bits-1)))
        else:
            result = {'and':lambda:a&b,'test':lambda:a&b,'or':lambda:a|b,'xor':lambda:a^b}[kind]()
            self.flags['c'] = self.flags['o'] = False
        result &= mask
        self.flags['z'],self.flags['s'] = result==0,bool(result&(1<<(bits-1)))
        return result

    def event(self,midi):
        self.reg('ax',midi['status'])
        data = midi['data']+[0,0]
        self.reg('bx',(data[0]<<8)|data[1])
        ip,stack,steps,writes = 0x58f1,[],0,[]
        self.timeline = []
        while ip!=0x599f:
            if steps>10000:
                raise ValueError('Driver exceeded bounded instruction limit')
            if ip==0x579e:
                self.timeline.append(('opl',ip))
                writes.append([self.reg('al'),self.reg('ah')])
                # Native entry/return observations exclude RET. Its one cycle
                # belongs to the non-OPL cost being counted here.
                ip = stack.pop()
                steps += 1
                continue
            if ip not in self.cache:
                self.cache[ip] = next(self.decoder.disasm(self.code[ip:ip+16],ip,count=1))
            ins = self.cache[ip]
            op,args = ins.mnemonic,ins.operands
            self.timeline.append((op,ip))
            next_ip = (ip+ins.size)&65535
            values = [self.read(ins,a) for a in args]
            steps += 1
            if op=='mov': self.write(ins,args[0],values[1])
            elif op=='xchg':
                self.write(ins,args[0],values[1]);self.write(ins,args[1],values[0])
            elif op in ('cmp','test','add','sub','and','or','xor'):
                value = self.arithmetic(op,*values,args[0].size*8)
                if op not in ('cmp','test'):self.write(ins,args[0],value)
            elif op in ('inc','dec','neg'):
                carry = self.flags['c']
                a,b = (0,values[0]) if op=='neg' else (values[0],1)
                self.write(ins,args[0],self.arithmetic(op,a,b,args[0].size*8))
                if op!='neg':self.flags['c'] = carry
            elif op in ('shr','shl'):
                value,count = values
                self.write(ins,args[0],value>>count if op=='shr' else value<<count)
                if count:
                    self.flags['c'] = bool((value>>(count-1 if op=='shr' else args[0].size*8-count))&1)
            elif op=='push':stack.append(values[0])
            elif op=='pop':self.write(ins,args[0],stack.pop())
            elif op=='call':stack.append(next_ip);next_ip=values[0]
            elif op=='ret':next_ip=stack.pop()
            elif op in ('lodsb','lodsw'):
                size = 1 if op=='lodsb' else 2
                offset = self.reg('si')
                self.reg('al' if size==1 else 'ax',int.from_bytes(self.memory[offset:offset+size],'little'))
                self.reg('si',offset+size)
            elif op=='mul':
                value = self.reg('al' if args[0].size==1 else 'ax')*values[0]
                self.reg('ax',value)
                if args[0].size==2:self.reg('dx',value>>16)
            elif op=='div':
                value = (self.reg('dx')<<16)|self.reg('ax')
                quotient,remainder = divmod(value,values[0])
                if quotient>65535:raise ValueError('Driver divide overflow')
                self.reg('ax',quotient);self.reg('dx',remainder)
            elif op=='clc':self.flags['c']=False
            elif op=='nop':pass
            elif op=='loop':
                self.reg('cx',self.reg('cx')-1)
                if self.reg('cx'):next_ip=values[0]
            elif op in ('jmp','je','jne','jb','jbe','ja','jae','jcxz'):
                f=self.flags
                branch = {'jmp':True,'je':f['z'],'jne':not f['z'],'jb':f['c'],
                          'jbe':f['c'] or f['z'],'ja':not(f['c'] or f['z']),
                          'jae':not f['c'],'jcxz':self.reg('cx')==0}[op]
                if branch:next_ip=values[0]
            else:
                raise ValueError(f'Unsupported driver instruction {ip:04x}: {ins.mnemonic} {ins.op_str}')
            ip=next_ip
        if stack:raise ValueError('Unbalanced driver stack')
        return writes,steps
