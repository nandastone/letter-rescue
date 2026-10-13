"""Decode Treehouse's type-2 SND resources without executing the DOS driver.

The payload after the sound-type byte is Standard MIDI File data. Keep musical
ticks and exact rational microseconds separate from the native sequencer's
timer quantization. Meta 07 is the cue byte consumed by the title controller
(unpacked image 1A4AC); it is not an inferred screenshot timestamp.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import struct
import zipfile

from resources import parse_archive


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def take(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError("Truncated MIDI data")
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def byte(self) -> int:
        return self.take(1)[0]

    def vlq(self) -> int:
        value = 0
        for _ in range(4):
            byte = self.byte()
            value = (value << 7) | (byte & 127)
            if byte < 128:
                return value
        raise ValueError("MIDI variable-length quantity exceeds four bytes")


def decode_sound(payload: bytes) -> dict:
    if not payload or payload[0] not in (2, 130):
        raise ValueError("Expected a type-2 MIDI SND resource")
    reader = Reader(payload[1:])
    if reader.take(4) != b'MThd' or reader.take(4) != b'\0\0\0\6':
        raise ValueError("Expected a six-byte MThd header")
    fmt, count, ppq = struct.unpack('>3H', reader.take(6))
    if fmt not in (0, 1) or count == 0 or (fmt == 0 and count != 1):
        raise ValueError("Unsupported MIDI format or track count")
    if ppq == 0 or ppq & 0x8000:
        raise ValueError("Expected positive MIDI pulses per quarter note")
    events = []
    for track in range(count):
        if reader.take(4) != b'MTrk':
            raise ValueError("Expected MTrk chunk")
        chunk = Reader(reader.take(struct.unpack('>I', reader.take(4))[0]))
        tick, running, ended = 0, None, False
        while chunk.pos < len(chunk.data):
            tick += chunk.vlq()
            first = chunk.byte()
            explicit = first >= 128
            if explicit:
                status = first
            else:
                if running is None:
                    raise ValueError("MIDI running status has no channel status")
                status = running
                chunk.pos -= 1
            event = dict(tick=tick, track=track, status=status, explicit_status=explicit)
            if 0x80 <= status <= 0xef:
                running = status
                data = chunk.take(1 if status >> 4 in (12, 13) else 2)
                if any(byte >= 128 for byte in data):
                    raise ValueError("MIDI channel data contains a status byte")
                event.update(kind='channel', data=list(data))
            elif status == 0xff:
                meta = chunk.byte()
                data = chunk.take(chunk.vlq())
                event.update(kind='meta', meta=meta, data=list(data))
                if meta == 0x51 and (len(data) != 3 or int.from_bytes(data, 'big') == 0):
                    raise ValueError("Invalid MIDI tempo")
                if meta == 0x2f:
                    if data or chunk.pos != len(chunk.data):
                        raise ValueError("Invalid or nonterminal MIDI end-of-track")
                    ended = True
                # SMF meta events do not replace the previous channel status.
            elif status in (0xf0, 0xf7):
                running = None
                event.update(kind='sysex', data=list(chunk.take(chunk.vlq())))
            else:
                raise ValueError(f"Unsupported SMF status {status:02x}")
            events.append(event)
        if not ended:
            raise ValueError("MIDI track has no end-of-track event")
    if reader.pos != len(reader.data):
        raise ValueError("Trailing data after MIDI tracks")
    events.sort(key=lambda event: (event['tick'], event['track']))
    tempo, previous, elapsed = 500000, 0, Fraction(0)
    cues = []
    for event in events:
        elapsed += Fraction((event['tick'] - previous) * tempo, ppq)
        previous = event['tick']
        event['time_us'] = [elapsed.numerator, elapsed.denominator]
        if event['kind'] == 'meta':
            if event['meta'] == 0x51 and event['track'] == 0:
                tempo = int.from_bytes(bytes(event['data']), 'big')
            elif event['meta'] == 7 and event['data']:
                cues.append(dict(tick=event['tick'], time_us=event['time_us'],
                                 value=event['data'][0], text=bytes(event['data']).decode('cp437')))
    return dict(format=fmt, tracks=count, ppq=ppq, loop=bool(payload[0] & 128),
                duration_ticks=previous, duration_us=[elapsed.numerator, elapsed.denominator],
                cues=cues, events=events, source_sha256=hashlib.sha256(payload).hexdigest())


def native_schedule(track: dict, frequency: int = 240) -> dict:
    """Resident 1A3FF/1A35D: fixed-point tick advancement and tempo byte order.

    This returns timer-interrupt ordinals, not emulated instruction durations.
    The tempo handler reads the final two SMF tempo bytes as a little-endian
    word. Preserve that original behavior instead of silently correcting it.
    """
    if track['format'] != 0:
        raise ValueError('Native scheduling currently covers single-track resources only')
    def increment(tempo):
        denominator = (tempo << 8) // track['ppq']
        if denominator == 0:
            raise ValueError('Tempo is too small for the original sequencer')
        value = ((256000000 // frequency) << 16) // denominator
        if value == 0:
            raise ValueError('Tempo does not advance the original sequencer')
        return value

    step, fraction, tick, irq, index = increment(500000), 0, 0, 0, 0
    events, tempos = [], []
    while index < len(track['events']):
        while index < len(track['events']) and track['events'][index]['tick'] <= tick:
            event = dict(track['events'][index], irq=irq)
            events.append(event)
            index += 1
            if event['kind'] == 'meta' and event['meta'] == 0x51 and event['track'] == 0:
                a, b, c = event['data']
                tempo = (a << 16) | (c << 8) | b
                step = increment(tempo)
                tempos.append(dict(irq=irq, tempo=tempo, step=step))
        if index == len(track['events']):
            break
        # Advance directly to the interrupt on which the next event is due.
        needed = (track['events'][index]['tick'] - tick) * 65536 - fraction
        jumps = max(1, (needed + step - 1) // step)
        whole = fraction + jumps * step
        tick += whole >> 16
        fraction = whole & 65535
        irq += jumps
    return dict(frequency=frequency, duration_irqs=irq, events=events, tempos=tempos)


def extract(source) -> dict:
    """Recover all eight MIDI resources and the original 128-instrument bank."""
    tracks, bank = {}, None
    with zipfile.ZipFile(source) as archive:
        for name in ('th', 'midisnd'):
            data = archive.read(f'TheTreeh/{name}.dat')
            for record in parse_archive(data):
                payload = data[record['payload_offset']:record['payload_offset'] + record['size']]
                if record['tag'] == 'SND' and payload[0] in (2, 130):
                    track = decode_sound(payload)
                    track['native'] = native_schedule(track)
                    tracks[f"{name}:{record['id']}"] = track
                elif name == 'th' and record['tag_hex'] == '00000000' and record['id'] == 1:
                    if len(payload) != 1 + payload[0] * 16:
                        raise ValueError('Invalid FM instrument bank')
                    bank = dict(source_sha256=hashlib.sha256(payload).hexdigest(),
                                patches=[list(payload[i:i + 16]) for i in range(1, len(payload), 16)])
    if len(tracks) != 8 or bank is None:
        raise ValueError('Missing original MIDI resources')
    return dict(tracks=tracks, bank=bank)
