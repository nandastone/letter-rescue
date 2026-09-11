"""Continuous original idle loop and IRQ0 delivery from one hardware checkpoint.

This models ordinary gameplay while waiting for the timer gate, including IRQ0
and IRQ1 delivery. Menu/joystick branches, rendering, typematic repeats and
derivation of frontend input delivery times remain explicit boundaries.
"""
import copy

from wr1_hardware_reference import Hardware,run_driver
from wr1_irq_work import IrqWork,STATE_FIELDS
from wr1_music_reference import Music
from wr1_opl_reference import Opl
from wr1_keyboard_work import KeyboardWork

COMPARE_FLAGS = {0x34ba:'0178',0x3580:'019a',0x3598:'01a0',0x35ab:'01b2',
                 0x35d3:'01b0',0x35f4:'018c',0x363a:'0198',0x3657:'01ae',
                 0x366a:'01a4',0x3671:'01a6',0x36d2:'01ac',0x3727:'0146'}
IDLE_NODES = set(COMPARE_FLAGS)|{0x34bf,0x34c1,0x3585,0x359d,0x35b0,0x35d8,
    0x35f9,0x363f,0x365c,0x366f,0x3676,0x36d7,0x371b,0x371e,0x3722,0x3724,
    0x372c,0x379f,0x37a1,0x40d2}


