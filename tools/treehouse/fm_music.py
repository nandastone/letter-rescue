"""Independent data-level implementation of the original melodic FM driver.

Register order follows resident image 1F92A..1FCC4; patch bytes come from TH
resource (tag 00000000, id 1). This is a build-time music renderer input, never
a recording of original hardware writes. Unsupported features fail explicitly.
"""
from __future__ import annotations


class MelodicDriver:
    def __init__(self, bank: dict, frequencies: list[int], operators: list[int]):
        self.patches = bank['patches']
        if len(frequencies) not in (12, 14):
            raise ValueError('Expected twelve notes with optional neighboring frequencies')
        self.neighbors = frequencies if len(frequencies) == 14 else None
        self.frequencies = frequencies[1:13] if self.neighbors else frequencies
        self.operators = operators
        self.programs = list(range(16))
        self.notes = [0] * 9
        self.channels = [0] * 9
        self.key = [0] * 9
        self.cursor = 0
        self.enabled = 65535
        self.transpose = 0
        self.irq = 0
        self.writes = []
        self.bend_range = 12
        self.reset()

    def write(self, register: int, value: int):
        self.writes.append(dict(irq=self.irq, register=register, value=value & 255))

    def reset(self):
        for voice in range(9):
            self.write(0xa0 + voice, 0)
            self.write(0xb0 + voice, 0)
        self.programs = list(range(16))
        self.notes = [0] * 9
        self.channels = [0] * 9
        self.enabled = 65535
        self.transpose = 0
        self.pitch = [(0, 0)] * 16
        self.rpn = 255
        self.bend_cents = 12
        # The original leaves its rotating allocation cursor and bend range.

    def note_off(self, channel: int, note: int):
        for voice in range(9):
            if self.notes[voice] == note and self.channels[voice] == channel:
                self.notes[voice] = 0
                self.write(0xb0 + voice, self.key[voice] & ~32)
                return
        if self.patches[self.programs[channel]][13]:
            raise ValueError('Rhythm patches are not implemented yet')

    def note_on(self, channel: int, note: int, velocity: int):
        if not velocity:
            self.note_off(channel, note)
            return
        if not self.enabled & (1 << channel):
            return
        patch = self.patches[self.programs[channel]]
        if patch[13]:
            raise ValueError('Rhythm patches are not implemented yet')
        free = next(((self.cursor + i) % 9 for i in range(9)
                     if self.notes[(self.cursor + i) % 9] == 0), None)
        # Original advances the search cursor even when no voice is free.
        self.cursor = (self.cursor + 1) % 9
        if free is None:
            return
        self.write(0xc0 + free, patch[2])
        for index in range(2):
            operator = self.operators[free * 2 + index]
            for j, register in enumerate((0x20, 0x40, 0x60, 0x80, 0xe0)):
                value = patch[3 + index * 5 + j]
                if j == 1 and (index == 1 or patch[2] & 1):
                    attenuation = min(127, max(64, ((value & 63) + 64) * 225 // (velocity + 161))) - 64
                    value = (value & 192) | attenuation
                self.write(register + operator, value)
        self.notes[free], self.channels[free] = note, channel
        self.frequency(free)

    def frequency(self, voice: int):
        offset, direction = self.pitch[self.channels[voice]]
        semitone = (self.notes[voice] - 31 + self.transpose + (offset >> 8)) & 255
        if semitone >= 128:
            semitone -= 256
        while semitone < 0:
            semitone += 12
        octave, index = divmod(semitone, 12)
        frequency = self.frequencies[index]
        if direction:
            if not self.neighbors:
                raise ValueError('Pitch bend requires the two original neighboring frequency entries')
            fraction = offset & 255
            if direction > 0:
                frequency += ((self.neighbors[index + 2] - frequency) * fraction) >> 8
            else:
                frequency -= ((frequency - self.neighbors[index]) * fraction) >> 8
        self.key[voice] = ((octave << 2) | (frequency >> 8) | 32) & 255
        self.write(0xa0 + voice, frequency & 255)
        self.write(0xb0 + voice, self.key[voice])

    def pitch_bend(self, channel: int, low: int, high: int):
        bend = (high << 7 | low) - 8192
        direction = (bend > 0) - (bend < 0)
        if bend == -8192:
            offset = self.bend_range << 8
        else:
            offset = ((abs(bend) << 3) * (self.bend_range << 8)) >> 16
        if direction < 0:
            # The driver negates only the semitone byte; its fraction is a
            # magnitude interpolated toward the previous table entry.
            offset = ((-(offset >> 8) & 255) << 8) | (offset & 255)
        self.pitch[channel] = (offset, direction)
        for voice in range(9):
            if self.notes[voice] and self.channels[voice] == channel:
                self.frequency(voice)

    def event(self, event: dict):
        self.irq = event['irq']
        data = event['data']
        if event['kind'] == 'sysex':
            # Vendor 000034, drivers 0/1, commands transpose/disable/enable.
            if len(data) >= 6 and data[:3] == [0, 0, 52] and data[3] in (0, 1):
                command, value = data[4:6]
                if command == 0:
                    self.transpose = value - 128 if value & 64 else value
                elif command == 1:
                    self.enabled &= ~(1 << (value & 15))
                elif command == 2:
                    self.enabled |= (1 << value) & 65535
            return
        if event['kind'] != 'channel':
            return
        status, channel = event['status'] >> 4, event['status'] & 15
        if status == 8:
            self.note_off(channel, data[0])
        elif status == 9:
            self.note_on(channel, *data)
        elif status == 12:
            if data[0] < len(self.patches):
                self.programs[channel] = data[0]
        elif status == 14:
            self.pitch_bend(channel, *data)
        elif status == 11:
            if data == [100, 0]:
                self.rpn = 0
            elif self.rpn != 255:
                if data[0] == 6:
                    self.bend_range = data[1]
                elif data[0] == 38:
                    self.bend_cents = data[1]


def render_registers(track: dict, bank: dict, frequencies: list[int], operators: list[int]) -> list[dict]:
    driver = MelodicDriver(bank, frequencies, operators)
    for event in track['native']['events']:
        driver.event(event)
    return driver.writes
