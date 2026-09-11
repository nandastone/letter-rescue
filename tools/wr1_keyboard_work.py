"""Recovered WR1 IRQ1 scan-code dispatch and instruction work, before IRET."""
import copy

HELD = {0xc882:'01a8',0xc88b:'01a4',0xc894:'01a2',0xc8cd:'0192',0xc8d6:'0190',
        0xc8df:'0194',0xc8e7:'0196',0xc91c:'01a6',0xc924:'019a',0xc93b:'019c'}
LATCHED = {0xc89d:'01b2',0xc8ad:'01b0',0xc8bd:'019e',0xc8ef:'01a0',
           0xc8fe:'01ae',0xc90d:'018c',0xc92c:'0198'}


class KeyboardWork:
    def __init__(self,catalogue):
        self.instructions=catalogue['keyboard_instructions']
        self.targets=catalogue['keyboard_targets']

    def span(self,start,end):
        while start<=end:
            op,following=self.instructions[str(start)]
            if start==0xc722:op='keyboard_read'
            elif start==0xc953:op='eoi'
            self.path.append((op,start))
            start=following

    def body(self,initial,scan):
        self.path=[]
        state=copy.deepcopy(initial)
        state['scan']=scan
        self.span(0xc722,0xc739)
        if state['pressed']==0xe0:
            self.span(0xc73b,0xc73b)
        else:
            self.span(0xc73e,0xc743)
            state['pressed']=int(not scan&128)
            if scan&128:self.span(0xc745,0xc74b)
            else:self.span(0xc74d,0xc74d)
            state['scan']=scan&127
            self.span(0xc753,0xc75d)
            handled=False
            if not state['custom']:self.span(0xc75f,0xc75f)
            else:
                for i,(start,key) in enumerate([(0xc762,'0190'),(0xc776,'0192'),(0xc78a,'0196'),(0xc79e,'0194'),(0xc7b2,'019e')]):
                    self.span(start,start+7)
                    if state['scan']!=state['bindings'][i]:continue
                    if i<4:
                        self.span(start+9,start+15)
                        state['flags'][key]=state['pressed']
                    else:
                        self.span(0xc7bb,0xc7c0)
                        if state['pressed']:
                            self.span(0xc7c2,0xc7c2)
                            state['flags'][key]=1
                        self.span(0xc7c8,0xc7c8)
                    handled=True
                    break
            if not handled:
                self.span(0xc7cb,0xc7d4)
                if not 1<=state['scan']<=80:self.span(0xc7d6,0xc7d6)
                else:
                    self.span(0xc7d9,0xc7dd)
                    target=self.targets[state['scan']-1]
                    if target in HELD:
                        self.span(target,target+6)
                        state['flags'][HELD[target]]=state['pressed']
                    elif target in LATCHED:
                        self.span(target,target+5)
                        if state['pressed']:
                            self.span(target+7,target+7)
                            state['flags'][LATCHED[target]]=1
                        self.span(target+13,target+13)
                    elif target!=0xc943:raise NotImplementedError(f'Keyboard target {target:x}')
        self.span(0xc943,0xc948)
        if state['pressed']:
            self.span(0xc94a,0xc94a)
            state['activity']=1
        self.span(0xc950,0xc95e)
        return self.path,state
