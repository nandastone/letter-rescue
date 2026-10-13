# Treehouse DOS executable and control resources

Date: 2026-09-25. Static research only: the executable was not run by these probes. Existing parent-produced boot RAM was used as comparison evidence. All code addresses below are offsets within the unpacked main image before DOS load relocation unless explicitly identified as file offsets or segment:offset addresses.

## Primary artifacts

Source ZIP: `testing/output/treehouse/source/The_Treehouse_1991.zip`, SHA-1 `9b1f060e072865657ac6949203b4b2b891639b1e`. TREEHSE.EXE SHA-256: `16c5623174f0e97ee928790fd6d3e638d5724f3fb2a7794c7d3a48274f1d82d9`. Existing capture: `testing/output/treehouse/boot-1800/boot.ram-0`, SHA-256 `8b4674d9956db9307138e967cf3582d81b86aa4c339863f1b35266e122b7be28`.

Scratch artifacts: `testing/output/treehouse/research-resources/treehse.exe`, `executable_probe.py`, `unpacked.bin`, `unpacked-reloc22.bin`, `scr-disassembly.json`. Run `python testing/output/treehouse/research-resources/executable_probe.py` to reproduce both unpacking and all356 script parses; the earlier `unpack_probe.py` is superseded. `unpacked.bin` SHA-256 is `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f`. The probe applies only the original unpacker's byte transform; no executable instructions are emulated or launched.

## Packing and original entry point

The 273408-byte executable has MZ fields: final-page bytes17, page count335, relocation count0, header paragraphs32, initial CS10463 (`0x28DF`), initial IP18 (`0x12`). The main declared executable ends at file offset `0x29C11` (171025). Packed entry code begins at file offset `0x29002`.

The stub implements backward run-length expansion, then applies its own relocation table, then restores the original stack and far-jumps to the saved entry point. Stub file offset `0x29107` begins the ASCII diagnostic `Packed file is corrupt`. This is consistent with EXEPACK-style packing. The exact packer version is not identified.

The 18-byte header at file `0x28FF0` has words:

```text
0D63 0D51 0000 0C21 0800 37E0 373A 0001 4252
```

Observed meanings from the stub: original IP `0x0D63`, original CS `0x0D51`; scratch load base word; stub+relocation bytes `0x0C21`; original SP `0x0800`; original SS `0x37E0`; expanded image paragraphs `0x373A`; source skip paragraphs1; final signature word `0x4252`.

Static unpack algorithm derived from entry disassembly:

1. Allocate `0x373A * 16 = 226208` bytes. Source points immediately before file `0x28FF0`, skipping trailing `0xFF` padding. Destination starts at the last expanded byte.
2. Read a backwards control packet: control byte, preceding little-endian count word, then source data. Controls masked with `0xFE` equal `0xB0` (repeat preceding byte) or `0xB2` (copy preceding count bytes). Write backwards into destination. Low bit1 marks final packet.
3. This file has386 packets, leaving source index `0xD719` and destination index `0xD519`. Copy the unchanged image prefix from file `[0x200,0xD71A)` into output `[0,0xD51A)`.
4. Relocation list starts at file `0x2911D` (stub header + `0x12D`). Read16 groups; each is a little-endian count followed by that many u16 offsets. Group number selects a64KiB block. There are1386 relocation targets, and the list ends exactly at `0x29C11`. Add the DOS load segment to each target word when producing a relocated memory image.

The matching image begins at raw `.ram-0` dump offset `0x220`; this was initially misidentified as a physical load base. Subsequent input research established a synthetic memory-map shift of `0x1860`, so the actual guest load base is physical `0x1A80` (segment `0x1A8`). See the correction in [the animation note](treehouse_animation_research.md). Relocating the main image by segment `0x22` makes **221795 of226208 bytes equal** to boot RAM at that base. Differences remain and are expected to include runtime data and code patching; they have not been classified. This comparison supports unpacking and address mapping, but is not a full runtime equivalence check.

Original entry `0D51:0D63` maps to unpacked offset `0xE273`. It begins with DOS version and interrupt setup; this is startup/runtime machinery, not gameplay entry. Its data segment immediate is `0x321D` before load relocation, so the main data segment starts at image offset `0x321D0`.

## Overlay structure

Five further MZ headers occur at aligned file offsets after the main executable. Their declared sizes and relocation tables are internally bounded:

| File offset | Overlay ID | Declared bytes | Header bytes | Relocations | Declared end |
|---|---:|---:|---:|---:|---|
| 0x29E00 | 1 | 42798 | 3584 | 842 | 0x3452E |
| 0x34600 | 2 | 17757 | 1536 | 364 | 0x38B5D |
| 0x38C00 | 3 | 17454 | 2048 | 379 | 0x3D02E |
| 0x3D200 | 4 | 21331 | 2048 | 405 | 0x42553 |
| 0x42600 | 5 | 1536 | 512 | 38 | 0x42C00 |

