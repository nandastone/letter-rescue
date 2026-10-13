# Treehouse DOS graphics: decoder and palette findings

Date: 2026-09-25. Target: the locally pinned DOS v1.1 package described in
[the port assessment](treehouse_port_assessment.md). Evidence comes from the
actual DAT resources, public implementation references, and the native
`testing/output/treehouse/boot-1800/boot.png` capture. No game code changed.

## Useful source references and their limits

- ScummVM's [DOSBitmap in bitmap.cpp](https://github.com/scummvm/scummvm/blob/master/engines/mohawk/bitmap.cpp)
  establishes the six-byte DOS image header and related LZ family. Its current
  implementation rejects the 0x80 flag and compression methods 1, 2 and 4, all
  present in Treehouse. Its EGA expansion must not be applied indiscriminately.
  `graphics.cpp` is general surface/blitting code; the decoder is `bitmap.cpp`.
- SDLPoP's [seg009.c](https://github.com/NagyD/SDLPoP/blob/master/src/seg009.c)
  implements packed-pixel decoding, all five methods, depth/stride calculation,
  and most-significant-pixel-first expansion. Its
  [types.h](https://github.com/NagyD/SDLPoP/blob/master/src/types.h) defines palette
  RGB, CGA-pattern and EGA-pattern fields. This is a working reverse-engineered
  implementation for a related game, not original Treehouse source.
- The Princed team's [format specification](https://www.popot.org/documentation/documents/FormatSpecifications_05Jan2008.pdf)
  documents DAT v2 tags, related compression and RGB6 palettes. Its prose RLE
  repeat description is ambiguous: the working SDLPoP algorithm negates the
  signed control byte. The local complete-image probe validates that behavior.

## SHAP payload decoding

Offsets here are relative to a resource's payload, excluding its DAT checksum
byte. The following layout is supported by local observations and the resource
agent's successful complete decode of all **2,337 SHAPs**.

| Offset | Type | Meaning |
| --- | --- | --- |
| 0 | u16 little endian | Height |
| 2 | u16 little endian | Width |
| 4 | u16 little endian | Format flags |
| 6 | bytes | Compressed or raw packed pixels |

Compute `depth = ((flags >> 12) & 7) + 1`,
`method = (flags >> 8) & 15`,
`stride = (width * depth + 7) // 8`, and expected bytes `stride * height`.
Observed format high bytes include B0-B4 (4 bits/pixel), 00-04 (1 bit/pixel),
and F3 (8 bits/pixel). The low flag byte is zero in the inspected SHAPs.

Methods are 0 raw rows, 1 RLE rows, 2 RLE columns, 3 LZ rows, and 4 LZ columns.
After decompressing methods 2/4, transpose bytes into row order:
`rowBytes[y * stride + x] = output[x * height + y]`. This is a **byte-column**
transpose before pixel expansion, not a transpose of individual pixels.

RLE reads one unsigned control byte. For values below 128, copy the next
`control + 1` input bytes. For values 128-255, repeat the next input byte
`256 - control` times. Every inspected resource produced the exact expected
size and consumed its full input under these rules; do not silently truncate
runs or pad missing data in the maintained decoder.

LZ uses a zero-filled 1,024-byte circular buffer with initial write position
958 (`1024 - 66`). Read a flag byte, processing its bits from least significant
to most significant. A set bit emits the next literal byte. A clear bit reads a
big-endian 16-bit reference: source position is its low ten bits and length is
its upper six bits plus three. Copy one byte at a time through the circular
buffer, allowing overlap, writing every emitted byte into the buffer and
advancing both source/write positions modulo 1,024. Stop at the declared output
size and validate complete input consumption.

Expand each row's packed pixels from most significant bits to least significant
bits. A 4-bit row's first pixel is the high nibble; a 1-bit row's first pixel is
bit 7. Ignore only the last byte's unused right-edge padding bits. Preserve raw
indices for 1-bit shapes until the runtime mask/color role is recovered; do not
assume every monochrome shape uses the same visible palette.

Probe reference:
`testing/output/treehouse/research-resources/decode_probe.py` (resource agent).
Its result was independently rerun during this investigation: 2,337 successes,
zero decoder failures. This establishes resource decompression, not animation,
placement, or full gameplay parity.

## SHPL fields and image-to-palette relationships

The actual Treehouse payload fits this layout:

| Offset | Type | Observed interpretation |
| --- | --- | --- |
| 0 | u16 little endian | First SHAP ID in associated range |
| 2 | u16 little endian | Count of SHAP IDs in range |
| 4 | u16 little endian | Always zero here; related SDLPoP field is palette row bits |
| 6 | u8 | Number of RGB colors |
| 7 | `3 * colorCount` bytes | RGB triples, channels in 0-63 |
| after RGB | optional 48 bytes | Present for every 16-color SHPL; absent for TH64 palettes |

The first/count interpretation covers every SHAP in its containing archive.
There are six SHPLs each in BOY/GIRL, 74 in MODULES, 71 in TH, and three in TH64.
The three TH64 palettes have 64, 64, and 80 colors, with total sizes 199, 199,
and 247 bytes respectively. Every other inspected SHPL has 16 colors and is
103 bytes long.

**The image-to-palette relation is not unique.** TH SHPL IDs 8000 and 8001 both
cover SHAP 8001-8062. MODULES SHPL 3100, 3101 and 3102 each cover SHAP 3101-3102,
with further such triplets. Keep the original palette IDs and ranges and allow
runtime selection. A permanent palette selected only by shape ID loses data.
BOY/GIRL and TH64 each give one range match for every shape; MODULES has 12
shapes with three matches and one with two; TH has 62 with two matches.

The 48-byte tail is strongly consistent with the related format's 16 CGA
pattern bytes plus 32 EGA pattern bytes, but Treehouse runtime interpretation
is not traced yet. For example TH SHPL 0 has 16 zero bytes followed by repeated
`01 23 45 67 89 AB CD EF` sequences. Keep those bytes rather than discarding
them. The field at offset 4 is not proven unused just because it is zero on disk.

## Native palette comparison

The full-color native title capture is based on **TH64 SHAP 1**, whose dimensions
are 320 by 200. TH SHAP 1 is the lower-color alternate exterior and differs
visibly. Native title signs and characters overlay the exterior, so compare the
uncovered background when judging its decode.

With TH64 SHPL 0, expand every six-bit channel using
`rgb8 = (rgb6 << 2) | (rgb6 >> 4)`. Direct decoded-background comparison against
the native RGB screenshot yields:

| Conversion | Exactly equal pixels, out of 64,000 |
| --- | ---: |
| `v << 2` | 6,272 |
| `v * 255 // 63` | 14,267 |
| `(v << 2) | (v >> 4)` | **42,817** |

With bit replication, all differences are confined to x=0-170, y=0-178, the
area containing title/copyright overlays and characters. **All pixels at
x >= 171 match exactly.** Also, 62 of the palette's 64 expanded colors occur in
the native capture. This establishes the proper RGB conversion for comparison
with this emulator capture; it does not prove physical monitor appearance or
complete title composition.

## PSL is a sound-reference lead

The `\0PSL` resources are not established palette lists. All 195 inspected
payloads are exactly `u16 count` followed by that many little-endian u16 IDs.
Every one of their 442 references (82 distinct IDs) matches a `\0SND` resource
in the audio DAT set. For example BOY PSL 20100 holds IDs 10048 and 10049, both
present in multiple sound backends. This strongly suggests a sound list;
whether it specifies preload sets, selection order, or playback instructions
needs runtime tracing. The matching numeric IDs alone do not establish when
sounds play.

## Remaining rendering work

- Recover exact SHPL selection, global palette placement, transparency/masks,
  palette changes, and CGA/EGA behavior from the executable.
- Decode SCR animation/drawing scripts and recover sprite positions, ordering,
  flips, clipping, event triggers, and timing.
- Compose the original title and other screens from decoded resources and
  compare against native output before changing text or scaling.
- Retain both full-color TH64 and lower-color TH variants; file naming alone
  is not the graphics-mode selection rule.
