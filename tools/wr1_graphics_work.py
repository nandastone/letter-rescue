"""Recovered original graphics-library work, using live device and call state."""


class GraphicsWork:
    def __init__(self,catalogue):
        self.instructions=catalogue['graphics_instructions']
        self.path=[]

    def span(self,start,end):
        while start<=end:
            op,following=self.instructions[str(start)]
            self.path.append((op,start))
            start=following

    def active_device(self,initial):
        if not 0<=initial['device_handle']<=40:raise NotImplementedError('Invalid graphics handle')
        self.span(0x1934e,0x19377)

    def resolve_device(self,initial):
        handle,slot=initial['device_handle'],initial['device_slot']
        record,descriptor=initial['device_record'],initial['device_descriptor']
        if not 0<=handle<=40 or not 0<=slot<44 or record[0]!=handle or record[2]!=descriptor[0]:
            raise NotImplementedError('Invalid graphics device lookup')
        self.span(0x1913a,0x1914f)
        self.span(0x19159,0x1915b)
        self.span(0x190ef,0x19104)
        self.span(0x1910e,0x19111)
        for i in range(slot+1):
            self.span(0x19114,0x19116)
            if i<slot:self.span(0x19118,0x1911b)
        self.span(0x19125,0x19137)
        self.span(0x1915e,0x1915e)
        self.span(0x19166,0x1917b)
        self.span(0x19185,0x19197)

    def draw_page(self,initial):
        """Select the next drawing page. Stops before the outer RETF 2."""
        self.path=[]
        page=initial['args'][0]&65535
        descriptor=initial['device_descriptor']
        if page&255>=descriptor[0x1f]:raise NotImplementedError('Invalid graphics page')
        self.span(0xf3f5,0xf404)
        self.active_device(initial)
        self.span(0xf409,0xf40b)
        self.span(0xf412,0xf413)
        self.resolve_device(initial)
        self.span(0xf418,0xf418)
        self.span(0xf421,0xf42c)
        self.span(0xf435,0xf452)
        state=list(initial['graphics_state'])
        stride=int.from_bytes(bytes(descriptor[0x22:0x24]),'little')
        state[8:10]=page.to_bytes(2,'little')
        state[10:12]=((page*stride)&65535).to_bytes(2,'little')
        return self.path,state

    def fill_style(self,initial):
        """Set fill pattern, color and transparency; stop before RETF 6."""
        self.path=[]
        transparent,color,pattern=[v&65535 for v in initial['args']]
        if not 0<=pattern<=11:raise NotImplementedError('Invalid fill pattern')
        self.span(0xf508,0xf539)
        if transparent!=1:self.span(0xf53b,0xf53b)
        self.span(0xf53e,0xf546)
        self.span(0xf54d,0xf556)
        state=list(initial['graphics_state'])
        for offset,value in [(0x22,pattern),(0x24,color),(0x26,int(transparent==1))]:
            state[offset:offset+2]=value.to_bytes(2,'little')
        return self.path,state

    def fill_raw(self,initial):
        """Solid EGA rectangle body, before RETF 8. Pixel contents do not branch."""
        self.path=[]
        state=bytes(initial['graphics_state'])
        word=lambda o:int.from_bytes(state[o:o+2],'little')
        signed=lambda v:((v+32768)&65535)-32768
        fill=initial['fill_state']
        if fill['ready']!=1 or word(0x3c)!=0 or word(0x18)==1:
            raise NotImplementedError('Fill initialization, transformed coordinates or clipping')
        if int.from_bytes(bytes(fill['record'][12:14]),'little')!=0x4ca:
            raise NotImplementedError('Non-EGA fill dispatch')
        ey,ex,sy,sx=[signed(v) for v in initial['args']]
        self.span(0xce38,0xce4c)
        self.span(0xce52,0xce59)
        self.span(0xce87,0xce8f)
        if word(0x30) or word(0x32):
            self.span(0xce91,0xce9d)
            sx=signed(sx+word(0x30));ex=signed(ex+word(0x30))
            sy=signed(sy+word(0x32));ey=signed(ey+word(0x32))
        self.span(0xcea0,0xcea4)
        self.span(0xcecc,0xced8)
        if ey<sy:
            self.span(0xceda,0xcee2)
            sy,ey=ey,sy
        self.span(0xcee5,0xceec)
        if word(0)==1:
            self.span(0xceee,0xcef4)
        else:
            if not 0<=fill['mode']<=16:raise NotImplementedError('Invalid fill mode')
            self.span(0xcef6,0xcf05)
        self.span(0xcf0e,0xcf1b)
        self.span(0xd2fa,0xd312)
        if ex<sx:
            self.span(0xd314,0xd31c)
            sx,ex=ex,sx
        if min(sx,sy)<0 or ex>=320 or ey>=200:raise NotImplementedError('Fill outside EGA screen')
        self.span(0xd31f,0xd326)
        self.span(0xd2d1,0xd2f9)
        self.span(0xd329,0xd359)
        count=ex//8-sx//8
        for row in range(ey-sy+1):
            self.span(0xd35b,0xd35f)
            repeats=count
            if sx%8:
                self.span(0xd361,0xd363)
                if count==0:
                    self.span(0xd365,0xd367)
                else:
                    self.span(0xd369,0xd36d)
                    repeats-=1
            if sx%8==0 or count!=0:
                self.span(0xd36e,0xd370)
                self.path.append((f'rep:{repeats}',0xd371))
            self.span(0xd373,0xd37c)
            if row<ey-sy:self.span(0xd37e,0xd383)
        self.span(0xd385,0xd39f)
        return self.path,[ey,ex,sy,sx]

    def fill_rect(self,initial):
        """Filled rectangle wrapper and its solid EGA child, before RETF 10."""
        from copy import deepcopy
        self.path=[]
        state=bytes(initial['graphics_state'])
        word=lambda o:int.from_bytes(state[o:o+2],'little')
        signed=lambda v:((v+32768)&65535)-32768
        mode,ey,ex,sy,sx=[signed(v) for v in initial['args']]
        if mode!=2 or word(0x3c)!=0 or word(0x22)!=0 or word(0x16)!=0:
            raise NotImplementedError('Outlined, transformed, patterned or non-copy fill')
        self.span(0xf174,0xf18a)
        self.span(0xf1b8,0xf1be)
        if ey<sy:
            self.span(0xf1c0,0xf1c3)
            sy,ey=ey,sy
        self.span(0xf1c6,0xf1cc)
        if ex<sx:
            self.span(0xf1ce,0xf1d1)
            sx,ex=ex,sx
        self.span(0xf1d4,0xf1e5)
        self.span(0xf2af,0xf2d3)
        opening=self.path
        child=deepcopy(initial)
        child['args']=[ey,ex,sy,sx]
        child['graphics_state'][0xe:0x10]=word(0x24).to_bytes(2,'little')
        body,_=self.fill_raw(child)
        self.path=opening+body
        self.span(0xd3a0,0xd3a0)
        self.span(0xf2d8,0xf2de)
        self.span(0xf3b1,0xf3cd)
        final=list(state)
        final[0x10:0x12]=[1,0]
        return self.path,final,[mode,ey,ex,sy,sx]

    def copy_rect(self,initial):
        """Aligned forward EGA copy work; stops before outer RETF 16.

        This predicts work and clipped arguments, not VRAM pixel contents.
        """
        self.path=[]
        descriptor=initial['device_descriptor']
        flags=initial['graphics_flags']
        if flags['copy_ready']!=1:
            raise NotImplementedError('Copy initialization')
        if descriptor[0]!=2 or descriptor[0x17]!=1 or descriptor[0x34:0x36]!=[0xc1,3]:
            raise NotImplementedError('Copy requires observed EGA descriptor')
        a=[v&65535 for v in initial['args']]
        page,dy,dx,source,ey,ex,sy,sx=a
        max_x=int.from_bytes(bytes(descriptor[24:26]),'little')-1
        max_y=int.from_bytes(bytes(descriptor[26:28]),'little')-1
        if sx>max_x or dx>max_x or sy>max_y or dy>max_y or ex<sx or ey<sy:
            raise NotImplementedError('Invalid copy rectangle')
        self.span(0x138d8,0x138ed)
        self.span(0x138f3,0x138f3)
        self.active_device(initial)
        self.span(0x138f8,0x138fd)
        self.span(0x13905,0x13906)
        self.resolve_device(initial)
        self.span(0x1390b,0x1390b)
        self.span(0x13915,0x1391e)
        if flags['check_mode']==1:
            self.span(0x13920,0x13924)
            if descriptor[0]!=9:
                self.span(0x13926,0x13926)
                self.video_mode(initial)
                if (flags['video_mode']&127)!=descriptor[0x16]:raise NotImplementedError('Mismatched graphics video mode')
                self.span(0x1392b,0x1392f)
        self.span(0x13939,0x1394a)
        self.span(0x13954,0x13957)
        if ex>max_x:
            self.span(0x13959,0x13959);ex=max_x
        self.span(0x1395c,0x1395f)
        self.span(0x13969,0x13974)
        right=ex-sx+dx
        if right>max_x:
            self.span(0x13976,0x13976);right=max_x
        ex=right-dx+sx
        width=ex-sx+1
        if sx%8 or dx%8 or width%8:raise NotImplementedError('Unaligned copy')
        self.span(0x13978,0x1399a)
        self.span(0x1399d,0x139ab)
        self.span(0x139b5,0x139b8)
        if ey>max_y:
            self.span(0x139ba,0x139ba);ey=max_y
        self.span(0x139bd,0x139c0)
        self.span(0x139ca,0x139d5)
        bottom=ey-sy+dy
        if bottom>max_y:
            self.span(0x139d7,0x139d7);bottom=max_y
        ey=bottom-dy+sy
        height=ey-sy+1
        self.span(0x139d9,0x13a08)
        self.span(0x13a0d,0x13a3b)
        if width==8:self.span(0x13a3d,0x13a45)
        self.span(0x13a4e,0x13a78)
        self.span(0x13a7d,0x13a9d)
        self.span(0x13aa2,0x13ab6)
        self.span(0x13ab9,0x13adc)
        self.span(0x13c91,0x13cb5)
        if source==page:
            for start,end,taken in [(0x13cb7,0x13cbd,sy>dy),(0x13cbf,0x13cc5,sx>right),
                                     (0x13cc7,0x13ccd,ex<dx),(0x13ccf,0x13cd5,sy>bottom),
                                     (0x13cd7,0x13cdd,ey<dy)]:
                self.span(start,end)
                if taken:break
            else:raise NotImplementedError('Overlapping EGA copy')
        self.span(0x13d06,0x13d17)
        self.span(0x163b6,0x163d8)
        self.span(0x13d1b,0x13d35)
        self.span(0x163b6,0x163d8)
        self.span(0x13d39,0x13d51)
        for row in range(height):
            self.span(0x13d52,0x13d52)
            self.path.append((f'rep:{width//8}',0x13d55))
            self.span(0x13d57,0x13d5e)
            if row<height-1:self.span(0x13d60,0x13d60)
        self.span(0x13d62,0x13d78)
        return self.path,[page,dy,dx,source,ey,ex,sy,sx]

    def video_mode(self,initial):
        flags=initial['graphics_flags']
        code=flags['video_code']
        if flags['display_type']==7 or code[:2]!=[0xfe,0x38] or code[4]!=0xcf:
            raise NotImplementedError('Unsupported BIOS video-mode handler')
        vector=flags['video_handler']
        base=((vector>>16)<<4)+(vector&65535)
        self.span(0x1919a,0x191ae)
        self.span(0x191c1,0x191c4)
        self.path.extend([('callback',base),('iret',base+4)])
        self.span(0x191c6,0x191d7)

    def masked_sprite(self,initial):
        """EGA masked drawing work from the image header; pixel bytes do not branch."""
        self.path=[]
        header=bytes(initial['image_header'])
        descriptor=bytes(initial['device_descriptor'])
        word=lambda b,o:int.from_bytes(b[o:o+2],'little')
        flags=initial['graphics_flags']
        if flags['sprite_ready']!=1 or descriptor[0]!=2 or word(descriptor,0x2a)!=0x316:
            raise NotImplementedError('Sprite initialization or different graphics device')
        if word(header,0)!=0xca00 or word(header,0x16)!=0 or not word(header,0x1a):
            raise NotImplementedError('Sprite requires an image in conventional memory')
        planes=header[0x12]
        if planes not in (1,4):raise NotImplementedError('Unsupported EGA plane count')
        page,y,x,operation,_,_= [v&65535 for v in initial['args']]
        width,height=word(header,0x2c),word(header,0x2e)
        count=word(header,0x30)
        mask=header[0x32]
        available_x,available_y=word(descriptor,24)-x,word(descriptor,26)-y
        if available_x<=0 or available_y<=0 or not width or not height:
            raise NotImplementedError('Sprite outside the drawable rectangle')
        self.span(0x164e2,0x164f6)
        self.span(0x164fc,0x1650f)
        # The caller requests the image's origin, so no data-dependent lookup.
        self.span(0x18c5a,0x18c71)
        self.span(0x18c8a,0x18c91)
        self.span(0x18c93,0x18c9a)
        self.span(0x18ca4,0x18ce0)
        self.span(0x18ce6,0x18ce6)
        self.span(0x18dbe,0x18dcb)
        self.span(0x16514,0x16516)
        self.span(0x1651e,0x1651e)
        self.active_device(initial)
        self.span(0x16523,0x16525)
        self.span(0x1652d,0x16531)
        self.resolve_device(initial)
        self.span(0x16536,0x16536)
        self.span(0x16540,0x16548)
        if flags['check_mode']==1:
            self.span(0x1654a,0x1654e)
            self.span(0x16550,0x16550)
            self.video_mode(initial)
            if (flags['video_mode']&127)!=descriptor[0x16]:raise NotImplementedError('Mismatched sprite video mode')
            self.span(0x16555,0x16559)
        self.span(0x16563,0x16576)
        self.span(0x1657f,0x16582)
        if available_x<width:
            self.span(0x16584,0x16593)
            count=(available_x+7)//8
            if available_x%8:self.span(0x16595,0x16595)
            self.span(0x16596,0x165a9)
            mask=(255<<((8-available_x%8)%8))&255
        self.span(0x165ac,0x165b9)
        self.span(0x165c2,0x165c5)
        if available_y<height:
            self.span(0x165c7,0x165c7);height=available_y
        self.span(0x165ca,0x165ea)
        self.span(0x167f6,0x16838)
        if planes!=1:self.span(0x1683a,0x1684c)
        self.span(0x16851,0x16861)
        self.span(0x163b6,0x163d8)
        self.span(0x16865,0x16883)
        shift=(8-x%8)%8
        if not shift and mask==255:
            for row in range(height):
                for plane in range(planes):
                    self.span(0x16885,0x16886)
                    for _ in range(count):self.span(0x16889,0x1688e)
                    self.span(0x16890,0x16898)
                    if planes!=1:
                        self.span(0x1689a,0x168a3)
                        if plane==planes-1:self.span(0x168a5,0x168a8)
                    if plane==planes-1:
                        self.span(0x168ab,0x168b1)
                        if row==height-1:
                            self.span(0x168b3,0x168b3);break
                    self.span(0x168b6,0x168bf)
        else:
            self.span(0x168c1,0x168cb)
            if count==1:self.span(0x168cd,0x168d1)
            self.span(0x168d3,0x168e0)
            for row in range(height):
                for plane in range(planes):
                    self.span(0x168e3,0x168f3)
                    if shift:self.span(0x168fa,0x16900)
                    else:
                        self.span(0x168f5,0x168f6)
                        if count==1:self.span(0x168f8,0x168f8)
                    if shift or count>1:
                        self.span(0x16901,0x1690c)
                        for _ in range(max(0,count-2)):self.span(0x1690e,0x16917)
                    self.span(0x16919,0x16943)
                    if plane==planes-1:
                        self.span(0x16945,0x16951)
                        if row==height-1:break
                    self.span(0x16953,0x1695c)
        self.span(0x1695e,0x16994)
        return self.path

    def display_page(self,initial):
        """Select an EGA display page, including BIOS CRTC/cursor port writes."""
        self.path=[]
        descriptor=initial['device_descriptor']
        flags=initial['graphics_flags']
        page=initial['args'][0]&65535
        if descriptor[0]!=2 or page>=min(8,descriptor[0x1f]):raise NotImplementedError('Unsupported display page/device')
        self.span(0x17606,0x17615)
        self.active_device(initial)
        self.span(0x1761a,0x1761c)
        self.span(0x17623,0x17624)
        self.resolve_device(initial)
        self.span(0x17629,0x17629)
        self.span(0x17632,0x17641)
        self.span(0x1764a,0x1764e)
        self.span(0x17668,0x17668)
        self.video_mode(initial)
        if (flags['video_mode']&127)!=descriptor[0x16]:raise NotImplementedError('Mismatched display mode')
        self.span(0x1766d,0x17671)
        self.span(0x1767a,0x17683)
        vector=flags['video_handler']
        base=((vector>>16)<<4)+(vector&65535)
        # INT10_SetActivePage writes four CRTC address bytes, then its cursor
        # helper writes four more. These are host IO calls inside one callback,
        # not eight additional guest instructions.
        self.path.extend([('video_page_callback',base),('iret',base+4)])
        self.span(0x17685,0x17694)
        state=dict(initial['display_state'])
        state.update(game_page=page,bios_page=page,bios_start=(page*state['page_size'])&65535)
        return self.path,state
