# Treehouse SCR animation interpreter research

Date: 2026-09-25. Static analysis of the original unpacked DOS executable and an existing boot RAM capture. No new execution was performed in this slice. The primary artifact identities and unpacking procedure are in [the executable note](treehouse_executable_research.md). Addresses below are offsets in its226208-byte unpacked image, before DOS load relocation; the main code segment starts at image offset0, the resident support segment at0xD510, and the data segment at0x321D0.

## Runtime interpreter located

`0xBDA0` is the actual SCR interpreter, distinct from the scanner at0xC39D. It receives an animation-state pointer, installs it as current drawing context, fetches the far instruction pointer at state+0x4E, and dispatches on the opcode. Opcodes0..7 use the jump table at0xC376; remaining classes dispatch at0xBFD4 and0xC320. Configuring a slot continues interpretation within the same call; wait, timing, sound, flush and termination handlers return to the caller. The caller at0x4855 repeatedly invokes the interpreter until its return value signals completion, while also processing application conditions.

Evidence files: `testing/output/treehouse/research-resources/unpacked.bin`, `main-disassembly.txt`, `scr-disassembly.json`. The linear disassembly is a browsing aid, not a complete code map: inline jump tables and overlay call encodings may be misdecoded as instructions. The addresses and handlers below were read from valid control-flow boundaries.

## Clock source is approximately60 ticks per second

Startup at0x11E loads60 and passes it to resident entry0D51:62EA (unpacked0x137FA). The support routine computes a PIT divisor using data constant0x001234DD (1193181) and installs the interrupt handler at0x13957. That handler increments the32-bit little-endian counter at DS:201E on each interrupt (0x13962/0x13968).

Existing boot RAM has requested frequency60 at DS:2014 and installed divisor0x4DAE (19886) at DS:202E. Timer setup at0x13897 writes mode0x36 to port43 and the divisor bytes to port40. The resulting nominal rate is1193181/19886, approximately60.002 ticks/second. Exact emulated timing still depends on the emulator's PIT model. Do not equate this counter with video callbacks or wall-clock milliseconds.

## State structure established by accesses

The animation state is allocated and zeroed by0xC39D. The script rectangle is copied into state+0x3E; instruction pointer becomes payload+8 at0xC6C2. Sixteen slot structures begin at state+0x78 with stride0x22.

| State offset | Interpretation | Evidence |
|---|---|---|
| +3E,+40,+42,+44 | top,left,bottom,right bounds | Header copy0xC66C; renderer uses width/height axes |
| +46..+4D | Accumulated dirty rectangle |0xCC1E unions sprite bounds here |
| +4E/+50 | Current far SCR pointer |0xBDBA fetch;0xC6CE initialization |
| +52 | Repetition count/shared opcode working state |01 handler0xBE3A; also reused by02/06 |
| +56 | Suppress next redraw flag |07 sets; frame update clears |
| +58 | Number of frame-update calls |0xC796 increments |
| +5A | Delay in timer ticks |01 writes operand2 |
| +5C/+5E | Last frame-update tick, u32 |0xC799..0xC7A6 |
| +60..+6F | Four optional far callbacks |10..13 handler |
| +70..+77 | Four loop counters |14..17 handler |
| +78.. | Sixteen34-byte slots | Slot index calculation0xC0AF |
| +29A | Number of shape entries | Creator0xC570 |
| +29C.. | Shape handles; slot shape1 indexes first entry | Renderer0xCBE6..0xCBF4 |

Slot fields:

| Slot offset | Interpretation |
|---|---|
| +00 | Current group-relative shape index;0 means disabled |
| +02,+04 | Inclusive start/end shape indices |
| +06 | Flags: low nibble draw mode; other fields described below |
| +08 | Motion update counter, byte |
| +09 | Shape update counter, byte |
| +0A/+0C | X as signed16.16, low word/high word |
| +0E/+10 | Y as signed16.16 |
| +12/+14,+16/+18 | X/Y velocity, signed16.16 |
| +1A/+1C,+1E/+20 | X/Y acceleration, signed16.16 |

Slot reset at0xCCF2 zeroes34 bytes, sets flags2, and initializes both positions to0x80000000. The renderer skips shape0. Shape handles are resolved from SHPL first ID plus relative index minus1 (resource loader evidence in the previous note).

## Instructions recovered from runtime handlers

