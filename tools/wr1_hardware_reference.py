"""WR1 OPL wait / PIT / VGA timing research model from DOSBox Pure source.

Initial state is observed once per independent experiment. Future hardware
events are scheduled by the model, not read from a recorded timeline.
"""
import copy
import math
import re
import struct


def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


def event_names(link_map):
    lines = link_map.splitlines()
    base = next(int(re.search(r'0x([0-9a-f]+)',line)[1],16) for line in lines if ' PIC_RunQueue()' in line)
    names = {}
    for i,line in enumerate(lines[:-1]):
        if not line.startswith(' .text$'):
            continue
        address = re.search(r'0x([0-9a-f]+)',lines[i+1])
        if not address:
            continue
        for name in ('PIT0_Event','VGA_DrawPart','VGA_VerticalTimer','VGA_VertInterrupt','VGA_DisplayStartLatch','VGA_PanningLatch','KEYBOARD_TransferBuffer'):
            if name in line:
                names[int(address[1],16)-base] = name
    return names


def run_driver(hardware,timeline):
    """Execute driver instruction work and independently simulated OPL waits."""
    count,waits = hardware.pending,[]
    decoded = count
    hardware.pending = 0
    for operation,_ in timeline:
        if operation.startswith('scas:'):
            # Dyn-x86 has no SCAS opcode implementation. Each compared byte
            # falls back through BR_Opcode with a normal-core budget of one:
            # the dynamic opcode costs one, then the string/outer-loop tests
            # leave CPU_Cycles=-2. The next byte starts a fresh dynamic block.
            remaining=int(operation.split(':')[1])
            if remaining<1:raise ValueError('SCAS work requires a compared byte')
            for _ in range(remaining):
                if not count:hardware.begin_block()
                hardware.end_block(count+1)
                hardware.left+=hardware.cycles
                hardware.cycles=-2
                count=decoded=0
                hardware.begin_block()
        elif operation.startswith('rep:'):
            if not count:hardware.begin_block()
            decoded += 1
            hardware.end_block(count+1)
            count = 0
            remaining = int(operation.split(':')[1])
            while remaining:
                hardware.cycles -= 1
                remaining -= 1
                if hardware.cycles<=0:
                    hardware.begin_block()
                    hardware.end_block(1) # Re-enter REP, even when CX became zero.
                    decoded = 1
            # The generated checked memory access invokes
            # dyn_check_bool_exception_al, which restores decode.cycles to 1
            # after dyn_string zeroed it. That cycle stays pending at the hook.
            count = 1
            if decoded==32:
                hardware.end_block(count)
                count = 0
                decoded = 0
        elif operation=='opl':
            if count:
                raise ValueError('OPL call must follow a completed CALL block')
            waits.append(hardware.opl())
            hardware.end_block(hardware.pending+1) # Pending POPs and RET.
            hardware.pending = 0
            decoded = 0
        else:
            if not count:
                hardware.begin_block()
            # Raw IO here is the speaker/PIT2 and PIC acknowledgement path.
            # AdLib access uses the explicit OPL primitive above.
            if operation=='keyboard_read':hardware.keyboard_read()
            elif operation=='video_page_callback':hardware.io_delay(8*19)
            elif operation=='in':hardware.io_delay(26)
            elif operation=='out':hardware.io_delay(19)
            elif operation=='eoi':
                hardware.io_delay(19)
                hardware.acknowledge_irq()
            count += 1
            decoded += 1
            if operation.startswith('j') or operation in ('ljmp','call','lcall','ret','retf','loop','int','iret','callback','video_page_callback') or decoded==32:
                hardware.end_block(count)
                count = 0
                decoded = 0
    hardware.pending = count
    # A return hook at the next instruction observes entry to the next block.
    # IRET can exhaust the last millisecond budget: PIC then discards its
    # overshoot before that hook, even when there is no more modeled work.
    if not count:hardware.begin_block()
    return waits


