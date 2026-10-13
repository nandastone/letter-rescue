"""Decode original Treehouse DOS digital NUL-SND resources.

The variable-width delta codec is transcribed from the original v1.1 routine
at unpacked image offset 0x1BE74. See testing/treehouse_demo_music_research.md.
Returns unsigned eight-bit mono PCM. Playback looping remains a runtime choice.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class SoundInfo:
    sample_rate: int
    codec: int
    declared_samples: int
    decoded_samples: int
    loop: bool
    loop_start: int
    loop_end: int
    consumed_bytes: int
    trailing_bytes: bytes
    decode_cycles: int = 0

    @property
    def count_matches(self) -> bool:
        return self.declared_samples == self.decoded_samples


def decode_sound_with_info(data: bytes) -> tuple[SoundInfo, bytes]:
    """Decode with original header, loop boundaries and count anomalies retained.

    Compressed streams contain their own output count. The original loader uses
    that count, even when the header differs (DIGISND 10123). A trailing byte is
    present in 73 original resources; retain it rather than treat it as audio.
    """
    if len(data) < 10:
        raise ValueError("Truncated digital sound header")
    kind, rate, codec, declared, loop_start, loop_end = struct.unpack_from(
        "<BHBHHH", data)
    if kind not in (1, 0x81) or not rate:
        raise ValueError("Unsupported sound type or sample rate")
    decode_cycles = 0
    if codec == 8:
        end = 10 + declared
        if end > len(data):
            raise ValueError("Truncated uncompressed digital sound")
        pcm = data[10:end]
    elif codec == 255:
        if len(data) < 13:
            raise ValueError("Truncated compressed digital sound")
        count = struct.unpack_from("<H", data, 10)[0]
        if count == 0:
            raise ValueError("Empty compressed digital sound")
        value = data[12]
        result = bytearray([value])
        bit = 13 * 8
        width = 0
        # Intrinsic normal-core work of resident E964, derived from each bit
        # and branch. Excludes resource reads, allocation and interrupt work.
        decode_cycles = 15

        def read_bits(n: int) -> int:
            nonlocal bit, decode_cycles
            if bit + n > len(data) * 8:
                raise ValueError("Truncated digital sound bit stream")
            code = 0
            for _ in range(n):
                one = (data[bit // 8] >> (7 - bit % 8)) & 1
                decode_cycles += 8 + one
                code = (code << 1) | one
                bit += 1
            return code

        while len(result) < count:
            decode_cycles += 5 + (width == 0)
            code = read_bits(width or 3)
            decode_cycles += 4
            if width:
                decode_cycles += 2
                marker = 1 << (width - 1)
                if code == marker:
                    decode_cycles += 2
                    width = 0
                    continue
                decode_cycles += 4 + (code > marker)
                delta = code if code < marker else code - (1 << width)
                value = (value + delta) & 255
                result.append(value)
            elif code == 7:
                decode_cycles += 5
                value = (value + 128) & 255
                result.append(value)
            else:
                decode_cycles += 7
                width = 2 + code
        decode_cycles += 2 + 9 + count + 2
        end = (bit + 7) // 8
        pcm = bytes(result)
    else:
        raise ValueError(f"Unsupported digital sound codec: {codec}")
    if len(data) - end > 1:
        raise ValueError("Unexpected trailing digital sound data")
    info = SoundInfo(rate, codec, declared, len(pcm), bool(kind & 0x80),
                     loop_start, loop_end, end, data[end:], decode_cycles)
    return info, pcm


def decode_sound(data: bytes) -> tuple[int, bytes]:
    """Return (sample_rate, unsigned eight-bit mono PCM)."""
    info, pcm = decode_sound_with_info(data)
    return info.sample_rate, pcm