class IdleClock:
    def __init__(self,catalogue,tables,cmf,initial,names):
        self.instructions = catalogue['main_instructions']
        self.irq_instructions = catalogue['irq_instructions']
        self.base = catalogue['main_file_base']
        self.pc = self.base+initial['cpu_ip']
        self.cs = initial['cpu_cs']
        self.ax = initial['cpu_ax']
        self.flags = {'c':bool(initial['cpu_flags']&1),'z':bool(initial['cpu_flags']&64)}
        if not initial['cpu_flags']&512:raise ValueError('Idle checkpoint requires interrupts enabled')
        self.hardware = Hardware(initial,names)
        self.game = copy.deepcopy(initial['clock_state'])
        driver = initial['music_driver']
        self.music = Music(cmf,driver)
        self.opl = Opl(tables,cmf,driver['opl_state'])
        self.irq = IrqWork(catalogue,len(tables['rhythm_registers']),driver['dispatcher_use_dx'],driver['external_timer'])
        self.keyboard_work = KeyboardWork(catalogue)
        self.keyboard_game = copy.deepcopy(initial.get('keyboard_game'))
        self.keyboard_entries = []
        self.entries = []
        self.fast_loops = 0
        # Derive the ordinary idle-loop length from the same source metadata.
        saved = self.pc,self.ax,self.flags.copy(),self.game
        self.game = copy.deepcopy(self.game)
        self.pc,self.game['timer'],self.game['threshold'] = 0x34ba,0,1
        self.game['control_flags'] = dict.fromkeys(COMPARE_FLAGS.values(),0)
        self.loop_cost = 0
        while True:
            self.instruction()
            self.loop_cost += 1
            if self.pc==0x34ba:break
            if self.loop_cost>100:raise ValueError('Ordinary idle loop did not close')
        self.pc,self.ax,self.flags,self.game = saved

    def instruction(self):
        pc = self.pc
        if pc not in IDLE_NODES:raise NotImplementedError(f'Outside ordinary idle path at file {pc:05x}')
        op,next_pc,target = self.instructions[str(pc)]
        if pc in COMPARE_FLAGS:
            value = self.game['control_flags'][COMPARE_FLAGS[pc]]&65535
            self.flags.update(c=False,z=value==0)
        elif pc==0x371b:self.ax=self.game['timer']&65535
        elif pc==0x371e:
            value = self.game['threshold']&65535
            self.flags.update(c=self.ax<value,z=self.ax==value)
        elif pc==0x379f:
            self.ax=0
            self.flags.update(c=False,z=True)
        elif pc==0x37a1:pass # Clears the frame's ancillary flag before admission.
        elif op in ('jmp','je','jne','jae'):
            taken = {'jmp':True,'je':self.flags['z'],'jne':not self.flags['z'],'jae':not self.flags['c']}[op]
            if taken:next_pc=target
        else:raise NotImplementedError(f'Unknown idle work at {pc:05x}')
        self.pc=next_pc
        return op

    def interrupt(self):
        h,p = self.hardware,self.hardware.interrupts
        possible = p['irr']&~p['imr']&~p['isr']&((1<<p['active_irq'])-1)
        number = next((i for i in range(8) if possible&(1<<i)),None)
        if number==1:
            return self.keyboard_interrupt()
        if number!=0:raise NotImplementedError(f'Pending unsupported interrupt {number}')
        p['irr'] &= ~1
        p['isr'] |= 1
        p['active_irq'],p['irq_check'] = 0,0
        prologue=[]
        ip=0x224
        while ip<0x232:
            op,following=self.irq_instructions[str(ip)]
            prologue.append((op,ip));ip=following
        run_driver(h,prologue)
        self.entries.append({'hardware':h.snapshot(),'pic_cycle':round(h.observed_time()*27000),
                             'return_ip':self.pc-self.base,'return_cs':self.cs,
                             'return_c':self.flags['c'],'return_z':self.flags['z']})
        initial=copy.deepcopy(self.game)
        index=initial['speaker_index']
        if index>=0:
            initial['speaker_entry']=initial['speaker_sequence'][index]
            initial['speaker_next']=initial['speaker_sequence'][index+1]
        else:initial['speaker_entry']=initial['speaker_next']=[0,0]
        path,_,state=self.irq.body(self.music,self.opl,initial)
        run_driver(h,path)
        self.game.update(state)
        run_driver(h,[('iret',0x313)])

    def keyboard_interrupt(self):
        if self.keyboard_game is None:raise ValueError('IRQ1 requires initial game keyboard state')
        h,p=self.hardware,self.hardware.interrupts
        p['irr'] &= ~2
        p['isr'] |= 2
        p['active_irq'],p['irq_check']=1,0
        self.keyboard_work.path=[]
        self.keyboard_work.span(0xc714,0xc720)
        run_driver(h,self.keyboard_work.path)
        self.keyboard_entries.append({'hardware':h.snapshot(),'pic_cycle':round(h.observed_time()*27000),
                                      'return_ip':self.pc-self.base,'return_cs':self.cs,
                                      'return_c':self.flags['c'],'return_z':self.flags['z']})
        path,self.keyboard_game=self.keyboard_work.body(self.keyboard_game,h.keyboard['port60'])
        run_driver(h,path)
        for key in self.game['control_flags']:
            if key in self.keyboard_game['flags']:
                self.game['control_flags'][key]=self.keyboard_game['flags'][key]
        run_driver(h,[('iret',0xc95f)])

    def until_admission(self,max_blocks=2000000,input_events=()):
        """Predict the gate with optional externally timed, changed key inputs.

        Input times are part of the replay contract, not inferred IRQ times.
        This bounded experiment supports delivery between idle CPU blocks.
        """
        h=self.hardware
        blocks=0
        events=iter(input_events)
        event=next(events,None)
        while self.pc!=0x37a4:
            if not h.pending:
                cycle=round(h.observed_time()*27000)
                while event is not None and event['cycle']<=cycle:
                    if event['cycle']!=cycle:
                        raise NotImplementedError('External input did not fall on an idle CPU block boundary')
                    h.keyboard_key(event['key'],event['scan'],event['pressed'],event['extended'])
                    event=next(events,None)
                h.begin_block()
                if h.interrupts['irq_check']:
                    self.interrupt()
                    continue
                # No state or hardware changes inside complete ordinary loops.
                # Stop short of exhausting the budget so its final partial
                # loop retains the native block that admits the hardware event.
                if self.pc==0x34ba and (self.game['timer']&65535)<(self.game['threshold']&65535) and not any(self.game['control_flags'].values()):
                    loops=(h.cycles-1)//self.loop_cost
                    if loops>0:
                        h.cycles-=loops*self.loop_cost
                        self.ax=self.game['timer']&65535
                        self.flags.update(c=True,z=False)
                        self.fast_loops+=loops
            op=self.instruction()
            h.pending+=1
            if op.startswith('j') or h.pending==32:
                h.end_block(h.pending)
                h.pending=0
                blocks+=1
                if blocks>max_blocks:raise ValueError('Idle simulation did not reach admission')
        if event is not None:raise ValueError('Input plan extends beyond this idle wait')
        return round(h.observed_time()*27000)