class Hardware:
    def __init__(self,initial,names):
        self.names = names
        self.ids = {name:key for key,name in names.items()}
        self.ticks = initial['pic_ticks']
        self.left = initial['cycle_left']
        self.cycles = initial['cycles_remaining']
        self.pit = copy.deepcopy(initial['pit'])
        self.queue = copy.deepcopy(initial['pic_queue'])
        self.vga = copy.deepcopy(initial['vga_timing'])
        self.pending = initial.get('pending_cycles',0)
        self.interrupts = copy.deepcopy(initial.get('pic_interrupts'))
        self.keyboard = copy.deepcopy(initial.get('keyboard'))
        if self.interrupts and (self.interrupts['special'] or self.interrupts['auto_eoi']):
            raise ValueError('Unsupported PIC priority mode')
        self.extra_polls = 0
        for p in self.pit:
            p['delay'] = f32(p['delay'])
            if p['mode']!=2 or p['bcd'] or p['new_mode'] or p['counterstatus_set']:
                raise ValueError('Unsupported PIT mode in observed WR1 interval')
        for event in self.queue:
            event['index'] = f32(event['index'])
            if event['id'] not in names:
                raise ValueError('Unmodeled hardware event')
        if self.vga['vblank_skip']:
            raise ValueError('Unmodeled VGA blanking skip')

    def time(self):
        return self.ticks+f32((27000-self.left-self.cycles)/27000)

    def observed_time(self):
        return self.time()+self.pending/27000

    def snapshot(self):
        result = dict(pit=self.pit,pic_queue=self.queue,vga_timing=self.vga,
                                  pic_ticks=self.ticks,cycle_left=self.left,
                                  cycles_remaining=self.cycles,pending_cycles=self.pending)
        if self.interrupts is not None:result['pic_interrupts']=self.interrupts
        if self.keyboard is not None:result['keyboard']=self.keyboard
        return copy.deepcopy(result)

    def activate_irq(self):
        self.interrupts['irq_check'] = 1
        self.left += self.cycles
        self.cycles = 0

    def raise_irq(self,number):
        p = self.interrupts
        if p is None:return # Legacy isolated OPL experiments omit PIC registers.
        bit = 1<<number
        if not p['irr']&bit:
            p['irr'] |= bit
            if not (p['imr']|p['isr'])&bit and number<p['active_irq']:
                self.activate_irq()

    def acknowledge_irq(self):
        p = self.interrupts
        if p is None:raise ValueError('IRQ acknowledgement requires initial PIC registers')
        if p['active_irq']==8:return
        p['isr'] &= ~(1<<p['active_irq'])
        p['active_irq'] = next((i for i in range(8) if p['isr']&(1<<i)),8)
        possible = p['irr']&~p['imr']&~p['isr']&255
        if possible:
            if possible&((1<<p['active_irq'])-1):self.activate_irq()
            else:p['irq_check']=0

    def add_event(self,name,delay,origin,value=0):
        event = dict(id=self.ids[name],index=f32(f32(delay)+origin),value=value)
        self.queue.append(event)
        # Python's stable sort matches insertion after equal-index queue entries.
        self.queue.sort(key=lambda e:e['index'])

    def keyboard_read(self):
        if self.keyboard is None:raise ValueError('Keyboard IO requires controller state')
        self.io_delay(26)
        self.keyboard['changed']=False
        if not self.keyboard['scheduled'] and self.keyboard['buffer']:
            self.keyboard['scheduled']=True
            index=f32((27000-self.left-self.cycles)/27000)
            self.add_event('KEYBOARD_TransferBuffer',.3,index)
            cycles=int(f32(f32(self.queue[0]['index']-index)*27000))
            if cycles<self.cycles:
                self.left+=self.cycles
                self.cycles=0
        return self.keyboard['port60']

    def keyboard_key(self,key,scan,pressed,extended=False):
        """Deliver one already changed key at the current external input boundary.

        key is the controller's key identity; scan is its set-1 make code.
        Frontend mapping and future delivery times are the caller's inputs.
        """
        k=self.keyboard
        if k is None:raise ValueError('Key delivery requires controller state')
        if pressed:
            k['repeat_wait']=k['repeat_rate'] if k['repeat_key']==key else k['repeat_pause']
            k['repeat_key']=key
        elif k['repeat_key']==key:
            k['repeat_key'],k['repeat_wait']=0,0
        for value in ([0xe0] if extended else [])+[scan|(0 if pressed else 128)]:
            if len(k['buffer'])>=32:continue
            k['buffer'].append(value)
            if not k['scheduled'] and not k['changed']:
                k['scheduled']=True
                index=f32((27000-self.left-self.cycles)/27000)
                self.add_event('KEYBOARD_TransferBuffer',.3,index)
                cycles=int(f32(f32(self.queue[0]['index']-index)*27000))
                if cycles<self.cycles:
                    self.left+=self.cycles
                    self.cycles=0

    def service(self,event):
        name,origin = self.names[event['id']],event['index']
        if name=='PIT0_Event':
            self.raise_irq(0)
            p = self.pit[0]
            p['start'] += p['delay']
            self.add_event(name,p['delay'],origin)
        elif name=='VGA_VerticalTimer':
            v = self.vga
            v['frame_start'] = self.time()
            self.add_event(name,v['vtotal'],origin)
            self.add_event('VGA_DisplayStartLatch',v['vrstart'],origin)
            self.add_event('VGA_PanningLatch',v['vrend'],origin)
            self.add_event('VGA_VertInterrupt',v['vdend']+.005,origin)
            v['parts_left'],v['lines_done'] = 4,0
            self.add_event('VGA_DrawPart',v['parts'],origin,v['parts_lines'])
        elif name=='VGA_DrawPart':
            v = self.vga
            v['lines_done'] += event['value']
            v['parts_left'] -= 1
            if v['parts_left']:
                lines = v['parts_lines'] if v['parts_left']!=1 else v['lines_total']-v['lines_done']
                self.add_event(name,v['parts'],origin,lines)
        elif name=='KEYBOARD_TransferBuffer':
            if self.keyboard is not None:
                self.keyboard['scheduled']=False
                if not self.keyboard['buffer']:return
                self.keyboard['port60']=self.keyboard['buffer'].pop(0)
                self.keyboard['changed']=True
            self.raise_irq(1)
        elif name not in ('VGA_VertInterrupt','VGA_DisplayStartLatch','VGA_PanningLatch'):
            raise ValueError('Unknown hardware callback')

    def begin_block(self):
        if self.cycles>0:
            return
        self.left += self.cycles
        self.cycles = 0
        if self.left<=0:
            # TIMER_AddTick discards overshoot from the last dynamic block.
            self.ticks += 1
            if self.keyboard is not None and self.keyboard['repeat_wait']:
                self.keyboard['repeat_wait']-=1
                if not self.keyboard['repeat_wait']:
                    raise NotImplementedError('Keyboard repeat injection requires frontend key state')
            self.left = 27000
            for event in self.queue:
                event['index'] = f32(event['index']-1)
        index = 27000-self.left
        while self.queue and f32(self.queue[0]['index']*27000)<=index:
            self.service(self.queue.pop(0))
        cycles = max(1,int(f32(f32(self.queue[0]['index']*27000)-index))) if self.queue else self.left
        self.cycles = min(cycles,self.left)
        self.left -= self.cycles

    def end_block(self,count):
        self.cycles -= count

    def io_delay(self,cycles):
        self.cycles -= min(cycles,self.cycles)

    def read_pit(self,channel):
        p = self.pit[channel]
        if p['go_read_latch']:
            p['go_read_latch'] = False
            index = math.fmod(self.time()-p['start'],p['delay'])
            p['read_latch'] = int(p['count']-(index/p['delay'])*p['count'])&65535
        state = p['read_state']
        if state==0:
            value = p['read_latch']>>8
            p['read_state'],p['go_read_latch'] = 3,True
        elif state==3:
            value = p['read_latch']&255
            p['read_state'] = 0
        elif state in (1,2):
            value = p['read_latch']&255 if state==1 else p['read_latch']>>8
            p['go_read_latch'] = True
        else:
            raise ValueError('Unsupported PIT read state')
        return value

    def read_word(self):
        self.io_delay(26)
        return self.read_pit(0)|(self.read_pit(1)<<8)

    def status(self):
        self.io_delay(26)
        self.io_delay(13)

    def opl(self):
        if self.pending:
            raise ValueError('Commit the preceding block before entering another OPL call')
        start = self.observed_time()
        self.extra_polls = 0
        self.begin_block()
        self.io_delay(19)
        self.status()
        self.end_block(9) # PUSH x4, MOV, OUT, MOV, IN, LOOP.
        for _ in range(99):
            self.begin_block()
            self.status()
            self.end_block(2)
        for iteration in range(30):
            self.begin_block()
            if iteration==0:
                self.io_delay(19)
            previous = self.read_word()
            current = self.read_word()
            self.end_block(9 if iteration==0 else 5)
            while current==previous:
                self.extra_polls += 1
                if self.extra_polls>1000:
                    raise ValueError('PIT poll failed to progress')
                self.begin_block()
                current = self.read_word()
                self.end_block(3)
            self.begin_block()
            self.end_block(1) # LOOP.
        self.begin_block()
        self.pending = 4 # Four POPs are pending at the native before-RET hook.
        return round((self.observed_time()-start)*27000)