The final end matches physical EOF. Main image contains overlay-loader diagnostics, including `Overlay not found` at packed-file offset `0x284FE` and an overlay stack overflow message. The startup routine at the original entry reads DOS program-path/environment information. This establishes an overlay-managed program; overlay functions have not yet been mapped to activities or assigned runtime segment addresses. Do not concatenate overlay bodies and treat them as one flat instruction address space.

## Resource loader footholds

The main resident segment is `0D51`. Two useful far-call entry points are `0D51:7668` (unpacked offset `0x14B78`, resource handle lookup/load) and `0D51:7688` (`0x14B98`, resource pointer load). Both take a u16 ID plus a four-byte type tag. At `0x14B78`, the callee loads the tag into DX:AX and ID into CX and calls `0x150D9`. Names here describe behavior inferred from callers; they are not original symbols.

Useful call sites:

- `0x41DE`: constructs tag `0x00534352` (NUL-SCR), ID is a sum of two caller arguments; invokes pointer loader and retains a far pointer.
- `0x4340`: constructs `0x0050534C` (NUL-PSL), same summed ID; invokes handle loader.
- `0x641F`: constructs `0x5348504C` (SHPL), invokes handle loader.
- `0x1B894`: constructs `0x53484150` (SHAP), ID comes from group first-shape word plus requested shape index minus1.

These establish shared resource access paths suitable for future debugger hooks. Raw dump offsets add `0x220`; guest physical addresses add `0x1A80` in the examined run. Later runs should discover and record their load base and the core memory-map translation.

## PSL: sound preload lists, confirmed

All195 NUL-PSL payloads satisfy `u16 count; count * u16 sound_ids`, with exact payload length `2 + 2 * count`.

Evidence from code: at `0x4363` the consumer reads a u16 count; loop `0x4371` through `0x43A1` reads successive u16 IDs from payload+2 and calls `0D51:E4AA` (unpacked `0x1B9BA`). That routine builds NUL-SND and calls the resource loader. Thus these are sound reference/preload lists, not general program bytecode.

Example: TH PSL800 is `03 00 16 27 15 27 17 27`, referencing sound IDs10006,10005,10007. TH PSL1000 references10008. The initial sound-loading routine may perform additional decoding or caching; its full semantics remain untraced.

## SCR: bounded animation instruction streams, structurally confirmed

All356 NUL-SCR payloads have an eight-byte header followed by variable-size instructions ending in byte00. The header consists of four little-endian 16-bit coordinates. Code `0x4229` onward manipulates words0/4 together and words2/6 together to reposition their bounds. This strongly supports a rectangle; axis order and edge inclusivity are not yet verified against rendering.

At `0xC449`, a consumer points to payload+8 and scans instructions. It classifies byte opcodes using two original executable tables:

- Class values: data-segment `0x0ABE`, unpacked offset `0x32C8E`.
- Operand byte lengths: data-segment `0x0AD0`, unpacked offset `0x32CA0`.

| Opcode class | Operand bytes | Match rule |
|---|---:|---|
| 00 | 0 | Exact; terminates stream |
| 01 | 4 | Exact |
| 02, 03, 04, 05 | 2 | Exact |
| 06 | 1 | Exact |
| 07 | 0 | Exact |
| 10..13 | 2 | Mask opcode with FC |
| 14..17 | 4 | Mask opcode with FC |
| 90..9F, A0..AF, B0..BF, C0..CF | 4 | Mask opcode with F0 |
| D0..DF, E0..EF | 8 | Mask opcode with F0 |
| F0..FF | 1 | Mask opcode with F0 |

Applying these tables consumes exactly every resource, with its final00 exactly at the last byte: **356/356 successes**. Unused classes in this release still exist in the executable table; do not infer they occur in gameplay.

For Cx instructions, the scanner reads u16 values at opcode+1 and+3 and marks all shapes in that inclusive range as referenced (`0xC4DC` through `0xC528`). This supplies a reliable first interpretation: Cx carries a shape range. The low nibble plausibly selects an animation slot because C0 throughC5 occur alongside corresponding B0 throughB5 and90 through95, but slot semantics remain a hypothesis. TH SCR70 starts with bounds `(0,0,23,27)` and cycles C0 ranges `(4,4),(3,3),(2,2),(1,1),(2,2)` with intervening B0 and01 commands.

A common sequence is `07 03 <u16 sound_id>`; the same sound IDs occur in matching PSL entries. The structural parser distinguishes07 (no operands) then03 (two operands). Calling03 a sound command is a strong data-level hypothesis, not yet established through its runtime dispatch handler. Likewise01's two u16 operands may encode timing/repetition, but their meaning must be traced before implementation.

## Next bounded work

Implement read-only SCR disassembly using the original opcode size table, annotate shape ranges and candidate sound references, and preserve raw operands. Find the runtime interpreter handling01,03,Bx,Cx and compare its cursor/timer changes against frame captures. Map overlay IDs to modules by following overlay-manager call sites and archive-open strings. Keep behavioral claims separate from the now well-supported resource layouts.


