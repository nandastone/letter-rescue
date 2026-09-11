"""Original GX text work for the initialized 8-pixel-wide EGA font path."""
from wr1_graphics_work import GraphicsWork


def word(data,offset):
    return int.from_bytes(bytes(data[offset:offset+2]),'little')


class TextWork(GraphicsWork):
    def font(self,initial):
        """Select the existing BIOS 8x8 font and its transparency mode."""
        self.path=[]
        state=list(initial['graphics_state'])
        font=dict(initial['text_state'])
        transparent,font_id=[x&65535 for x in initial['args']]
        if font_id!=3:raise NotImplementedError('Other original font sizes')
        self.span(0x10296,0x102ae)
        self.span(0x102c1,0x102d0)
        if transparent!=1:self.span(0x102d2,0x102d2)
        self.span(0x102d5,0x102e9)
        fixed=initial['device_handle']<=1
        if not fixed:
            self.span(0x102eb,0x102f0)
            fixed=initial['device_handle']==9
        if fixed:
            self.span(0x10323,0x10329)
            font['font_pointer']=0xf000fa6e
        else:
            # WR1 does not replace this BIOS ROM font between these calls.
            # Its known current font-3 pointer supplies the return value;
            # changing from an unknown font requires a BIOS font checkpoint.
            if font['font_id']!=3 or font['height']!=8:
                raise NotImplementedError('Unknown initial BIOS 8x8 font pointer')
            flags=initial['graphics_flags'];code=flags['video_code']
            if code[:2]!=[0xfe,0x38] or code[4]!=0xcf:raise NotImplementedError('Unknown font-info BIOS callback')
            self.span(0x102f2,0x102fc)
            vector=flags['video_handler'];base=((vector>>16)<<4)+(vector&65535)
            self.path.extend([('callback',base),('iret',base+4)])
            self.span(0x102fe,0x1030d)
        self.span(0x1032f,0x1033d)
        state[0x50:0x52]=font_id.to_bytes(2,'little')
        state[0x52:0x54]=int(transparent==1).to_bytes(2,'little')
        font.update(font_id=font_id,height=8)
        return self.path,state,font

    def style(self,kind,initial):
        self.path=[]
        state=list(initial['graphics_state'])
        if kind=='text_color':start,end,offset=0xf6c8,0xf6ee,0x0e
        elif kind=='text_background':start,end,offset=0xf715,0xf73b,0x0c
        else:raise ValueError('Unknown text style')
        self.span(start,end)
        state[offset:offset+2]=(initial['args'][0]&65535).to_bytes(2,'little')
        return self.path,state

    def cursor(self,initial):
        self.path=[]
        state=list(initial['graphics_state'])
        self.span(0xdb86,0xdb9c)
        if word(state,0x3c)==1:raise NotImplementedError('Transformed text cursor')
        self.span(0xdbb4,0xdbce)
        for offset,value in [(0x12,initial['args'][1]),(0x14,initial['args'][0])]:
            state[offset:offset+2]=(value&65535).to_bytes(2,'little')
        return self.path,state

    def length(self,initial):
        self.path=[]
        data=initial['text_bytes']
        if not data or data[-1]!=0 or 0 in data[:-1]:raise ValueError('Require a complete NUL-terminated string')
        self.span(0x22460,0x2246b)
        self.path.append((f'scas:{len(data)}',0x2246e))
        self.span(0x22470,0x22479)
        return self.path,len(data)-1

    def string(self,initial):
        self.path=[]
        state=list(initial['graphics_state'])
        font=initial['text_state']
        data=initial['text_bytes']
        if not data or data[-1]!=0 or 0 in data[:-1] or len(data)>128:
            raise ValueError('Require a complete string fitting the original scan limit')
        if len(state)<88:raise ValueError('Text work requires the complete GX state')
        if font['ready']!=1 or word(state,0x50)!=font['font_id']:
            raise NotImplementedError('Text font initialization/change')
        self.span(0x103d3,0x103fe)
        for _ in data:self.span(0x10401,0x10406)
        self.span(0x10408,0x1040e)
        self.span(0x10414,0x1041e)
        self.span(0x1042a,0x10472)
        self.path.append((f'scas:{len(data)}',0x10475))
        self.span(0x10477,0x10481)
        count=len(data)-1
        if not count:
            self.span(0x10483,0x10483)
        else:
            x=(word(state,0x12)+word(state,0x30))&65535
            self.span(0x10486,0x1048a)
            align=word(state,0x54)
            if align!=1:
                self.span(0x1048c,0x10496)
                if align==4:
                    self.span(0x10498,0x104a0);x=(x-8*count)&65535
                else:
                    self.span(0x104a2,0x104a9);x=(x-4*count)&65535
            self.span(0x104ac,0x104b0)
            align=word(state,0x56)
            if align!=1:
                self.span(0x104b2,0x104b9)
                self.span(0x104bb,0x104c3) if align==4 else self.span(0x104c5,0x104cc)
            self.span(0x104cf,0x104d8)
            if word(state,0x18)==1:raise NotImplementedError('Clipped text work')
            self.span(0x1052f,0x10532)
            if word(state,0)==1:
                self.span(0x10534,0x1053a);mode=word(state,2)
            else:
                self.span(0x1053c,0x10546)
                mode=initial['fill_state']['mode']
                self.span(0x10548,0x1054b)
            if mode!=2 or word(initial['fill_state']['record'],8)!=0x552:
                raise NotImplementedError('Non-EGA text driver')
            self.span(0x10554,0x1055f)
            self.span(0x10567,0x10567)
            self.span(0x107b2,0x107bf)
            self.span(0x10739,0x1075c)
            self.span(0x107c2,0x107ee)
            shifted=x%8!=0
            transparent=word(state,0x52)==1
            height=font['height']
            if not 0<height<=32:raise NotImplementedError('Unsupported font height')
            for i in range(count):
                self.span(0x107f1,0x10804)
                if not shifted:
                    self.span(0x10806,0x10806)
                    for _ in range(height):
                        self.span(0x10808,0x10812)
                        if not transparent:self.span(0x10814,0x10817)
                        self.span(0x1081a,0x1081e)
                    self.span(0x10820,0x10820)
                else:
                    for _ in range(height):
                        self.span(0x10822,0x10837)
                        if not transparent:self.span(0x10839,0x1083e)
                        self.span(0x10841,0x1084f)
                        if not transparent:self.span(0x10851,0x10856)
                        self.span(0x1085a,0x1085f)
                self.span(0x10861,0x1086d)
                if i<count-1:self.span(0x1086f,0x1086f)
            self.span(0x10871,0x10888)
            self.span(0x1056a,0x10575)
            state[0x12:0x14]=((x+8*count)&65535).to_bytes(2,'little')
        self.span(0x10578,0x10586)
        return self.path,state
