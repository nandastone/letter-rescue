#!/usr/bin/env python3
"""Generate simple sound effects as WAV files."""

import struct
import math
import os

def generate_wav(filename, frequency, duration, volume=0.5, wave_type="sine", fade_out=True):
    """Generate a simple WAV file."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration)

    samples = []
    for i in range(num_samples):
        t = i / sample_rate

        if wave_type == "sine":
            sample = math.sin(2 * math.pi * frequency * t)
        elif wave_type == "square":
            sample = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
        elif wave_type == "noise":
            import random
            sample = random.uniform(-1, 1)
        else:
            sample = math.sin(2 * math.pi * frequency * t)

        # Fade out.
        if fade_out:
            envelope = 1.0 - (i / num_samples)
            sample *= envelope

        sample *= volume
        samples.append(sample)

    # Write WAV file.
    with open(filename, "wb") as f:
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = num_samples * block_align

        # RIFF header.
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")

        # fmt chunk.
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))  # PCM.
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))

        # data chunk.
        f.write(b"data")
        f.write(struct.pack("<I", data_size))

        for sample in samples:
            value = int(sample * 32767)
            value = max(-32768, min(32767, value))
            f.write(struct.pack("<h", value))


def generate_multi_tone(filename, tones, volume=0.5):
    """Generate a WAV with multiple sequential tones. tones = [(freq, duration), ...]."""
    sample_rate = 22050
    all_samples = []

    for freq, duration in tones:
        num_samples = int(sample_rate * duration)
        for i in range(num_samples):
            t = i / sample_rate
            envelope = 1.0 - (i / num_samples) * 0.3
            sample = math.sin(2 * math.pi * freq * t) * volume * envelope
            all_samples.append(sample)

    num_samples = len(all_samples)
    with open(filename, "wb") as f:
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = num_samples * block_align

        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))

        for sample in all_samples:
            value = int(sample * 32767)
            value = max(-32768, min(32767, value))
            f.write(struct.pack("<h", value))


if __name__ == "__main__":
    sfx_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "sfx")
    os.makedirs(sfx_dir, exist_ok=True)

    # Jump: short upward chirp.
    generate_multi_tone(os.path.join(sfx_dir, "jump.wav"), [
        (400, 0.05), (600, 0.05), (800, 0.05),
    ], volume=0.3)

    # Correct match: happy ascending arpeggio.
    generate_multi_tone(os.path.join(sfx_dir, "correct.wav"), [
        (523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.2),
    ], volume=0.4)

    # Wrong match: descending buzz.
    generate_multi_tone(os.path.join(sfx_dir, "wrong.wav"), [
        (300, 0.15), (200, 0.2),
    ], volume=0.3)

    # Death: sad descending tone.
    generate_multi_tone(os.path.join(sfx_dir, "death.wav"), [
        (600, 0.1), (500, 0.1), (400, 0.1), (300, 0.15), (200, 0.2),
    ], volume=0.4)

    # Slime: squelchy sound.
    generate_wav(os.path.join(sfx_dir, "slime.wav"), 150, 0.3, volume=0.4, wave_type="square")

    # Collect item: short ping.
    generate_multi_tone(os.path.join(sfx_dir, "collect.wav"), [
        (880, 0.05), (1100, 0.08),
    ], volume=0.3)

    # Level complete: victory fanfare.
    generate_multi_tone(os.path.join(sfx_dir, "level_complete.wav"), [
        (523, 0.15), (659, 0.15), (784, 0.15), (1047, 0.3),
        (784, 0.1), (1047, 0.4),
    ], volume=0.4)

    # Block reveal: short chime.
    generate_multi_tone(os.path.join(sfx_dir, "reveal.wav"), [
        (700, 0.06), (900, 0.08),
    ], volume=0.25)

    # Door unlock: ascending triumphant tone.
    generate_multi_tone(os.path.join(sfx_dir, "unlock.wav"), [
        (440, 0.12), (554, 0.12), (659, 0.12), (880, 0.25),
    ], volume=0.35)

    print("Generated %d sound effects in %s" % (9, sfx_dir))