The low nibble of9x..Fx is definitively a slot index0..15. Operand words are little endian. Position values below are interpreted as signed16-bit values promoted into the high word of16.16 storage; preserve original16/32-bit wraparound.

| Opcode | Proven behavior | Handler |
|---|---|---|
| 00 | Return completed once `now >= last_update + delay`; otherwise return pending |0xBDCE |
| 01 | Update frame when due; operand1 controls repeat count; operand2 establishes delay ticks |0xBE03 |
| 03 | When due, if global sound-enable DS:5822 is nonzero, load/play operand sound ID; advance3 and return |0xBEFA |
| 07 | Draw current scene immediately, set suppress-next-redraw flag, advance1 and return |0xBFBD |
| 9n | `flags = (flags & mask16) | value16`; reset cadence counters when cadence fields change |0xC0D5 |
| An | Add `(dx<<16,dy<<16)` to slot position, marking bounds before/after |0xC130 |
| Bn | Assign `(x<<16,y<<16)` to slot position, marking bounds before/after |0xC170 |
| Cn | Set current/start to operand1 and end to operand2; start0 resets/disables slot; mark bounds before/after |0xC1B0 |
| Dn | Assign two32-bit velocity fields from8 operand bytes |0xC1FC |
| En | Assign two32-bit acceleration fields from8 operand bytes |0xC22E |

03's sound target is resident0D51:E5E2 (image0x1BAF2); this routine calls the NUL-SND loader and then the sound-start path, resolving the earlier sound-opcode hypothesis.

The draw routine at0xCBD2 resolves the current shape handle, passes integer X from slot+0C and integer Y from slot+10 plus flags&15 to the active graphics function via resident0D51:8272. In existing boot RAM that function dispatch points at resident offsetA112 (image0x17622), whose clipping reads the decoded shape width and height. Thus X/Y order is established. For the active VGA renderer, mode10 is confirmed as a zero-transparent copy: comparison at0x176F3 branches through0x1775C to the pixel loop0x177A6, which preserves destination for source byte0 and copies each nonzero source byte. This is palette-index transparency, not alpha blending. Other display-mode drivers remain unverified.

## Exact01 scheduling order

The order is significant: frame update happens **before** the instruction's delay is loaded on its first encounter. Pseudocode names replace offsets only; arithmetic follows the observed unsigned32-bit comparison and16-bit counters.

```text
step_01(state, count_operand, delay_operand, now):
    if now < u32(state.last_update_tick + state.delay_ticks):
        return pending
    frame_update(state, now)
    global_completed_frame_updates += 1
    if state.repeat_count == 0:
        state.repeat_count = count_operand
        state.delay_ticks = delay_operand
    state.repeat_count = u16(state.repeat_count - 1)
    if state.repeat_count == 0:
        state.script_pointer += 5
    return pending
```

`frame_update` at0xC78A increments state+58 and stores current tick in+5C. Unless suppression+56 is set, it calls scene redraw0xC9ED. It clears suppression, transfers the dirty region to the parent drawing context, clears that rectangle, then advances shape/motion state for the next frame. This means the displayed image reflects slot state **before** the automatic shape and velocity updates.

`draw_scene` restores background data or clears the scene area, then draws the16 slots in ascending slot order (0xCA4D..0xCA74). It also handles application overlays; those branches are not reproduced here. The main interpreter loops straight through9n/An/Bn/Cn/Dn/En without waiting, then yields on01/03/07. Timer values may change between separate interpreter calls.

## Automatic slot updates after each displayed frame

For an active slot whose start differs from end, the old shape-counter byte is compared to flags bits8..11. If old counter is at least that threshold, the counter resets and the shape advances. Bit12 selects reverse direction: clear means+1, set means-1. Bit13 selects bounce instead of wrap. In bounce mode, passing below start sets current=start+1 and clears reverse; passing above end sets current=end-1 and sets reverse. Without bounce, out-of-range values wrap to the opposite bound. These branches are at0xC844..0xC937.

The old motion-counter byte is compared to flags bits4..7. When due, the counter resets, position adds velocity, and velocity adds acceleration (0xC93A..0xC9D9). Both counters increment before comparison, but compare the previous byte value; implement this carefully. Dirty bounds are marked around shape/position changes.

## Small animation with a deterministic semantic trace

