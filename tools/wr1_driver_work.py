"""Live-state reconstruction of the AdLib MIDI handler's instruction path.

Unlike DriverCPU this does not execute the binary, emulate registers, or decode
instructions. It follows recovered voice/controller decisions and expands their
static instruction spans. Call before Opl.event mutates the supplied voice state.
"""


class DriverWork:
    def __init__(self, catalogue, rhythm_writes):
        self.instructions = catalogue['instructions']
        self.rhythm_writes = rhythm_writes

    def span(self,start,end):
        while start<=end:
            op,following = self.instructions[str(start)]
            self.timeline.append((op,start))
            start = following

    def opl(self):
        self.timeline.append(('opl',0x579e))

    def instrument(self):
        for start,end in [(0x56d9,0x56fb),(0x56fe,0x570a),(0x570d,0x5719),
                          (0x571c,0x572d),(0x5730,0x573c),(0x573f,0x574b),
                          (0x574e,0x575a),(0x575d,0x5769),(0x576c,0x5778),
                          (0x577b,0x5787),(0x578a,0x5795)]:
            self.span(start,end)
            self.opl()
        self.span(0x5798,0x579d)

    def frequency(self):
        s,channel = self.state,self.channel
        self.span(0x5b55,0x5b94)
        bend = s['bends'][channel]
        if bend:
            self.span(0x5b96,0x5b9f)
            if bend>=128:self.span(0x5ba1,0x5ba1)
            self.span(0x5ba2,0x5baf)
            self.span(0x5bb1,0x5bb5) if bend==128 else self.span(0x5bb8,0x5bbc)
        self.span(0x5bbe,0x5bc8)
        self.opl()
        self.span(0x5bcb,0x5bdf)
        on = self.kind!=128
        if on:
            self.span(0x5be1,0x5be7)
            on = self.velocity!=0
            if on:
                self.span(0x5be9,0x5bef)
                if s['rhythm']&32:
                    self.span(0x5bf1,0x5bf7)
                    on = channel<11
        if on:self.span(0x5bf9,0x5bf9)
        self.span(0x5bfc,0x5c00)
        self.opl()
        self.span(0x5c03,0x5c26)
        if s['volumes'][channel]>=96:self.span(0x5c28,0x5c28)
        self.span(0x5c2a,0x5c50)
        self.opl()
        self.span(0x5c53,0x5c56)

    def note(self):
        s,channel = self.state,self.channel
        count = 9
        self.span(0x59f7,0x5a0c)
        if s['rhythm']&32:
            count = 6
            self.span(0x5a0e,0x5a1b)
            drum = s['percussion']==1 and channel==9
            if s['percussion']==1:self.span(0x5a1d,0x5a23)
            if drum:
                self.span(0x5a4b,0x5a66)
                self.opl()
                self.span(0x5a69,0x5a69)
                self.span(0x5b54,0x5b54)
                return
            self.span(0x5a25,0x5a2b)
            if channel>=11:
                self.span(0x5a2d,0x5a45)
                self.opl()
                self.span(0x5a48,0x5a48)
                self.span(0x5b54,0x5b54)
                return
        self.span(0x5a6c,0x5a72)
        if self.kind>128:self.span(0x5ab0,0x5ab6)
        if self.kind<=128 or self.velocity==0:
            self.span(0x5a74,0x5a7b)
            for voice in range(count):
                self.span(0x5a7e,0x5a89)
                if s['voices'][voice]>>8==channel:
                    self.span(0x5a91,0x5a9b)
                    if s['notes'][voice]==self.note_value:
                        self.span(0x5aa2,0x5aa7)
                        self.frequency()
                        self.span(0x5aaa,0x5aad)
                        self.span(0x5b54,0x5b54)
                        return
                    self.span(0x5a9d,0x5aa0)
                self.span(0x5a8b,0x5a8c)
            self.span(0x5a8e,0x5a8e)
            self.span(0x5b54,0x5b54)
            return
        # Native reuse can restart the channel scan after finding a busy
        # candidate in the unassigned pass. Preserve that path, not just its
        # eventual choice of voice: its work affects timer admission.
        voices = s['voices'].copy()
        for retry in range(2):
            self.span(0x5ab8,0x5aba)
            voice,phase,found = 0,0,False
            iterations = 0
            while True:
                iterations += 1
                if iterations>100:raise ValueError('Unbounded voice search')
                self.span(0x5abd,0x5ac3) if phase==0 else self.span(0x5ad2,0x5ad6)
                match = voices[voice]>>8==(channel if phase==0 else 255)
                if match:
                    self.span(0x5b00,0x5b0a)
                    if not s['notes'][voice]:
                        found = True
                        break
                    self.span(0x5b0c,0x5b12)
                    voice += 1
                    if voice<count:
                        phase = 0
                        continue
                    self.span(0x5b14,0x5b14)
                else:
                    self.span(0x5ac5,0x5acb) if phase==0 else self.span(0x5ad8,0x5ade)
                    voice += 1
                    if voice<count:continue
                    if phase==1:break
                self.span(0x5acd,0x5acf)
                voice,phase = 0,1
            if found:
                self.span(0x5b16,0x5b2f)
                if voices[voice]&255!=s['programs'][channel]:
                    self.span(0x5b31,0x5b4d)
                    self.instrument()
                self.span(0x5b50,0x5b50)
                self.frequency()
                self.span(0x5b53,0x5b53)
                return
            self.span(0x5ae0,0x5ae0)
            recycled = False
            for voice in range(count):
                self.span(0x5ae2,0x5ae8)
                if not s['notes'][voice]:
                    self.span(0x5af5,0x5afe)
                    voices[voice] = 65535
                    self.span(0x5ab0,0x5ab6)
                    recycled = True
                    break
                self.span(0x5aea,0x5af0)
            if not recycled:
                self.span(0x5af2,0x5af2)
                self.span(0x5b54,0x5b54)
                return
        raise ValueError('Voice recycling did not terminate')

    def control(self,controller,value):
        self.span(0x582d,0x5835)
        if controller==123:
            self.span(0x5837,0x5837)
            self.span(0x57c4,0x57ca)
            self.span(0x57e9,0x57ef)
            self.span(0x57f7,0x57fa)
            for voice in range(9):
                self.span(0x57fc,0x5808)
                if self.state['voices'][voice]>>8==self.channel:
                    self.span(0x580a,0x5810)
                    self.opl()
                    self.span(0x5813,0x5819)
                    self.opl()
                    self.span(0x581c,0x5823)
                self.span(0x5825,0x5829)
            self.span(0x582b,0x582c)
            self.span(0x583a,0x583a)
            self.span(0x58f0,0x58f0)
            return
        self.span(0x583d,0x5840)
        if controller==7:
            self.span(0x5842,0x584b)
        else:
            self.span(0x584e,0x5851)
            if controller==103:
                self.span(0x5853,0x5856)
                if value==0:
                    self.span(0x5860,0x586f)
                    self.opl()
                    self.span(0x5872,0x5884)
                else:
                    self.span(0x5858,0x585b)
                    if value==1:
                        self.span(0x5887,0x5896)
                        self.opl()
                        self.span(0x5899,0x58a8)
                        for _ in range(self.rhythm_writes):
                            self.span(0x58ab,0x58b1)
                            self.span(0x58b3,0x58b3)
                            self.opl()
                            self.span(0x58b6,0x58b6)
                        self.span(0x58ab,0x58b1)
                        self.span(0x58b8,0x58bb)
                        self.opl()
                        self.span(0x58be,0x58c1)
                        self.opl()
                        self.span(0x58c4,0x58ca)
                    else:self.span(0x585d,0x585d)
            else:
                self.span(0x58cd,0x58d0)
                if controller!=105:self.span(0x58d2,0x58d5)
                if controller in (104,105):
                    self.span(0x58da,0x58e9)
                    self.span(0x58ee,0x58ee)
                else:self.span(0x58d7,0x58d7)
        self.span(0x58f0,0x58f0)

    def event(self,midi,state):
        if state['mode']!=1:raise ValueError('Work model supports AdLib mode only')
        self.state,self.timeline = state,[]
        self.kind,self.channel = midi['status']&240,midi['status']&15
        data = midi['data']+[0,0]
        self.velocity,self.note_value = data[1],data[0]
        self.span(0x58f1,0x58f7)
        self.span(0x592b,0x594c)
        if self.kind>144:
            self.span(0x594e,0x5954)
            if self.kind<=176:
                self.span(0x5956,0x5956)
                self.control(data[0],data[1])
                self.span(0x5959,0x5959)
            else:
                self.span(0x595c,0x5962)
                if self.kind<=192:
                    self.span(0x5964,0x5964)
                    self.span(0x5cc4,0x5ccd)
                    if state['rhythm']&32:self.span(0x5ccf,0x5cd5)
                    self.span(0x5cd7,0x5cea)
                    self.span(0x5967,0x5967)
        else:
            self.span(0x596a,0x5970)
            transpose = True
            if state['rhythm']&32:
                self.span(0x5972,0x5978)
                if state['percussion']==1:
                    self.span(0x597a,0x5980)
                    transpose = self.channel!=9
                    if transpose:self.span(0x5982,0x5982)
                else:
                    self.span(0x5985,0x598b)
                    transpose = self.channel<11
            if transpose:
                self.span(0x598d,0x5996)
                self.note_value = (self.note_value+state['transpose'])&255
            self.span(0x599a,0x599a)
            self.note()
        self.span(0x599d,0x599e)
        return self.timeline
