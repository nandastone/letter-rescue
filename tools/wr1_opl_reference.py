"""AdLib MIDI handlers recovered from WR1.EXE1ec59..1f26a.

Pure register output; no recorded future events or synthesis timing are used.
"""
import copy
import struct


class Opl:
    def __init__(self, tables, cmf, initial):
        self.tables = tables
        self.state = copy.deepcopy(initial)
        self.instruments = copy.deepcopy(tables['default_instruments'])
        offset = struct.unpack_from('<H',cmf,6)[0]
        count = struct.unpack_from('<H',cmf,36)[0]
        for i in range(count):
            self.instruments[i] = list(cmf[offset+16*i:offset+16*i+11])
        self.writes = []

    def write(self, register, value):
        self.writes.append([register & 255,value & 255])

    def instrument(self, voice, program):
        values = self.instruments[program]
        mod,car = self.tables['modulators'][voice],self.tables['carriers'][voice]
        for i,base in enumerate([0x20,0x40,0x60,0x80,0xe0]):
            self.write(base+mod,values[2*i])
            self.write(base+car,values[2*i+1])
        self.state['levels'][voice] = values[3]
        self.write(0xc0+voice,values[10])

    def restart(self):
        # EXE1f1e9 runs before the CMF instrument copy. For a repeat, the bank
        # already contains this song. Channel volume and percussion type persist.
        self.writes = []
        self.state['rhythm'] = 192
        self.write(0xbd,192)
        for voice in range(9):
            self.instrument(voice,0)
        for field,count,value in [('programs',16,0),('bends',16,0),('notes',9,0),('voices',9,65535)]:
            self.state[field] = [value]*count
        return self.writes

    def frequency(self, voice, channel, note, on):
        s,t = self.state,self.tables
        s['notes'][voice] = note
        octave,key = divmod((note-1)&255,12)
        frequency = t['frequencies'][key]
        bend = s['bends'][channel]
        if bend:
            step = t['bend_steps'][key+(bend>=128)]
            delta = ((bend*step*2)&65535)>>8
            frequency = (frequency + (delta if bend==128 else -delta)) & 65535
        self.write(0xa0+voice,frequency&255)
        block = (octave*4)&255
        if on and not (s['rhythm']&32 and channel>=11):
            block |= 32
        self.write(0xb0+voice,block|((frequency>>8)&3))
        level = s['levels'][voice]
        scale = ((min(s['volumes'][channel],95)+32)*2)&255
        attenuation = (63-((((63-(level&63))*scale)>>8)+1))&255
        self.write(0x40+t['carriers'][voice],(level&192)|attenuation)

    def note(self, channel, note, on):
        s,t = self.state,self.tables
        count = 6 if s['rhythm']&32 else 9
        if s['rhythm']&32 and ((s['percussion']==1 and channel==9) or channel>=11):
            mask = t['percussion'][(note-35)&255] if s['percussion']==1 and channel==9 else 16>>(channel-11)
            s['rhythm'] ^= mask
            self.write(0xbd,s['rhythm'])
            return
        if not on:
            for voice in range(count):
                if s['voices'][voice]>>8==channel and s['notes'][voice]==note:
                    self.frequency(voice,channel,note,False)
                    s['notes'][voice] = 0
                    return
            return
        # Search idle voices on this MIDI channel, then unassigned voices,
        # then recycle the first silent voice. Native allocation is not LRU.
        voice = next((i for i in range(count) if s['voices'][i]>>8==channel and not s['notes'][i]),None)
        if voice is None:
            voice = next((i for i in range(count) if s['voices'][i]>>8==255 and not s['notes'][i]),None)
        if voice is None:
            voice = next((i for i in range(count) if not s['notes'][i]),None)
            if voice is None:
                return
            s['voices'][voice] = 65535
        program = s['programs'][channel]
        if s['voices'][voice]&255 != program:
            s['voices'][voice] = (channel<<8)|program
            self.instrument(voice,program)
        self.frequency(voice,channel,note,True)

    def control(self, channel, controller, value):
        s = self.state
        if controller==7:
            s['volumes'][channel] = value
        elif controller in (104,105):
            # The native code clears BH before comparing it to 68h, so both
            # controller numbers take the same branch (EXE1ee5a..1ee6e).
            s['bends'][channel] = value
        elif controller==103 and value in (0,1):
            s['rhythm'] = 192 if value==0 else 224
            s['percussion'] = value
            self.write(0xbd,s['rhythm'])
            s['voices'][6:9] = [65535 if value==0 else 4351]*3
            if value:
                for register,datum in self.tables['rhythm_registers']:
                    self.write(register,datum)
                self.write(0xbd,224)
                self.write(8,0)
        elif controller==123:
            # EXE1ed44: loop target 57fc reloads the voice-table base each time.
            # Unlike ordinary note-off, this clears both frequency registers.
            for voice in range(9):
                if s['voices'][voice]>>8==channel:
                    self.write(0xa0+voice,0)
                    self.write(0xb0+voice,0)
                    s['notes'][voice] = 0

    def event(self, event):
        self.writes = []
        s = self.state
        if s['mode']!=1:
            raise ValueError('Only the observed AdLib mode is implemented')
        status,payload = event['status'],event['data']
        kind,channel = status&240,status&15
        if kind in (128,144):
            note = payload[0]
            percussion = s['rhythm']&32 and ((s['percussion']==1 and channel==9) or channel>=11)
            if not percussion:
                note = (note+s['transpose'])&255
            self.note(channel,note,kind==144 and payload[1]!=0)
        elif kind in (160,176):
            self.control(channel,payload[0],payload[1])
        elif kind==192:
            s['programs'][channel] = payload[0]
        return self.writes