TH SCR70 pairs with SHPL70, whose first shape is71 and count4. The script consists only of C0, B0,90 and01, then00. Its rectangle is(top0,left0,bottom23,right27). Starting at tickT with a newly zeroed animation state and stepping it frequently enough, the code implies this display schedule:

| Display tick | Relative shape | Archive SHAP ID | X | Y | Draw mode |
|---|---:|---:|---:|---:|---:|
| T |4|74|6|9|10|
| T+8 |3|73|4|5|10|
| T+16 |2|72|2|3|10|
| T+24 |1|71|0|0|10|
| T+32 |2|72|2|3|10|

Completion can first be reported atT+40 because00 uses the last update plus the retained8-tick delay. This is a **static semantic prediction**, not a measured frame match. The exact tickT depends on when the animation enters the interpreter. Configuration commands for the next image may execute before its due time; this is valid because actual scene redraw waits for01.

A minimal faithful implementation can now reproduce this script's instruction/tick/shape/position trace. Pixel agreement additionally requires implementing the proven zero-transparent mode10, palette installation, background restore/dirty rectangle semantics, and the original scene origin. Frame timing agreement requires recording the PIT counter and entry tick alongside video callbacks. These are concrete remaining boundaries, not grounds to substitute guessed behavior.


## Exterior title/start input: character click required

Additional static input investigation used `testing/output/treehouse/enter-treehouse-c/state/title.ram-*` and `after-click.ram-*`. The exterior title is already interactive; Enter/Space are not a universal continue action.

The main event loop calls0x18CD at0x6C5. A nonzero input result triggers hit testing at the current pointer coordinates, stored as `(y,x)` at DS:2064/2066. At0x711 it scans the active rectangle table and dispatches through the index table at0xA62. The initial exterior has9 rectangles. Relevant entries in original data at image0x2E8F0 are:

| Index | Rectangle `(top,left,bottom,right)` | Action |
|---:|---|---|
| 1 |(64,232,184,290)|Tree/door; extra Ctrl gate before character selection |
| 7 |(105,80,184,128)|Select left character/boy |
| 8 |(109,128,188,174)|Select right character/girl |

Coordinates are on the logical320x200 image. Safe ordinary click points are **(x96,y145)** for the boy and **(x149,y145)** for the girl. Rectangle containment uses inclusive top/left and exclusive bottom/right (resident predicate image0x15798).

The jump table maps index1 to0x743 and indexes7/8 directly to0x75D. At0x743, when DS:5692 is zero (no selected character archive), resident0D51:5C52 must return nonzero or the event is ignored. Its body at image0x13162 reads BIOS0040:0017 and tests bit2: this is the Ctrl modifier. Thus clicking the tree before character selection requires Ctrl. **Ordinary clicks on either character bypass that gate.** At0x767, index8 assigns girl=1; other accepted start indexes assign boy=0. The path then opens the chosen character archive and builds the active scene.

Existing after-click capture has pointer `(x250,y150)` and no Ctrl. This falls within tree index1 and explains why the title did not transition. It is not evidence that left mouse input was lost. Confirm the character-click result in the emulator before claiming end-to-end input validation.

## Correction: libretro RAM dump addresses are synthetic

The `.ram-0` artifact is not a direct physical-address-zero memory image. In these captures its length is649120 bytes; `.ram-100000` contains6240 bytes (`0x1860`). The latter begins with plausible interrupt vectors, while `.ram-0` begins with DOS environment/MCB data. The core maps conventional memory after the first6240 bytes at synthetic start0 and moves the low-memory region to synthetic start0x100000.

For these artifacts:

```text
guest physical 0x00000..0x0185F -> .ram-100000 at same byte offset
guest physical 0x01860..0x9FFFF -> .ram-0 at physical_address - 0x1860
```

This is independently corroborated by relocated far-call segment values and pointer targets. The actual executable load segment is0x01A8 (physical0x1A80); its bytes appear at `.ram-0` offset0x220. Main DS is0x33C5 (physical0x33C50); its bytes appear at offset0x323F0. Runtime hotspot-table pointer3037:0000 resolves to guest physical0x30370 and dump offset0x2EB10, exactly matching the table above. The active count is9 after applying this translation. Earlier notes' raw-offset0x220 comparison remains a valid byte comparison, but naming it a physical load base was incorrect. Tools should persist and interpret the core memory-map descriptors rather than infer physical addresses from output filenames.
