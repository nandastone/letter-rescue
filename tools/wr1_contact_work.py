"""Original nearby-cell scan and word revelation, including its graphics work.

Matching outcomes and pickup subroutines are explicit remaining boundaries.
Initial live attributes and words drive the scan; later observations do not.
"""
import copy
from wr1_graphics_work import GraphicsWork
from wr1_text_work import TextWork


def signed(value):
    return ((value+32768)&65535)-32768


class ContactWork(GraphicsWork):
    def __init__(self,catalogue):
        super().__init__(catalogue)
        self.graphics=GraphicsWork(catalogue)
        self.text=TextWork(catalogue)

    def child(self,kind,args,text_bytes=None):
        initial=copy.deepcopy(self.device)
        initial['args']=args
        if text_bytes is not None:initial['text_bytes']=text_bytes
        start=len(self.path)
        if kind in ('text_color','text_background'):
            path,state=self.text.style(kind,initial)
            ret=0xf6ef if kind=='text_color' else 0xf73c
        elif kind=='text_cursor':path,state=self.text.cursor(initial);ret=0xdbcf
        elif kind=='text_string':path,state=self.text.string(initial);ret=0x10587
        elif kind=='string_length':
            path,_=self.text.length(initial);state=initial['graphics_state'];ret=0x2247a
        elif kind=='draw_page':path,state=self.graphics.draw_page(initial);ret=0xf453
        elif kind=='fill_style':path,state=self.graphics.fill_style(initial);ret=0xf557
        else:raise ValueError('Unknown contact child')
        self.path.extend(path)
        self.device['graphics_state']=state
        self.calls.append({'kind':kind,'args':args,'start':start,'return':len(self.path)})
        self.span(ret,ret)

    def body(self,initial,attributes,graphics):
        self.path=[]
        self.calls=[]
        self.state=copy.deepcopy(initial)
        self.attributes=copy.deepcopy(attributes)
        self.device=copy.deepcopy(graphics)
        self.span(0xc1aa,0xc1bc)
        self.child('fill_style',[0,3,0])
        self.span(0xc1c1,0xc1c6)
        active=self.state['active_word']==1
        if not active:self.span(0xc1c8,0xc1c8)
        self.scan(active)
        self.span(0xc6f3,0xc6f7)
        return self.path,self.state,self.device['graphics_state'],self.attributes,self.calls

    def scan(self,active):
        s=self.state
        self.span(0xc1cb if active else 0xc57a,0xc1d1 if active else 0xc580)
        row=max(signed(s['gy']-5),0)
        if row>0:self.span(0xc1d3 if active else 0xc582,0xc1da if active else 0xc589)
        else:self.span(0xc1dc if active else 0xc58b,0xc1dc if active else 0xc58b)
        self.span(0xc1de if active else 0xc58d,0xc1de if active else 0xc58d)
        while True:
            self.span(0xc563 if active else 0xc6e2,0xc567 if active else 0xc6e6)
            if row>s['gy']:
                if active:self.span(0xc569,0xc569)
                return
            self.span(0xc56c if active else 0xc6e8,0xc572 if active else 0xc6ee)
            if row>=signed(s['map_height']-1):
                if active:self.span(0xc577,0xc577)
                return
            self.span(0xc574 if active else 0xc6f0,0xc574 if active else 0xc6f0)
            self.span(0xc1e1 if active else 0xc590,0xc1e5 if active else 0xc594)
            col=max(signed(s['gx']-1),0)
            if col>0:self.span(0xc1e7 if active else 0xc596,0xc1ec if active else 0xc59b)
            else:self.span(0xc1ee if active else 0xc59d,0xc1ee if active else 0xc59d)
            self.span(0xc1f0 if active else 0xc59f,0xc1f0 if active else 0xc59f)
            while True:
                self.span(0xc54d if active else 0xc6cc,0xc555 if active else 0xc6d4)
                if col>=signed(s['gx']+4):break
                self.span(0xc557 if active else 0xc6d6,0xc55d if active else 0xc6dc)
                if col>=signed(s['map_width']-1):break
                self.span(0xc55f if active else 0xc6de,0xc55f if active else 0xc6de)
                self.span(0xc1f3 if active else 0xc5a2,0xc201 if active else 0xc5b0)
                if not 0<=col<len(self.attributes) or not 0<=row<len(self.attributes[col]):
                    raise NotImplementedError('Contact read outside initial attribute map')
                value=self.attributes[col][row]
                if value<(14 if active else 7):
                    if active:
                        self.span(0xc206,0xc20a)
                        if col==s['source_x']:
                            self.span(0xc20c,0xc210)
                            if row==s['source_y']:
                                self.span(0xc212,0xc212);return
                        raise NotImplementedError('Matching result graphics/score/RNG work')
                    self.span(0xc5b5,0xc5ba)
                    if col==s['last_x']:
                        self.span(0xc5bc,0xc5c1)
                        if row==s['last_y']:
                            self.span(0xc5c3,0xc5c3);return
                    self.reveal(col,row,value)
                    return
                self.span(0xc203 if active else 0xc5b2,0xc203 if active else 0xc5b2)
                self.span(0xc52c if active else 0xc6ab,0xc530 if active else 0xc6af)
                if col>=s['gx']:
                    self.span(0xc532 if active else 0xc6b1,0xc540 if active else 0xc6bf)
                    if value>0x7a:raise NotImplementedError('Pickup graphics/score work')
                self.span(0xc54c if active else 0xc6cb,0xc54c if active else 0xc6cb)
                col=signed(col+1)
            self.span(0xc562 if active else 0xc6e1,0xc562 if active else 0xc6e1)
            row=signed(row+1)

    def reveal(self,col,row,value):
        s=self.state
        self.span(0xc5c6,0xc629)
        if not 0<=s['word_offset']<7:raise NotImplementedError('Invalid word rotation')
        index=(value+s['word_offset'])%7
        s.update(active_word=1,active_index=index,source_x=col,source_y=row,last_x=col,last_y=row)
        self.attributes[col][row]=value+7
        if s['sound_mode']:
            self.span(0xc62b,0xc635)
            s.update(speaker_segment=s['data_segment'],speaker_offset=0x4ba,speaker_index=0)
        self.span(0xc63b,0xc63f);self.child('text_background',[12])
        self.span(0xc644,0xc648);self.child('text_color',[3])
        self.span(0xc64d,0xc651);self.child('text_background',[15])
        self.span(0xc656,0xc65a);self.child('text_color',[3])
        self.span(0xc65f,0xc663);self.child('draw_page',[5])
        data=list(s['words'][index].encode('ascii'))+[0]
        args=[signed(0x9970+8*index),s['data_segment']]
        self.span(0xc668,0xc677);self.child('string_length',args,data)
        self.span(0xc67c,0xc690);self.child('text_cursor',[5,59+4*(8-(len(data)-1))])
        self.span(0xc695,0xc6a4);self.child('text_string',args,data)
        self.span(0xc6a9,0xc6a9)
