"""Renderer work selected from live state, starting at the original entry."""
from copy import deepcopy
from wr1_graphics_work import GraphicsWork
from wr1_text_work import TextWork


def signed(value):
    return ((value+32768)&65535)-32768


class RendererWork(GraphicsWork):
    def __init__(self,catalogue):
        super().__init__(catalogue)
        self.graphics=GraphicsWork(catalogue)
        self.text=TextWork(catalogue)

    def complete(self,initial,graphics,background,tiles,doors,matching,player,actors,images,tail):
        """Complete renderer before C1A9 RETF, including visible reward text."""
        _,state,gstate,calls,local,tile_state,door_state,actor_state=self.actors(initial,graphics,background,tiles,doors,matching,player,actors,images)
        result=deepcopy(tail)
        cx,cy=state['camera_x'],state['camera_y']
        page=local['page']
        x0,y0=cx//2,cy//2
        x1,y1=x0+(cx&1)+18,y0+10
        device=deepcopy(graphics)
        device['graphics_state']=gstate

        def child(kind,args,header=None,text_bytes=None):
            device['args']=args
            start=len(self.path)
            if kind=='masked_sprite':
                device['image_header']=images[str(header&65535)]
                work=self.graphics.masked_sprite(device)
                ret=0x16995
            elif kind=='copy_rect':
                work,_=self.graphics.copy_rect(device)
                ret=0x13d79
            elif kind=='text_font':
                work,device['graphics_state'],device['text_state']=self.text.font(device)
                ret=0x1033e
            elif kind=='text_background':
                work,device['graphics_state']=self.text.style(kind,device)
                ret=0xf73c
            elif kind=='text_cursor':
                work,device['graphics_state']=self.text.cursor(device)
                ret=0xdbcf
            elif kind=='text_string':
                device['text_bytes']=text_bytes
                work,device['graphics_state']=self.text.string(device)
                ret=0x10587
            else:
                work,device['graphics_state']=self.graphics.draw_page(device)
                ret=0xf453
            self.path.extend(work)
            calls.append({'kind':kind,'args':args,'start':start,'return':len(self.path)})
            self.span(ret,ret)

        def image(offset,x,y,operation):
            child('masked_sprite',[page,y,x,operation,signed(offset),actor_state['data_segment']],offset)

        def text_at(caption,x,y):
            self.span(0xa333,0xa33c)
            child('text_cursor',[signed(y),signed(x)])
            self.span(0xa341,0xa347)
            pointer=caption['pointer']
            child('text_string',[signed(pointer&65535),pointer>>16],text_bytes=caption['bytes'])
            self.span(0xa34c,0xa34d)

        def visible(branches):
            for start,end,jump,allowed in branches:
                self.span(start,end)
                if not allowed:
                    if jump is not None:self.span(jump,jump)
                    return False
            return True

        if result['foreground_count']!=len(result['foreground']):raise ValueError('Incomplete foreground')
        self.span(0xbc5e,0xbc60)
        for i in range(len(result['foreground'])+1):
            self.span(0xbd70,0xbd74)
            if i==len(result['foreground']):break
            self.span(0xbd76,0xbd76)
            x,y=result['foreground'][i]
            if visible([(0xbc63,0xbc6e,0xbc70,x>=x0),(0xbc73,0xbc7e,0xbc80,x<x1),
                        (0xbc83,0xbc8e,0xbc90,y>=y0),(0xbc93,0xbc9e,0xbca0,y<y1)]):
                self.span(0xbca3,0xbd6a)
                sx,sy=background['source_columns'][x][y]
                child('copy_rect',[page,y*16+32-cy*8,x*16+16-cx*8,3,sy+15,sx+15,sy,sx])
            self.span(0xbd6f,0xbd6f)
        self.span(0xbd79,0xbd81)
        result['action_busy']=0
        for i in range(len(actor_state['enemies'])+1):
            self.span(0xbf47,0xbf4b)
            if i==len(actor_state['enemies']):break
            self.span(0xbf4d,0xbf4d)
            enemy=actor_state['enemies'][i]
            mode=signed(enemy['state'])
            self.span(0xbd84,0xbd8d)
            if mode<0:
                self.span(0xbd8f,0xbd8f)
            else:
                self.span(0xbd92,0xbd9b)
                if mode>24:self.span(0xbd9d,0xbd9d)
                else:
                    self.span(0xbda0,0xbdd6)
                    x,y=(enemy['x']-cx)*8+16,(enemy['y']-cy)*8-55
                    corpse=mode==24
                    if corpse:self.span(0xbdd8,0xbdd8)
                    else:
                        self.span(0xbddb,0xbde0)
                        if result['death']:
                            self.span(0xbde2,0xbde2)
                            corpse=True
                    if corpse:
                        self.span(0xbf13,0xbf2c)
                        image(0xa206,x,y+64,1)
                        self.span(0xbf31,0xbf41)
                        image(0x8a13,x,y+64,2)
                    else:
                        self.span(0xbde5,0xbdfe)
                        result['action_busy']=1
                        frame=result['rescue_frames'][mode]
                        if frame>=0 and visible([(0xbe00,0xbe03,None,frame<24),(0xbe05,0xbe07,None,x>=0),
                                                (0xbe09,0xbe0d,None,x<288),(0xbe0f,0xbe13,None,y>=0),(0xbe15,0xbe19,None,y<104)]):
                            self.span(0xbe1b,0xbe2f)
                            image(0x9e86+128*frame,x,y,1)
                            self.span(0xbe34,0xbe4b)
                            image(0x8693+128*frame,x,y,2)
                        self.span(0xbe50,0xbe5f)
                        enemy['state']=mode+1
                        if mode+1==24:raise NotImplementedError('Rescue score update and text work')
                        self.span(0xbe61,0xbe61)
            self.span(0xbf46,0xbf46)
        self.span(0xbf50,0xbf55)
        if result['miss_timer']:
            self.span(0xbf57,0xbf7f)
            result['miss_timer']=(result['miss_timer']-1)&65535
            x,y=(result['miss_x']-cx)*8+16,(result['miss_y']-cy-8)*8+33
            if visible([(0xbf82,0xbf84,None,x>=0),(0xbf86,0xbf8a,None,x<288),
                        (0xbf8c,0xbf8e,None,y>=0),(0xbf90,0xbf93,None,y<104)]):
                self.span(0xbf95,0xbfa5)
                image(0xa286,x,y,1)
                self.span(0xbfaa,0xbfba)
                image(0x8a93,x,y,2)
        self.span(0xbfbf,0xbfc4)
        if result['reward_timer']==0:
            self.span(0xbfc6,0xbfc6)
        elif visible([(0xbfc9,0xbfd0,None,result['reward_x']>=cx),(0xbfd2,0xbfdc,None,cx+36>=result['reward_x']),
                      (0xbfde,0xbfe5,None,result['reward_y']>=cy),(0xbfe7,0xbff1,None,cy+19>=result['reward_y'])]):
            self.span(0xbffc,0xc004)
            child('text_font',[1,3])
            self.span(0xc009,0xc010)
            child('text_background',[page+13])
            self.span(0xc015,0xc018)
            child('draw_page',[page])
            self.span(0xc01d,0xc04b)
            rx,ry=result['reward_x'],result['reward_y']
            text_at(result['reward_text'],(rx-cx)*8+16,(ry-cy)*8+result['reward_timer']+32)
            self.span(0xc050,0xc058)
            if result['reward_bonus']==3:
                self.span(0xc05a,0xc064)
                if signed(rx-3)>=cx:
                    self.span(0xc066,0xc075)
                    if signed(rx+3)<=signed(cx+36):
                        self.span(0xc077,0xc0a2)
                        text_at(result['perfect_text'],(rx-cx)*8-4,(ry-cy)*8+result['reward_timer']+24)
                        self.span(0xc0a7,0xc0a7)
            self.span(0xc0aa,0xc0af)
            if result['reward_bonus']==1:
                self.span(0xc0b1,0xc0bb)
                if signed(rx-3)>=cx:
                    self.span(0xc0bd,0xc0cc)
                    if signed(rx+3)<=signed(cx+36):
                        self.span(0xc0ce,0xc0f9)
                        text_at(result['bonus_text'],(rx-cx)*8-4,(ry-cy)*8+result['reward_timer']+24)
                        self.span(0xc0fe,0xc0fe)
            self.span(0xc101,0xc10c)
            result['reward_timer']=(result['reward_timer']-1)&65535
            child('text_font',[0,3])
        else:
            self.span(0xbff3,0xbff9)
            result['reward_timer']=0
        for start,end,args in [(0xc111,0xc128,[page,0,0,5,31,319,0,0]),
                               (0xc12d,0xc14a,[page,32,0,5,199,15,32,0]),
                               (0xc14f,0xc16e,[page,32,304,5,199,319,32,304]),
                               (0xc173,0xc190,[page,184,0,5,199,319,184,0])]:
            self.span(start,end)
            child('copy_rect',args)
        self.span(0xc195,0xc19c)
        state['render_page']=page
        child('draw_page',[page])
        self.span(0xc1a1,0xc1a8)
        return self.path,state,device['graphics_state'],calls,local,tile_state,door_state,actor_state,result

    def actors(self,initial,graphics,background,tiles,doors,matching,player,actors,images):
        """Renderer through BC5E, including enemy animation and drip drawing."""
        _,state,gstate,calls,local,tile_state,door_state=self.player(initial,graphics,background,tiles,doors,matching,player)
        result=deepcopy(actors)
        if result['enemy_count']!=len(result['enemies']) or result['drip_count']!=len(result['drips']):
            raise ValueError('Incomplete actor arrays')
        cx,cy=state['camera_x'],state['camera_y']
        device=deepcopy(graphics)
        device['graphics_state']=gstate

        def image(offset,x,y,operation):
            offset&=65535
            args=[local['page'],y,x,operation,signed(offset),result['data_segment']]
            device['args']=args
            device['image_header']=images[str(offset)]
            start=len(self.path)
            self.path.extend(self.graphics.masked_sprite(device))
            calls.append({'kind':'masked_sprite','args':args,'start':start,'return':len(self.path)})
            self.span(0x16995,0x16995)

        def visible(branches):
            for start,end,jump,allowed in branches:
                self.span(start,end)
                if not allowed:
                    if jump is not None:self.span(jump,jump)
                    return False
            return True

        self.span(0xba38,0xba3a)
        for i in range(len(result['enemies'])+1):
            self.span(0xbb97,0xbb9b)
            if i==len(result['enemies']):break
            self.span(0xbb9d,0xbb9d)
            enemy=result['enemies'][i]
            x,y,mode=enemy['x'],enemy['y'],signed(enemy['state'])
            self.span(0xba3d,0xba46)
            if mode==24:
                self.span(0xba48,0xba48)
            elif visible([(0xba4b,0xba5c,0xba5e,x>cx-2),(0xba61,0xba72,0xba74,x<cx+35),
                          (0xba77,0xba88,0xba8a,y>cy-2),(0xba8d,0xba9e,0xbaa0,y<=cy+19)]):
                self.span(0xbaa3,0xbaf0)
                frame=result['animation_frames'][enemy['animation_index']]
                offset=enemy['type']*512+frame*128
                dx,dy=(x-cx)*8+16,(y-cy)*8+9
                if mode<24:
                    self.span(0xbaf2,0xbb14)
                    image(0xb98b+offset,dx,dy,1)
                    self.span(0xbb19,0xbb3b)
                    image(0xaf8c+offset,dx,dy,2)
                    self.span(0xbb40,0xbb49)
                    if mode==-1:
                        self.span(0xbb4b,0xbb5a)
                        enemy['animation_index']=(enemy['animation_index']+1)&65535
                        if signed(enemy['animation_index'])>11:
                            self.span(0xbb5c,0xbb66)
                            enemy['animation_index']=0
                else:
                    self.span(0xbb68,0xbb6d)
                    if state['render_page']==0:
                        self.span(0xbb6f,0xbb91)
                        image(0xb98b+offset,dx,dy,1)
            self.span(0xbb96,0xbb96)
        self.span(0xbba0,0xbba2)
        for i in range(len(result['drips'])+1):
            self.span(0xbc55,0xbc59)
            if i==len(result['drips']):break
            self.span(0xbc5b,0xbc5b)
            drip=result['drips'][i]
            x,y=drip['x'],drip['y']
            if visible([(0xbba5,0xbbb1,0xbbb3,x>cx),(0xbbb6,0xbbc7,0xbbc9,x<cx+36),
                        (0xbbcc,0xbbd8,None,y>cy),(0xbbda,0xbbeb,None,y<cy+19)]):
                self.span(0xbbed,0xbc2e)
                image(0xa986+drip['frame']*128,(x-cx)*8+16,(y-cy)*8+32,1)
                self.span(0xbc33,0xbc4f)
                image(0x8513+drip['frame']*128,(x-cx)*8+16,(y-cy)*8+32,2)
            self.span(0xbc54,0xbc54)
        return self.path,state,gstate,calls,local,tile_state,door_state,result

    def matching(self,initial,graphics,background,tiles,doors,matching):
        """Renderer through B9EC: available questions or selected word/pictures."""
        _,state,gstate,calls,local,tile_state,door_state=self.doors(initial,graphics,background,tiles,doors)
        device=deepcopy(graphics)
        device['graphics_state']=gstate
        offset_x,offset_y=16-8*state['camera_x'],32-8*state['camera_y']
        active=matching['active']!=0
        if len(matching['locations'])!=7:raise ValueError('Incomplete matching locations')

        def visible(checks):
            for start,end,jump,allowed in checks:
                self.span(start,end)
                if not allowed:
                    self.span(jump,jump)
                    return False
            return True

        def clipped(x,y,rect,width,height,blocks,page):
            # Source-X clipping, destination-X clamp, right clipping, then Y.
            conditions=[x>0,x>=0,320-max(0,x)-width>=0,y>0,y>=0,200-max(0,y)-height>=0]
            for block,condition in zip(blocks,conditions):
                a,b,t0,t1,f0,f1,z0,z1=block
                self.span(a,b)
                self.span(t0 if condition else f0,t1 if condition else f1)
                self.span(z0,z1)
            sx,sy,ex,ey=rect
            args=[local['page'],max(0,y),max(0,x),page,ey+min(0,200-max(0,y)-height),
                  ex+min(0,320-max(0,x)-width),sy-min(0,y),sx-min(0,x)]
            self.span(0xb886 if active else 0xb9c9,0xb89d if active else 0xb9de)
            device['args']=args
            start=len(self.path)
            work,_=self.graphics.copy_rect(device)
            self.path.extend(work)
            calls.append({'kind':'copy_rect','args':args,'start':start,'return':len(self.path)})
            self.span(0x13d79,0x13d79)

        question_blocks=[(0xb94c,0xb94e,0xb950,0xb952,0xb954,0xb954,0xb956,0xb95b),
                         (0xb95e,0xb960,0xb966,0xb966,0xb962,0xb964,0xb968,0xb968),
                         (0xb96a,0xb972,0xb97e,0xb97e,0xb974,0xb97c,0xb980,0xb983),
                         (0xb986,0xb98a,0xb98c,0xb98e,0xb990,0xb990,0xb993,0xb998),
                         (0xb99b,0xb99f,0xb9a5,0xb9a5,0xb9a1,0xb9a3,0xb9a8,0xb9a8),
                         (0xb9ab,0xb9b4,0xb9c1,0xb9c1,0xb9b6,0xb9bf,0xb9c3,0xb9c6)]
        word_blocks=[(0xb678,0xb67a,0xb67c,0xb67e,0xb680,0xb680,0xb682,0xb692),
                     (0xb695,0xb697,0xb69d,0xb69d,0xb699,0xb69b,0xb69f,0xb69f),
                     (0xb6a1,0xb6b6,0xb6c2,0xb6c2,0xb6b8,0xb6c0,0xb6c4,0xb6c7),
                     (0xb6ca,0xb6ce,0xb6d0,0xb6d2,0xb6d4,0xb6d4,0xb6d7,0xb6e7),
                     (0xb6ea,0xb6ee,0xb6f4,0xb6f4,0xb6f0,0xb6f2,0xb6f7,0xb6f7),
                     (0xb6fa,0xb710,0xb71d,0xb71d,0xb712,0xb71b,0xb71f,0xb725)]
        picture_blocks=[(0xb781,0xb7a5,0xb7a7,0xb7a9,0xb7ab,0xb7ab,0xb7ad,0xb7b2),
                        (0xb7b5,0xb7b7,0xb7bd,0xb7bd,0xb7b9,0xb7bb,0xb7bf,0xb7bf),
                        (0xb7c1,0xb7eb,0xb7f7,0xb7f7,0xb7ed,0xb7f5,0xb7f9,0xb7fc),
                        (0xb7ff,0xb825,0xb827,0xb829,0xb82b,0xb82b,0xb82e,0xb833),
                        (0xb836,0xb83a,0xb840,0xb840,0xb83c,0xb83e,0xb843,0xb843),
                        (0xb846,0xb871,0xb87e,0xb87e,0xb873,0xb87c,0xb880,0xb883)]
        self.span(0xb5f6,0xb5fb)
        if active:
            self.span(0xb600,0xb602)
        else:
            self.span(0xb5fd,0xb5fd)
            self.span(0xb8ae,0xb8b0)
        for i in range(8):
            self.span(0xb8a3 if active else 0xb9e4,0xb8a6 if active else 0xb9e7)
            if i==7:break
            self.span(0xb8a8 if active else 0xb9e9,0xb8a8 if active else 0xb9e9)
            wx,wy,attr=matching['locations'][i]
            gx,gy=int(signed(wx)/8),int(signed(wy)/8)
            x,y=signed(wx)+offset_x,signed(wy)+offset_y
            if active:
                self.span(0xb605,0xb62e)
                is_word=False
                if gx!=matching['source_x']:
                    self.span(0xb630,0xb630)
                else:
                    self.span(0xb633,0xb63a)
                    if gy!=matching['source_y']:self.span(0xb63c,0xb63c)
                    else:is_word=True
                if is_word:
                    shown=visible([(0xb63f,0xb65b,0xb65d,x>-64),(0xb660,0xb664,0xb666,x<320),
                                   (0xb669,0xb66b,0xb66d,y>0),(0xb670,0xb673,0xb675,y<192)])
                    if shown:clipped(x,y,matching['word_rects'][matching['active_index']],64,16,word_blocks,4)
                else:
                    self.span(0xb728,0xb745)
                    index=(attr+matching['picture_offset'])%7
                    shown=visible([(0xb748,0xb764,0xb766,x>-24),(0xb769,0xb76d,0xb76f,x<320),
                                   (0xb772,0xb774,0xb776,y>0),(0xb779,0xb77c,0xb77e,y<192)])
                    if shown:clipped(x,y,state['source_rects'][state['phases'][i]][index],24,24,picture_blocks,4)
            else:
                self.span(0xb8b3,0xb8e3)
                eligible=attr<7
                if not eligible:self.span(0xb8e5,0xb8e5)
                else:
                    self.span(0xb8e8,0xb8fa)
                    if gx==matching['last_x']:
                        self.span(0xb8fc,0xb90e)
                        if gy==matching['last_y']:
                            self.span(0xb910,0xb910)
                            eligible=False
                if eligible:
                    shown=visible([(0xb913,0xb92f,0xb931,x>-24),(0xb934,0xb938,0xb93a,x<320),
                                   (0xb93d,0xb93f,0xb941,y>0),(0xb944,0xb947,0xb949,y<192)])
                    if shown:clipped(x,y,[208,40,231,63],24,24,question_blocks,5)
            self.span(0xb8a2 if active else 0xb9e3,0xb8a2 if active else 0xb9e3)
        if active:self.span(0xb8ab,0xb8ab)
        return self.path,state,gstate,calls,local,tile_state,door_state

    def player(self,initial,graphics,background,tiles,doors,matching,player):
        """Renderer through BA38, after both player image passes."""
        _,state,gstate,calls,local,tile_state,door_state=self.matching(initial,graphics,background,tiles,doors,matching)
        self.span(0xb9ec,0xb9f1)
        if player['visible']:
            device=deepcopy(graphics)
            device['graphics_state']=gstate
            for i,im in enumerate(player['images']):
                self.span(0xb9f3 if i==0 else 0xba1c,0xba17 if i==0 else 0xba33)
                pointer=im['pointer']
                args=[local['page'],state['player_y']-32,state['player_x'],i+1,signed(pointer&65535),pointer>>16]
                device['args']=args
                device['image_header']=im['header']
                start=len(self.path)
                self.path.extend(self.graphics.masked_sprite(device))
                calls.append({'kind':'masked_sprite','args':args,'start':start,'return':len(self.path)})
                self.span(0x16995,0x16995)
        return self.path,state,gstate,calls,local,tile_state,door_state

    def doors(self,initial,graphics,background,tiles,doors):
        """Renderer through B5F6: clipped exit, entrance countdown and blink."""
        _,state,gstate,calls,local,tile_state=self.tiles(initial,graphics,background,tiles)
        result=deepcopy(doors)
        device=deepcopy(graphics)
        device['graphics_state']=gstate
        cx,cy=state['camera_x'],state['camera_y']

        def draw(x,y,entrance=False):
            if entrance:
                checks=[(0xb4cf,0xb4d9,0xb4db,cx-4<x),(0xb4de,0xb4e8,0xb4ea,cx+36>x),
                        (0xb4ed,0xb4f7,0xb4f9,cy-5<y),(0xb4fc,0xb506,0xb508,cy+19>y)]
                clips=[(0xb50b,0xb512,0xb514,0xb516,0xb518,0xb51b,0xb51f,0xb537),
                       (0xb53b,0xb548,0xb54a,0xb54c,0xb54e,0xb558,0xb55b,0xb564),
                       (0xb567,0xb56e,0xb570,0xb572,0xb574,0xb577,0xb57b,0xb5ac),
                       (0xb5ad,0xb5ba,0xb5bc,0xb5be,0xb5c0,0xb5ca,0xb5cd,0xb5f1)]
            else:
                checks=[(0xb38a,0xb394,0xb396,cx-4<x),(0xb399,0xb3a3,0xb3a5,cx+36>x),
                        (0xb3a8,0xb3b2,0xb3b4,cy-5<y),(0xb3b7,0xb3c1,0xb3c3,cy+19>y)]
                clips=[(0xb3c6,0xb3cd,0xb3cf,0xb3d1,0xb3d3,0xb3d6,0xb3da,0xb3f2),
                       (0xb3f6,0xb403,0xb405,0xb407,0xb409,0xb413,0xb416,0xb41f),
                       (0xb422,0xb429,0xb42b,0xb42d,0xb42f,0xb432,0xb436,0xb467),
                       (0xb468,0xb475,0xb477,0xb479,0xb47b,0xb485,0xb488,0xb4ac)]
            for start,end,jump,visible in checks:
                self.span(start,end)
                if not visible:
                    self.span(jump,jump)
                    return
            edges=[cx-x,cx+36-x-4,cy-y,cy+19-y-(5 if entrance else 4)]
            for i,(start,end,z0,z1,n0,n1,tail0,tail1) in enumerate(clips):
                self.span(start,end)
                zero=edges[i]<0 if i%2==0 else edges[i]>0
                self.span(z0 if zero else n0,z1 if zero else n1)
                self.span(tail0,tail1)
            left,top=max(0,edges[0])*8,max(0,edges[2])*8
            sx,sy=16+left,result['theme']*40+33+top
            ex,ey=47+min(0,edges[1])*8,result['theme']*40+72+min(0,edges[3])*8
            args=[local['page'],32+(y-cy)*8+top,16+(x-cx)*8+left,5,ey,ex,sy,sx]
            device['args']=args
            start=len(self.path)
            work,_=self.graphics.copy_rect(device)
            self.path.extend(work)
            calls.append({'kind':'copy_rect','args':args,'start':start,'return':len(self.path)})
            self.span(0x13d79,0x13d79)

        self.span(0xb368,0xb387)
        draw(result['exit_x'],result['exit_y'])
        self.span(0xb4b1,0xb4b6)
        if result['entrance_timer']==0:
            self.span(0xb4b8,0xb4b8)
        else:
            self.span(0xb4bb,0xb4c4)
            result['entrance_timer']=(result['entrance_timer']-1)&65535
            show=True
            if signed(result['entrance_timer'])<=10:
                self.span(0xb4c6,0xb4ca)
                if local['page']==0:
                    self.span(0xb4cc,0xb4cc)
                    show=False
            if show:draw(result['entrance_x'],result['entrance_y'],True)
        return self.path,state,gstate,calls,local,tile_state,result

    def tiles(self,initial,graphics,background,tiles):
        """Renderer entry through B368, including pickups and tile animation."""
        _,state,gstate,calls,local=self.background(initial,graphics,background)
        result=deepcopy(tiles)
        if len(result['pickups'])!=7 or result['animated_count']!=len(result['animated']):
            raise ValueError('Incomplete live tile state')
        device=deepcopy(graphics)
        device['graphics_state']=gstate
        cx,cy=state['camera_x'],state['camera_y']
        x0,y0=cx//2,cy//2
        x1,y1=x0+(cx&1)+18,y0+10

        def copy(args):
            device['args']=args
            start=len(self.path)
            work,_=self.graphics.copy_rect(device)
            self.path.extend(work)
            calls.append({'kind':'copy_rect','args':args,'start':start,'return':len(self.path)})
            self.span(0x13d79,0x13d79)

        self.span(0xb191,0xb193)
        for i in range(8):
            self.span(0xb21e,0xb221)
            if i==7:break
            self.span(0xb223,0xb223)
            x,y=map(signed,result['pickups'][i])
            self.span(0xb196,0xb1a1)
            visible=False
            if x<x0:
                self.span(0xb1a3,0xb1a3)
            else:
                self.span(0xb1a6,0xb1b1)
                if x<x1:
                    self.span(0xb1b3,0xb1be)
                    if y>=y0:
                        self.span(0xb1c0,0xb1cb)
                        visible=y<y1
            if visible:
                self.span(0xb1cd,0xb218)
                copy([local['page'],y*16+32-cy*8,x*16+16-cx*8,2,15,i*16+15,0,i*16])
            self.span(0xb21d,0xb21d)
        self.span(0xb226,0xb230)
        result['phase']=(result['phase']+1)&65535
        if signed(result['phase'])>3:
            self.span(0xb232,0xb232)
            result['phase']=0
        self.span(0xb238,0xb23a)
        for i in range(len(result['animated'])+1):
            self.span(0xb35f,0xb363)
            if i==len(result['animated']):break
            self.span(0xb365,0xb365)
            x,y=map(signed,result['animated'][i])
            visible=True
            for start,end,jump,allowed in [(0xb23d,0xb248,0xb24a,x>=x0),(0xb24d,0xb258,0xb25a,x<x1),
                                           (0xb25d,0xb268,0xb26a,y>=y0),(0xb26d,0xb278,0xb27a,y<y1)]:
                self.span(start,end)
                if not allowed:
                    self.span(jump,jump)
                    visible=False
                    break
            if visible:
                self.span(0xb27d,0xb359)
                sx,sy=background['source_columns'][x][y]
                sx+=16*result['phase']
                copy([local['page'],y*16+32-cy*8,x*16+16-cx*8,3,sy+15,sx+15,sy,sx])
            self.span(0xb35e,0xb35e)
        return self.path,state,gstate,calls,local,result

    def background(self,initial,graphics,background):
        """Generate entry through B191, including exposed tiles and cache copies."""
        _,state,gstate,calls,local=self.prefix(initial,graphics)
        device=deepcopy(graphics)
        device['graphics_state']=gstate
        page,dx,dy=local['page'],local['dx'],local['dy']
        cx,cy=state['camera_x'],state['camera_y']
        x0,y0=cx//2,cy//2
        x1,y1=x0+(cx&1)+18,y0+10
        px,py=16-(cx&1)*8,32-(cy&1)*8

        def child(kind,args):
            device['args']=args
            start=len(self.path)
            result=getattr(self.graphics,kind)(device)
            self.path.extend(result[0])
            calls.append({'kind':kind,'args':args,'start':start,'return':len(self.path)})
            if kind!='copy_rect':device['graphics_state']=result[1]
            ret={'copy_rect':0x13d79,'fill_style':0xf557,'fill_rect':0xf3ce}[kind]
            self.span(ret,ret)

        def tile(x,y,dest_x,dest_y,test_start,test_end,draw_start,draw_end):
            self.span(test_start,test_end)
            sx,sy=background['source_columns'][x][y]
            if signed(sx)>=0:
                self.span(draw_start,draw_end)
                child('copy_rect',[page,dest_y,dest_x,3,sy+15,sx+15,sy,sx])

        self.span(0xacc5,0xad39)
        if background['full_redraw']:
            raise NotImplementedError('Full background rebuild')
        self.span(0xad3b,0xad3b)
        self.span(0xae0e,0xae39)
        child('copy_rect',[page,32+dy,16+dx,2,183,303,32,16])
        self.span(0xae3e,0xae46)
        child('fill_style',[0,background['color'],0])
        self.span(0xae4b,0xae51)
        if dx==-8:
            self.span(0xae53,0xae53)
        else:
            self.span(0xae56,0xae59)
            if dx!=8:self.span(0xae5b,0xae5b)
        if dx==8:
            self.span(0xae5e,0xae72)
            child('fill_rect',[2,183,23,32,16])
            self.span(0xae77,0xae7d)
            for y in range(y0,y1+1):
                self.span(0xaf0b,0xaf11)
                if y==y1:break
                self.span(0xaf13,0xaf13)
                tile(x0,y,px,py+(y-y0)*16,0xae80,0xae96,0xae98,0xaeff)
                self.span(0xaf04,0xaf08)
            self.span(0xaf16,0xaf16)
        elif dx==-8:
            self.span(0xaf19,0xaf34)
            child('fill_rect',[2,183,303,32,296])
            self.span(0xaf39,0xaf43)
            for y in range(y0,y1+1):
                self.span(0xafcc,0xafd2)
                if y==y1:break
                self.span(0xafd4,0xafd4)
                tile(x1-1,y,288+(cx&1)*8,py+(y-y0)*16,0xaf46,0xaf5b,0xaf5d,0xafc0)
                self.span(0xafc5,0xafc9)
        self.span(0xafd7,0xafe3)
        if dy==-8:
            self.span(0xafe5,0xafe5)
        else:
            self.span(0xafe8,0xafeb)
            if dy!=8:self.span(0xafed,0xafed)
        if dy==8:
            self.span(0xaff0,0xb00d)
            child('fill_rect',[2,39,303,32,16])
            self.span(0xb012,0xb018)
            for x in range(x0,x1+1):
                self.span(0xb0a5,0xb0ab)
                if x==x1:break
                self.span(0xb0ad,0xb0ad)
                tile(x,y0,px+(x-x0)*16,py,0xb01b,0xb031,0xb033,0xb09a)
                self.span(0xb09f,0xb0a2)
            self.span(0xb0b0,0xb0b0)
        elif dy==-8:
            self.span(0xb0b3,0xb0d0)
            child('fill_rect',[2,183,303,176,16])
            self.span(0xb0d5,0xb0df)
            for x in range(x0,x1+1):
                self.span(0xb165,0xb168)
                if x==x1:break
                self.span(0xb16a,0xb16a)
                tile(x,y1-1,px+(x-x0)*16,168+(1^(cy&1))*8,0xb0e2,0xb0f7,0xb0f9,0xb15c)
                self.span(0xb161,0xb164)
        self.span(0xb16d,0xb18c)
        child('copy_rect',[2,32,16,page,183,303,32,16])
        return self.path,state,device['graphics_state'],calls,local

    def prefix(self,initial,graphics):
        """Stop before ACC5, after camera adjustment and drawing-page selection.

        Child boundaries are path indices for verification, never native timings.
        Unaligned animated HUD copies remain explicitly unsupported by CopyWork.
        """
        self.path=[]
        state=deepcopy(initial)
        device=deepcopy(graphics)
        calls=[]

        def child(kind,args):
            device['args']=args
            start=len(self.path)
            if kind=='copy_rect':
                work,_=self.graphics.copy_rect(device)
                ret=0x13d79
            else:
                work,device['graphics_state']=self.graphics.draw_page(device)
                ret=0xf453
            self.path.extend(work)
            calls.append({'kind':kind,'args':args,'start':start,'return':len(self.path)})
            self.span(ret,ret)

        self.span(0xab25,0xab32)
        if state['animation_enabled']==0:
            self.span(0xab34,0xab34)
        else:
            self.span(0xab37,0xab39)
            for i in range(8):
                self.span(0xac1f,0xac22)
                if i==7:break
                self.span(0xac24,0xac24)
                self.span(0xab3c,0xab4b)
                state['counters'][i]=(state['counters'][i]+1)&65535
                if signed(state['counters'][i])<=7:
                    self.span(0xab4d,0xab4d)
                else:
                    self.span(0xab50,0xab7a)
                    state['counters'][i]=0
                    phase=signed(state['phases'][i]+1)
                    phase=phase-int(phase/2)*2
                    state['phases'][i]=phase&65535
                    slot=signed(state['word_slots'][i])
                    if slot>=7:
                        self.span(0xab7c,0xab7c)
                    else:
                        if not 0<=slot<7 or phase not in (0,1):
                            raise NotImplementedError('Invalid animated picture state')
                        self.span(0xab7f,0xac19)
                        sx,sy,ex,ey=state['source_rects'][phase][i]
                        child('copy_rect',[5,5,slot*23+144,4,ey,ex,sy,sx])
                self.span(0xac1e,0xac1e)
        self.span(0xac27,0xac36)
        dx=dy=0
        left=False
        if signed(state['camera_x'])>0:
            self.span(0xac38,0xac3e)
            left=signed(state['player_x'])<144
        if left:
            self.span(0xac40,0xac4e)
            state['camera_x']=(state['camera_x']-1)&65535
            state['player_x']=(state['player_x']+8)&65535
            dx=8
        else:
            self.span(0xac50,0xac5a)
            if signed(state['attr_width']-36)>signed(state['camera_x']):
                self.span(0xac5c,0xac62)
                if signed(state['player_x'])>144:
                    self.span(0xac64,0xac6d)
                    state['camera_x']=(state['camera_x']+1)&65535
                    state['player_x']=(state['player_x']-8)&65535
                    dx=-8
        self.span(0xac72,0xac77)
        up=False
        if signed(state['camera_y'])>0:
            self.span(0xac79,0xac7e)
            up=signed(state['player_y'])<108
        if up:
            self.span(0xac80,0xac8e)
            state['camera_y']=(state['camera_y']-1)&65535
            state['player_y']=(state['player_y']+8)&65535
            dy=8
        else:
            self.span(0xac90,0xac9a)
            if signed(state['attr_height']-19)>signed(state['camera_y']):
                self.span(0xac9c,0xaca2)
                if signed(state['player_y'])>132:
                    self.span(0xaca4,0xacad)
                    state['camera_y']=(state['camera_y']+1)&65535
                    state['player_y']=(state['player_y']-8)&65535
                    dy=-8
        self.span(0xacb2,0xacc0)
        if state['render_page'] not in (0,1):raise NotImplementedError('Invalid render page')
        page=(state['render_page']+1)%2
        child('draw_page',[page])
        return self.path,state,device['graphics_state'],calls,{'dx':dx,'dy':dy,'page':page}
