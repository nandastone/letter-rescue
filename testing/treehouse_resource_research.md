# Treehouse DOS resource format research

Date: 2026-09-25. Scope: static examination of the acquired DOS distribution; no original game execution. This establishes extraction and bitmap decoding, not behavioral equivalence.

## Primary evidence and reproducibility

The primary artifact is `testing/output/treehouse/source/The_Treehouse_1991.zip` (SHA-1 `9b1f060e072865657ac6949203b4b2b891639b1e`). All offsets below are relative to individual uncompressed ZIP members. The local disposable probes are `testing/output/treehouse/research-resources/inspect_resources.py` and `decode_probe.py`; `inventory.json` records every resource's entry offset, payload offset, size, flags, checksum, SHA-256 and prefix. These analysis files are generated output, not maintained tools.

External primary source comparison: [ScummVM DOSArchive_v2](https://github.com/scummvm/scummvm/blob/master/engines/mohawk/resource.cpp#L413-L459) describes the same archive layout. [SDLPoP's decoding implementation](https://github.com/NagyD/SDLPoP/blob/master/src/seg009.c#L608-L852) provides the five image decoding methods that were experimentally applied to this game's bytes. [SDLPoP structure definitions](https://github.com/NagyD/SDLPoP/blob/master/src/types.h#L444-L449) match the six-byte bitmap header. Source locations were read on the date above; URLs track upstream master and should be pinned before becoming a reproducible dependency.

The evidence supports a shared DOS resource/image format with these implementations. It does not establish that Treehouse's gameplay engine is implemented in ScummVM or SDLPoP.

## Archive layout: confirmed across 3,806 resources

All integers are little endian. Ten DAT members follow this layout:

| File | File size | Directory offset | Directory size | Resource count |
|---|---:|---:|---:|---:|
| boy.dat | 113612 | 0x1AB82 | 4170 | 376 |
| girl.dat | 115694 | 0x1B3A4 | 4170 | 376 |
| digisnd.dat | 1113437 | 0x10F2ED | 2672 | 242 |
| ibm_snd.dat | 20587 | 0x4CC5 | 934 | 84 |
| midisnd.dat | 54519 | 0xD4A0 | 87 | 7 |
| modules.dat | 474679 | 0x6FE0A | 16429 | 1489 |
| mt32snd.dat | 26503 | 0x6121 | 1638 | 148 |
| th.dat | 400066 | 0x5EE02 | 11456 | 1034 |
| th64.dat | 54087 | 0xD2D2 | 117 | 9 |
| voices.dat | 412330 | 0x648DD | 461 | 41 |

File header: `u32 directory_offset; u16 directory_size`. Every observed file satisfies `directory_offset + directory_size == file_size`.

At directory offset: `u16 type_count`, followed by six-byte type records: `u32 tag; u16 resource_table_relative_offset`. Interpret the tag as a numeric four-character code: on-disk bytes `50 41 48 53` name `SHAP`. Preserve leading NUL bytes in tags; the sound type is `\0SND` and an all-zero type exists.

Each resource table starts at `directory_offset + relative_offset`: `u16 resource_count`, then 11-byte records:

| Relative byte | Type | Meaning |
|---:|---|---|
| 0 | u16 | Resource ID |
| 2 | u32 | Absolute offset of checksum byte |
| 6 | u16 | Payload byte count |
| 8 | 3 raw bytes | Flags/unknown metadata |

Extract payload from `stored_offset + 1` for `size` bytes. The preceding byte is a checksum: **all 3,806 resources satisfy `(checksum + sum(payload)) & 255 == 255`**. Every extracted range lies before its archive directory. The only three-byte flag values encountered are `00 00 00`, `20 00 00`, `40 00 00`. Their meaning is unresolved; `40` is not a generic compression flag because plaintext STRL resources also carry it.

Resource totals: SHAP 2337; NUL-SND 523; NUL-SCR 356; NUL-PSL 195; STRL 176; SHPL 160; TXT4 26; SONG 25; CURS 4; all-zero tag 3; FONT 1.

High-confidence extraction algorithm: verify header bounds; bound-check type records and their relative offsets; bound-check each resource table and 11-byte record; retain IDs/types/flags; verify payload bounds and checksum; export raw payload and its hash without interpreting or rewriting unknown fields. Small configuration and save files (`songs.dat`, `status.dat`, etc.) do not satisfy this archive layout and need separate treatment.

## Bitmap decoding: all 2,337 SHAP resources decode exactly

Direct examination confirms a six-byte SHAP header: `u16 height; u16 width; u16 flags`. Define `depth = ((flags >> 12) & 7) + 1`, `method = (flags >> 8) & 15`, and `stride = ceil(width * depth / 8)`. Output size before unpacking pixels is `stride * height`.

Methods observed: 0 raw; 1 run-length horizontal; 2 run-length vertical; 3 LZ horizontal; 4 LZ vertical. For RLE, signed nonnegative control copies `control+1` literals; a negative control repeats the next byte `-control` times. LZ uses a zeroed 1024-byte circular dictionary starting at position958; flags are consumed low bit first, 1 means literal, and 0 means a big-endian 16-bit copy token whose low10 bits select dictionary position and upper6 bits give length minus3. Dictionary copying supports overlapping references. Vertical methods produce columns of bytes: transpose decompressed order into rows using the image height and byte stride. Expand packed pixels most significant bits first.

The disposable decoder consumed the full compressed payload and produced the exact expected output length for **all 2,337** images. Format high bytes and counts: B4 1606; B3 570; B0 60; B1 28; 00 24; B2 21; 04 11; 01 6; F3 6; 02 4; 03 1. This includes monochrome, 4bpp and 8bpp assets. It establishes structural decoding success; frame comparisons must still prove palette choice, placement, masks and animation timing.

[ScummVM DOSBitmap](https://github.com/scummvm/scummvm/blob/master/engines/mohawk/bitmap.cpp#L707-L815) is an additional comparison point, but its unsupported format-bit and compression cases prevent using it unmodified on this corpus.

The decoded `th.dat` SHAP1 is a coherent 320x200 treehouse exterior with fence and pond. Local preview: `testing/output/treehouse/research-resources/th-shap-1.png`. Its palette came from SHPL0. This preview is generated from original resource bytes, not a redraw.

## SHPL palettes and shape grouping

Observed header: `u16 first_shape_id; u16 shape_count; u16 zero; u8 color_count`, followed at byte7 by RGB triplets. All components in the sampled palette are 6-bit values. Mapping `component * 255 // 63` gives a plausible preview; exact DAC conversion remains to be compared against captured emulator output.

Across 160 SHPL resources, 157 are 103 bytes with 16 colors and 48 trailing bytes; two are 199 bytes with 64 colors and no trailing bytes; one is 247 bytes with 80 colors and no trailing bytes. The trailing48 bytes plausibly contain alternate display palette data, based on related format definitions, but their meaning in Treehouse remains unverified. Preserve them. Shape-group semantics are inferred from IDs, not yet confirmed by executable traces.

Concrete TH examples: SHPL0 payload offset23558, length103, starts `(first=1,count=3,zero=0,colors=16)`; SHPL4 starts `(5,1,0,16)`; SHPL6 starts `(7,11,0,16)`. TH64 has corresponding 64-color art.

## Text, font, and unresolved resources

STRL normally contains a one-byte string count followed by NUL-terminated strings. **175 of176** resources exactly satisfy count and termination. TH STRL500 at payload offset `0x21934`, length63, declares12 and contains month labels. TH STRL1001 through1012 contain historical calendar facts; modules STRL resources contain activity instructions and facts.

Exception: MODULES STRL200, payload offset137625 (`0x21999`), declares25 but contains24 terminated strings. All archive-level bounds and checksum checks still pass. A text extractor should retain the declared count and actual strings and report this anomaly without discarding the resource.

TH FONT1 starts at `0x20B51`, length3554, and contains a plausible offset table followed by glyph data. Its glyph format has not been fully decoded. TH contains26 TXT4 blocks whose content is not plaintext; no claim is made about their compression or semantics. SCR/PSL semantics, sound codecs, CURS layout, and runtime uses of the all-zero tag remain unresolved. SONG resources have a short header and repeated pairs (all observed sizes equal `5 + 2 * payload[1]`), but note meanings and playback timing need executable evidence.

## Member SHA-256 identities

```text
boy.dat      608b323e727fb12a40497cdc534f46d2636422e65348c10f36f9ed02afc2c1e9
girl.dat     3ba60eeecf01198ef1c64846499af15db747b3f2561fb8bdde59c15dd485fbd7
digisnd.dat  aef523959048a2baa69e972b4f8fd79ee5aaeda8a249a6eae4e788e8e7fe6f2b
ibm_snd.dat  901dda52f0512614a355ab2b3e47ce283cad1fe674cab4a214b9df515aefc3f6
midisnd.dat  7ac9ba27689a64390299b7b2c9da0942d896f96a31f2991e8a98fc91c8ff9cae
modules.dat  3060c4327b5c5bffdda9382ff4a5effeacce1c8be7c921dc686604820dd86b96
mt32snd.dat  82e6f881a1ea2019f05a71ae5a7b856029a42eb026645052b17a238e5ce89407
th.dat       46c53d7af487d1b5c8639634fb17f7bd876e0dc6877022614f29e7d36f885f9c
th64.dat     795fc657e4fe890c9b44143282c8677f074c416f3866dce5d504b794a4a18178
voices.dat   3cf6fec1c1e680c0534a2d73a7b3a8fa91b2a9ea51e441f7a255cec56d485c9d
```

These hashes and the corpus observations above were computed directly from the primary ZIP, not taken from third-party descriptions.
