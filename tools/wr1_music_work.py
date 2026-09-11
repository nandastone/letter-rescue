"""Recovered work from game INT 63h through return, excluding the BIOS tail.

This uses CMF bytes and current sequencer/voice state. Native durations and
future paths are never inputs. Timer programming is conditional on observed
driver mode; unsupported PIT reprogramming is rejected rather than skipped.
"""
import struct
from wr1_driver_work import DriverWork


class MusicWork(DriverWork):
    def __init__(self,catalogue,rhythm_writes,dispatcher_use_dx,external_timer=None):
        super().__init__(catalogue,rhythm_writes)
        self.driver = DriverWork(catalogue,rhythm_writes)
        self.dispatcher_use_dx = dispatcher_use_dx
        self.external_timer = external_timer

    def file_span(self,start,end):
        self.span(start-0x19580,end-0x19580)

    def delay(self,music,cursor):
        self.file_span(0x1f824,0x1f828)
        delay = 0
        while True:
            byte = music.byte(cursor)
            cursor = (cursor+1)&65535
            delay = ((delay<<7)|(byte&127))&0xffffffff
            self.file_span(0x1f82a,0x1f838)
            if byte<128:break
            self.file_span(0x1f83a,0x1f856)
        self.file_span(0x1f858,0x1f85a)
        return delay,cursor

    def repeat_memory(self,address,count):
        self.timeline.append((f'rep:{count}',address-0x19580))

    def reset_voices(self,opl):
        self.file_span(0x1f1e9,0x1f1f5)
        self.opl()
        self.file_span(0x1f1f8,0x1f1fa)
        for _ in range(9):
            self.file_span(0x1f1fc,0x1f1fc)
            self.instrument()
            self.file_span(0x1f1ff,0x1f204)
        for start,end,rep,count in [(0x1f206,0x1f20f,0x1f212,16),
                                    (0x1f214,0x1f21d,0x1f220,16),
                                    (0x1f222,0x1f227,0x1f22a,9),
                                    (0x1f22c,0x1f232,0x1f235,9)]:
            self.file_span(start,end)
            self.repeat_memory(rep,count)
        self.file_span(0x1f237,0x1f23a)
        self.writes.extend(opl.restart())

    def restart(self,music,opl):
        if self.external_timer!=1:
            raise NotImplementedError('CMF timer programming requires observed external-timer mode 1')
        if not 0<=music.state['data_offset']<16:
            raise ValueError('Expected normalized CMF segment offset')
        self.file_span(0x1f56b,0x1f56e)
        self.file_span(0x1f85b,0x1f88f)
        self.file_span(0x1f571,0x1f583)
        self.reset_voices(opl)
        self.file_span(0x1f586,0x1f594)
        self.file_span(0x1f596,0x1f59a)
        self.file_span(0x1f59c,0x1f5a8)
        self.repeat_memory(0x1f5aa,32)
        self.file_span(0x1f5ac,0x1f5d6)
        self.file_span(0x1f890,0x1f898)
        self.file_span(0x1f5d9,0x1f602)
        instruments = struct.unpack_from('<H',music.data,36)[0]
        for i in range(instruments):
            self.file_span(0x1f604,0x1f605)
            self.repeat_memory(0x1f608,11)
            self.file_span(0x1f60a,0x1f60e)
            if i+1<instruments:self.file_span(0x1f602,0x1f602)
        self.file_span(0x1f610,0x1f618)
        self.delay(music,(music.state['data_offset']+struct.unpack_from('<H',music.data,8)[0])&65535)
        self.file_span(0x1f61b,0x1f637)
        self.file_span(0x1f63a,0x1f653)

    def track_end(self,music,opl):
        s = music.state
        if len(s['tracks'])!=1:raise NotImplementedError('Work for ending one of several active tracks')
        self.file_span(0x1f7a6,0x1f7bb)
        self.file_span(0x1f7c0,0x1f7ca)
        self.file_span(0x1f7cc,0x1f7cc)
        self.file_span(0x1f7d7,0x1f7dd)
        if s['repeat']:
            self.file_span(0x1f7df,0x1f7f0)
            self.file_span(0x1f7f6,0x1f7f6)
            self.restart(music,opl)
            self.file_span(0x1f7f9,0x1f7f9)
        else:
            self.file_span(0x1f7fa,0x1f800)

    def finish(self,music):
        self.span(0x5103,0x5103)
        self.span(0x5108,0x510e)
        if music.tick()!=self.events:raise ValueError('Work planner and sequencer disagree')
        return self.timeline,self.writes

    def tick(self,music,opl):
        """Generate work and update models once; return work and register writes."""
        self.timeline = [('mov',0x2d8),('int',0x2da)]
        self.writes,self.events = [],[]
        self.span(0x50d9,0x50ea)
        if self.dispatcher_use_dx:self.span(0x50ec,0x50ec)
        self.span(0x50ee,0x5101)
        s = music.state
        self.file_span(0x1f65a,0x1f664)
        if not s['playing']:
            self.file_span(0x1f666,0x1f666)
        else:
            self.file_span(0x1f667,0x1f675)
            if ((s['counter']+1)&65535)>=s['division']:
                self.file_span(0x1f677,0x1f67e)
            self.file_span(0x1f683,0x1f683)
            for track in s['tracks']:
                self.file_span(0x1f68a,0x1f694)
                self.file_span(0x1f697,0x1f6a4)
                if not track['active']:
                    self.file_span(0x1f6a6,0x1f6ab)
                    continue
                self.file_span(0x1f6ad,0x1f6c2)
                delay = track['delay']
                if (((delay&65535)+(delay>>16))&65535)>1:
                    self.file_span(0x1f6c4,0x1f6d0)
                    continue
                self.file_span(0x1f6d2,0x1f6e2)
                cursor,status = track['cursor'],track['status']
                while True:
                    self.file_span(0x1f6e4,0x1f6ea)
                    byte = music.byte(cursor)
                    cursor = (cursor+1)&65535
                    if byte==255:
                        self.file_span(0x1f763,0x1f769)
                        kind = music.byte(cursor)
                        cursor = (cursor+1)&65535
                        if kind==47:
                            self.track_end(music,opl)
                            return self.finish(music)
                        self.file_span(0x1f76b,0x1f76d)
                        if kind==81:raise NotImplementedError('Tempo-port programming needs its own IO model')
                        self.file_span(0x1f76f,0x1f777)
                        size = music.byte(cursor)
                        cursor = (cursor+1)&65535
                        self.events.append({'status':255,'kind':kind,'data':[music.byte((cursor+i)&65535) for i in range(size)]})
                        cursor = (cursor+size)&65535
                    else:
                        self.file_span(0x1f6ec,0x1f6ee)
                        if byte<128:
                            cursor = (cursor-1)&65535
                            self.file_span(0x1f6f0,0x1f6f1)
                            self.file_span(0x1f703,0x1f70e)
                        else:
                            status = byte
                            self.file_span(0x1f6f4,0x1f700)
                        self.file_span(0x1f70f,0x1f725)
                        size = (2,2,2,2,1,1,2,0)[(status>>4)-8]
                        payload = []
                        if size:
                            self.file_span(0x1f727,0x1f72d)
                            payload.append(music.byte(cursor))
                            cursor = (cursor+1)&65535
                            if size>1:
                                self.file_span(0x1f72f,0x1f732)
                                payload.append(music.byte(cursor))
                                cursor = (cursor+1)&65535
                        midi = {'status':status,'data':payload}
                        self.events.append(midi)
                        self.file_span(0x1f733,0x1f733)
                        self.timeline.extend(self.driver.event(midi,opl.state))
                        self.timeline.append(('ret',0x599f))
                        self.writes.extend(opl.event(midi))
                    self.file_span(0x1f736,0x1f736)
                    delay,cursor = self.delay(music,cursor)
                    self.file_span(0x1f739,0x1f73c)
                    if not delay&65535:self.file_span(0x1f73e,0x1f741)
                    if delay:break
                self.file_span(0x1f743,0x1f760)
            self.file_span(0x1f68a,0x1f696)
        return self.finish(music)
