"""WR1 timer body, speaker sequencing and DOSBox BIOS chaining (before IRET).

Music/voice state remains continuous. This routine experiment receives current
game and speaker state at entry; the main loop may have changed that state.
"""
from wr1_music_work import MusicWork

STATE_FIELDS = ('timer','speaker_index','speaker_elapsed','bios_countdown','bios_reload','bios_ticks')


def signed16(value):
    return ((value+32768)&65535)-32768


class IrqWork:
    def __init__(self,catalogue,rhythm_writes,driver_mode,timer_mode):
        self.instructions = catalogue['irq_instructions']
        self.music_work = MusicWork(catalogue,rhythm_writes,driver_mode,timer_mode)

    def span(self,start,end):
        while start<=end:
            op,following = self.instructions[str(start)]
            if start==0x308:op='eoi'
            self.timeline.append((op,start))
            start = following

    def speaker(self,initial):
        s = self.state
        self.span(0x232,0x245)
        s['timer'] = signed16(s['timer']+1)
        s['speaker_elapsed'] = (s['speaker_elapsed']+1)&0xffffffff
        if s['speaker_index']<0:
            self.span(0x247,0x247)
            return
        self.span(0x24a,0x260)
        duration = initial['speaker_entry'][1]&65535
        high = 65535 if duration&32768 else 0
        if high>s['speaker_elapsed']>>16:
            self.span(0x262,0x262)
            return
        self.span(0x265,0x265)
        if high==s['speaker_elapsed']>>16:
            self.span(0x267,0x26b)
            if duration>(s['speaker_elapsed']&65535):
                self.span(0x26d,0x26d)
                return
        self.span(0x270,0x297)
        s['speaker_elapsed'] = 0
        s['speaker_index'] = signed16(s['speaker_index']+1)
        if initial['speaker_next'][1]==0:
            self.span(0x299,0x2a6)
            s['speaker_index'] = -1
        else:self.span(0x2a8,0x2d6)

    def bios(self,initial):
        # Native callback instruction IDs vary; verify the surrounding ROM
        # template installed by DOSBox's CB_IRQ0 / CB_IRET setup.
        code,user = initial['bios_code'],initial['int1c_code']
        if code[:3]!=[0xfb,0xfe,0x38] or code[5:]!=[0x1e,0x50,0x52,0xcd,0x1c,0xfa,0xb0,0x20,0xe6,0x20,0x5a,0x58,0x1f,0xcf]:
            raise ValueError('Unrecognized BIOS IRQ0 template')
        if user[:2]!=[0xfe,0x38] or user[4]!=0xcf:
            raise ValueError('Unrecognized INT 1Ch template')
        vector = initial['bios_handler']
        base = ((vector>>16)<<4)+(vector&65535)
        for op,offset in [('sti',0),('callback',1),('push',5),('push',6),('push',7),('int',8)]:
            self.timeline.append((op,base+offset))
        vector = initial['int1c_handler']
        user_base = ((vector>>16)<<4)+(vector&65535)
        self.timeline.extend([('callback',user_base),('iret',user_base+4)])
        for op,offset in [('cli',10),('mov',11),('eoi',13),('pop',15),('pop',16),('pop',17),('iret',18)]:
            self.timeline.append((op,base+offset))
        self.state['bios_ticks'] = (self.state['bios_ticks']+1)&0xffffffff
        if self.state['bios_ticks']>=0x1800b0:self.state['bios_ticks']=0

    def body(self,music,opl,initial):
        self.timeline = []
        self.state = {key:initial[key] for key in STATE_FIELDS}
        self.speaker(initial)
        path,writes = self.music_work.tick(music,opl)
        self.timeline.extend(path)
        self.span(0x2dc,0x2ef)
        self.state['bios_countdown'] = (self.state['bios_countdown']-1)&0xffffffff
        if self.state['bios_countdown']:
            self.span(0x306,0x308)
        else:
            self.state['bios_countdown'] = self.state['bios_reload']
            self.span(0x2f1,0x300)
            self.bios(initial)
            self.span(0x304,0x304)
        self.span(0x30a,0x312)
        return self.timeline,writes,self.state
