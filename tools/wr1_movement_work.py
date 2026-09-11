"""Original movement/animation/speaker work between admission and contacts.

Paths come from initial game state and attribute bytes, not a recorded path.
The modal recap and bottom-of-map paths are explicit boundaries.
"""
import copy
from wr1_graphics_work import GraphicsWork


def signed(value):
    return ((value+32768)&65535)-32768


class MovementWork(GraphicsWork):
    def __init__(self,catalogue):
        self.instructions=catalogue['movement_instructions']
        self.tables=catalogue['movement_tables']
        self.path=[]

    def attr(self,x,y):
        if not 0<=x<len(self.attributes) or not 0<=y<len(self.attributes[x]):
            raise NotImplementedError('Original movement read outside the captured attribute map')
        return self.attributes[x][y]

    def add(self,key,value):
        self.state[key]=signed(self.state[key]+value)

    def sound_is(self,offset):
        s=self.state
        return s['speaker_segment']==s['data_segment'] and s['speaker_offset']==offset

    def pose(self,index):
        facing=self.state['facing']
        if facing not in (0,1):raise NotImplementedError('Invalid movement facing')
        self.state['sprite']=self.tables['poses'][4*facing+index]

    def step(self,initial,attributes,admission_ax=0):
        if admission_ax!=0:raise ValueError('Ordinary admission must have AX=0')
        self.path=[]
        self.state=copy.deepcopy(initial)
        self.attributes=attributes
        s=self.state
        s.update(timer=0,previous_x=s['x'],previous_y=s['y'],support=0)
        self.span(0x37a4,0x37b8)
        if s['sprite']==9:
            self.span(0x37ba,0x37ba);s['sprite']=0
        self.span(0x37c0,0x37dc)
        support=self.attr(s['gx']+1,s['gy'])
        if support!=0x73:self.span(0x37de,0x37f0)
        if support in (0x73,0x74):
            s['support']=support
            self.span(0x37f2,0x3816)
            if s['speaker_segment']==s['data_segment']:self.span(0x3818,0x381a)
            stop=self.sound_is(0x4f6)
            if not stop:
                self.span(0x381c,0x382a)
                if s['speaker_segment']==s['data_segment']:self.span(0x382c,0x382e)
                stop=self.sound_is(0x526)
            if stop:
                self.span(0x3830,0x383a);s['speaker_index']=-1
            self.span(0x383c,0x3841)
            if s['recap_pending']:raise NotImplementedError('Modal recap interrupts movement')
        self.span(0x384b,0x3850)
        if s['up']:self.up()
        else:
            self.span(0x3852,0x3852)
            self.down()
        self.span(0x3af1,0x3afb)
        self.add('phase',1)
        if s['phase']>=17:
            self.span(0x3afd,0x3afd);s['phase']=16
        self.idle()
        self.horizontal()
        self.footstep_exit()
        return self.path,s

    def up(self):
        s=self.state
        s['idle_ticks']=0
        self.span(0x3855,0x385e)
        climbing=False
        if s['support']==0x74:
            self.span(0x3860,0x3878)
            climbing=self.attr(s['gx']+1,s['gy']-2)==0x74
        if not climbing:
            self.span(0x387a,0x3890)
            if self.attr(s['gx']+1,s['gy']-1)==0x74:
                self.span(0x3892,0x38aa)
                climbing=self.attr(s['gx']+1,s['gy']-3)==0x74
        if climbing:
            self.span(0x38ac,0x38b1)
            if s['sprite']==22:
                self.span(0x38b3,0x38b9);s['sprite']=23
            else:
                self.span(0x38bb,0x38bb);s['sprite']=22
            self.span(0x38c1,0x38d3)
            s.update(phase=0,speaker_index=-1)
        else:
            self.span(0x38d5,0x38d9)
            if s['support']:
                self.span(0x38db,0x38f9);self.pose(0);s['phase']=0
            else:
                self.span(0x38fb,0x3900)
                if s['phase']<9:
                    self.span(0x3902,0x391b);self.pose(1)
                else:
                    self.span(0x391d,0x3933);self.pose(3)
        self.span(0x3936,0x393b)
        if s['phase']<9:
            self.span(0x3940,0x3945)
            if s['speaker_index']<0:
                self.span(0x3947,0x394c)
                if s['sprite']<22:
                    self.span(0x394e,0x3953)
                    if s['phase']==0:
                        self.span(0x3955,0x395a)
                        if s['sound_mode']:
                            self.span(0x395c,0x3966)
                            s.update(speaker_segment=s['data_segment'],speaker_offset=0x4f6,speaker_index=0)
            self.span(0x396c,0x397b)
            self.add('y',-8);self.add('gy',-1)
            col=s['gx']
            while True:
                self.span(0x39b0,0x39b9)
                if not signed(s['gx']+3)>col:
                    self.span(0x39bb,0x39bb)
                    break
                self.span(0x397d,0x3993)
                if self.attr(col,s['gy']-4)==0x73:
                    self.span(0x3995,0x399f)
                    self.add('y',8)
                    if s['phase']<9:
                        self.span(0x39a4,0x39aa);s['phase']=16
                    else:self.span(0x39a1,0x39a1)
                    self.span(0x3aed,0x3aed);self.add('gy',1)
                    break
                self.span(0x39ad,0x39ad);col=signed(col+1)
        else:
            self.span(0x393d,0x393d)
            self.span(0x39be,0x39c3)
            self.span(0x39c8,0x39ea)
            self.add('y',8);self.add('gy',1);self.pose(3)

    def down(self):
        s=self.state
        self.span(0x39ed,0x39fb)
        if s['speaker_segment']==s['data_segment']:self.span(0x39fd,0x39ff)
        if self.sound_is(0x4f6):
            self.span(0x3a01,0x3a0b);s['speaker_index']=-1
        self.span(0x3a0d,0x3a11)
        if s['support']:
            self.span(0x3a13,0x3a18)
            if not s['down']:
                self.span(0x3a1a,0x3a1a);return
            self.span(0x3a1d,0x3a21)
            if s['support']!=0x74:
                self.span(0x3a23,0x3a23);return
        self.span(0x3a26,0x3a2a)
        climbing=s['support']==0x74
        if not climbing:
            self.span(0x3a2c,0x3a42)
            climbing=self.attr(s['gx']+1,s['gy']+1)==0x74
        if climbing:
            self.span(0x3a44,0x3a5a)
            climbing=self.attr(s['gx']+1,s['gy']-1)==0x74
            if not climbing:
                self.span(0x3a5c,0x3a74)
                climbing=self.attr(s['gx']+1,s['gy']-2)==0x74
        if climbing:
            self.span(0x3a76,0x3a7b)
            if s['sprite']==22:
                self.span(0x3a7d,0x3a83);s['sprite']=23
            else:
                self.span(0x3a85,0x3a8b);s['sprite']=22
        else:
            self.span(0x3a8d,0x3aa3);self.pose(3)
        self.span(0x3aa6,0x3abb)
        if self.attr(s['gx'],s['gy']-1)==0x73:
            self.span(0x3abd,0x3ac1);self.add('gx',1);self.add('x',8)
        self.span(0x3ac6,0x3add)
        if self.attr(s['gx']+2,s['gy']-1)==0x73:
            self.span(0x3adf,0x3ae3);self.add('gx',-1);self.add('x',-8)
        self.span(0x3ae8,0x3aed);self.add('y',8);self.add('gy',1)

    def idle(self):
        s=self.state
        for key,start,end,skip in [('left',0x3b03,0x3b08,0x3b0a),('right',0x3b0d,0x3b12,0x3b14),
                                   ('up',0x3b17,0x3b1c,0x3b1e),('down',0x3b21,0x3b26,0x3b28)]:
            self.span(start,end)
            if s[key]:
                self.span(skip,skip);return
        self.span(0x3b2b,0x3b34);self.add('idle_ticks',1)
        if s['idle_ticks']>17:
            self.span(0x3b36,0x3b3b)
            if s['sprite']<2:
                self.span(0x3b3d,0x3b4b);s['idle_ticks']=0;s['sprite']^=1
                return
            self.span(0x3b4e,0x3b53)
            if s['sprite']<22:
                self.span(0x3b55,0x3b60);s.update(sprite=0,idle_ticks=0)
                return
            self.span(0x3b63,0x3b68)
            if s['sprite']!=24:self.span(0x3b6a,0x3b6f)
            if s['sprite'] in (24,25):
                self.span(0x3b74,0x3b8d);self.pose(2)
            else:self.span(0x3b71,0x3b71)
            return
        self.span(0x3b90,0x3b96)
        if (s['sprite']&65535)<=25:
            self.span(0x3b98,0x3b9c)
            if s['sprite'] in (0,1,11,21,22,23):return
            if s['sprite'] in (10,25):
                self.span(0x3bd5,0x3bd9)
                if s['support']:
                    self.span(0x3bdb,0x3be1);s['sprite']=9
                return
            if s['sprite'] in (20,24):
                self.span(0x3be3,0x3be7)
                if s['support']:
                    self.span(0x3be9,0x3bef);s['sprite']=19
                return
        self.span(0x3bf1,0x3bf5)
        if s['left_index']>-1:
            self.span(0x3bf7,0x3c07);s.update(left_index=0,right_index=-1,sprite=12)
        else:
            self.span(0x3c09,0x3c0e);s.update(right_index=0,sprite=2)

    def horizontal(self):
        s=self.state
        self.span(0x3c14,0x3c19)
        if s['left']:
            self.span(0x3c1e,0x3c33)
            s['idle_ticks']=0;self.add('x',-8);self.add('gx',-1)
            row=signed(s['gy']-4)
            while True:
                self.span(0x3c53,0x3c57)
                if row>=s['gy']:break
                self.span(0x3c35,0x3c45)
                if self.attr(s['gx'],row)==0x73:
                    self.span(0x3c47,0x3c50);self.add('gx',1);self.add('x',8)
                    break
                self.span(0x3c52,0x3c52);row=signed(row+1)
            self.span(0x3c59,0x3c6d)
            s.update(facing=1,right_index=-1);self.add('left_index',1)
            if s['left_index']>7:
                self.span(0x3c6f,0x3c6f);s['left_index']=0
            self.span(0x3c74,0x3c7b)
            if s['previous_y']==s['y']:
                self.span(0x3c7d,0x3c82)
                if s['sprite']!=9:
                    self.span(0x3c84,0x3c8d)
                    if not 0<=s['left_index']<8:raise NotImplementedError('Invalid left animation index')
                    s['sprite']=self.tables['left_walk'][s['left_index']]
        else:self.span(0x3c1b,0x3c1b)
        self.span(0x3c90,0x3c95)
        if s['right']:
            self.span(0x3c9a,0x3caa)
            self.add('x',8);self.add('gx',1)
            row=signed(s['gy']-4)
            while True:
                self.span(0x3cca,0x3cce)
                if row>=s['gy']:break
                self.span(0x3cac,0x3cbe)
                if self.attr(s['gx']+2,row)==0x73:
                    self.span(0x3cc0,0x3cc4);self.add('gx',-1);self.add('x',-8)
                self.span(0x3cc9,0x3cc9);row=signed(row+1)
            self.span(0x3cd0,0x3ce9)
            s.update(idle_ticks=0,facing=0,left_index=-1);self.add('right_index',1)
            if s['right_index']>7:
                self.span(0x3ceb,0x3ceb);s['right_index']=0
            self.span(0x3cf0,0x3cf7)
            if s['previous_y']==s['y']:
                self.span(0x3cf9,0x3cfe)
                if s['sprite']!=9:
                    self.span(0x3d00,0x3d09)
                    if not 0<=s['right_index']<8:raise NotImplementedError('Invalid right animation index')
                    s['sprite']=self.tables['right_walk'][s['right_index']]
        else:self.span(0x3c97,0x3c97)

    def footstep_exit(self):
        s=self.state
        for frame,start,end in [(6,0x3d0c,0x3d11),(16,0x3d13,0x3d18),
                                 (3,0x3d1a,0x3d1f),(13,0x3d21,0x3d26)]:
            self.span(start,end)
            if s['sprite']==frame:break
        if s['sprite'] in (6,16,3,13):
            self.span(0x3d28,0x3d2d)
            if s['speaker_index']==-1:
                self.span(0x3d2f,0x3d34)
                if s['sound_mode']:
                    self.span(0x3d36,0x3d40)
                    s.update(speaker_segment=s['data_segment'],speaker_offset=0x4ea,speaker_index=0)
        self.span(0x3d46,0x3d4b)
        if s['door_state']:
            self.span(0x3d4d,0x3d54)
            at_door=s['gx']==s['door_x']
            if not at_door:
                self.span(0x3d56,0x3d5e)
                at_door=s['gx']==signed(s['door_x']-1)
            if at_door:
                self.span(0x3d60,0x3d6a)
                if s['gy']==signed(s['door_y']+5):
                    self.span(0x3d6c,0x3d6c);s['door_state']=2
        self.span(0x3d72,0x3d79)
        if s['gy']>=s['map_height']:raise NotImplementedError('Bottom-of-map death bypasses contacts')
