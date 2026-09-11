# Gameplay IRQ and music-driver latency

The tenth-pass one-frame admission residual is a measured execution delay,
not just uncertainty in the synchronized starting clock.

## Observation at the first medium residual

Source: `testing/output/wr1_irq_latency_native.jsonl`, from the medium drip
replay. The observation core reports the PIT epoch and four IRQ instruction
boundaries, without changing guest instructions, registers or timer state.

| Event | Emulated time (ms) | Frontend worker |
|---|---:|---:|
| Before EXE 4352, game timer is 7 |13102.456999997|914|
| Music driver call at 43fa |Within that IRQ|914|
| Music driver duration |0.660148144|Spans the handoff|
| IRQ body duration through 442a |0.661370372|Spans the handoff|
| Frontend call 915, game timer is already 8 |13103.000074029|Before next worker|
| Main admission at 37a4 / CS 0096:0444 |13103.119703703|915|

The main admission file address is **37a4** (`0x2a00 + 0x0096*16 + 0x0444`).
The clone's ideal IRQ gate admits this update one frontend frame earlier.
Changing the initial clock phase cannot account for variable driver work.

Across 489 post-load IRQs in this capture, driver calls range from 0.002148 ms
to 3.094963 ms; 58 take more than 0.1 ms. The maximum measured BIOS-tail cost is
0.001741 ms. The music driver is therefore the dominant variable work inside
these interrupts. Other emulated rendering/CPU work and video delivery still
need their own accounting; this is not a universal timing fix by itself.

The instrumented core preserves all 468 original instruction observations in
the common capture prefix: instruction address, admission worker, player,
score, enemies, RNG and drips agree with the prior observation core.

## Recovered interrupt handler

The handler is **CS 0172:0224**, file 4344. The four hooks are CS offsets
0232, 02d8, 02dc, 030a (file 4352, 43f8, 43fc, 442a). It is a separate code segment
from the gameplay main loop.

- Save registers, set DS and increment the game timer at 4352.
- Advance the PC-speaker sound sequence if active.
- Execute interrupt 63h, AH 2fh at 43fa.
- Decrement the original BIOS chaining counter. Occasionally call the saved
  BIOS handler; otherwise acknowledge IRQ0 directly.
- Restore registers and IRET.

IRQ0 runs at `12428 / 1193182` seconds. DOSBox Pure stores the corresponding
millisecond period as a float. The direct PIT probe reads `pit[0].start` and
`pit[0].delay` without latching or writing PIT ports. Its initial phase is
validated against the existing idle-prefix constraints before use by a replay.

## Embedded music driver

WR1.4, WR1.5 and WR1.6 each begin with **CTMF**, version 0101, and contain the
game's music. The driver is embedded in WR1.EXE, not an external DOS program.

In this native run, interrupt 63h points to 1860:50d9. With the observed DS 23fd
and executable relocation, that resolves to **file 1e659**, driver code/data
base **file 19580**. This entry saves registers, switches DS to CS, selects a
function by AH from a table at CS 4a22, and calls it. AH 2f therefore uses the
entry at CS 4a80. That table is initially zero in the file and is populated at
runtime, so a static table lookup alone does not identify the tick function.

`tools/wr1_core_trace.cpp` now also records the live AH 2f function pointer in
each IRQ observation. The follow-up capture is
`testing/output/wr1_irq_driver_native.jsonl`. It identifies the live entry as
**CS:60da / file 1f65a**. The disassembly is saved at
`testing/output/wr1_music_tick_disassembly.txt`.

The tick routine checks playing byte CS:0961, increments sub-beat counter 0853
against division 0859, and increments beat 0855 on wrap. It walks track count 0857,
using active words 0861, 32-bit delay values 08a1, stream cursors 0921 and running
status bytes 0962. A delay greater than one decrements; otherwise the routine
consumes MIDI-like events, including running status, until it reads a nonzero
variable-length delay. Dispatch is file 1ee71. Meta FF2F ends a track and FF51
changes tempo; a repeat flag at 0860 can restart the stream. The division,
stream segment 085c, stream start 085e and format byte 085b determine its setup.
These are driver-relative offsets, not the game's DS offsets.

## Independent sequencer verification

`testing/output/wr1_music_state_native.jsonl` records the driver state before
and after IRQ calls, plus the initial frontend handoff. Starting once at
counter 560, both `scripts/wr1_music.gd` and the independent Python reference
`tools/wr1_music_reference.py` match **487 consecutive native IRQ ticks**,
emitting **71 MIDI events**. The correct source is **WR1.5**; trying WR1.4 or
WR1.6 produces 474 mismatching states in either case. No later track state is
injected into either model.

The maintained fixture is `testing/fixtures/wr1_music_ticks.json`. Original
music data is preserved in `assets/audio/original/wr1_4.cmf`, `wr1_5.cmf` and
`wr1_6.cmf`. The Godot test passes 3,896 state checks, and both Python tests pass.
This verifies sequencing for the measured interval, not full song looping or
every MIDI control message. The sequencer is not yet connected to gameplay
audio or the main update gate; synthesis and execution cost remain open.

## Next: OPL writes and their execution work

The event dispatcher is file 1ee71. The OPL register writer is
**file 1ed1e..1ed43**, driver CS:579e..57c3. Register/value arrive in AL/AH.
After writing port 388h, it reads status 100 times. After writing port 389h, it
performs 30 PIT polling iterations, each waiting for a changed counter value.
This explains why even a small number of register writes takes substantial
emulated time.

At the capture's 27,000 cycles/ms, DOSBox Pure charges 26 cycles for an IO read,
19 for an IO write, and an additional 13 for an Adlib status read. These are
integer divisions in `src/hardware/iohandler.cpp` and `adlib.cpp`. They are
clamped by the remaining CPU execution budget, so handoffs can affect the
last access in a time slice. Counting the routine's ordinary instructions
and the minimum loop iterations suggests 5,894 cycles per OPL write before
such clamping. This is a hypothesis for the next native call-boundary probe,
not a runtime timing constant already validated.

The next step is to recover the event handlers' register writes and execution
work, validate them against the native driver, and connect the independently
sequenced events to sound synthesis and IRQ admission timing.

No measured future IRQ schedule has been added to the clone. The existing
timing-residual fixtures remain explicit failing parity observations rather
than compensated frame offsets.

## Completed OPL probe and full-loop verification

The next probe is now implemented. See `testing/wr1_eleventh_slice.md` for
the retained evidence: 9,641 consecutive WR1.5 IRQ ticks through restart,
2,665 independently sequenced MIDI events and 6,498 exact register writes,
plus a separate 363-tick WR1.4 initialization capture. Both Python and Godot
match the native sequencer and voice state throughout.

Measured OPL entry-to-return cost is usually 5,893 cycles, excluding RET.
It ranges from 5,774 to 5,896 in the long recording, so the earlier 5,894-cycle
whole-routine estimate must not be used as a universal timing constant. The
first problematic driver tick is 17,824 cycles overall; its three observed
OPL intervals total 17,547 cycles. There are 277 additional cycles of driver
work, rather than the 142 cycles suggested by assuming three unclamped writes.

The song restart performs 100 reset writes after its final drum write and
takes roughly 22.076 ms. A timing model must also handle driver work longer
than one IRQ period. The gameplay clock still needs that integration.

The twelfth slice now explains all non-IO instruction-accounting differences
for 2,588 native MIDI calls. `testing/wr1_twelfth_slice.md` distinguishes that
verified result from the still-unmodeled OPL wait durations and records the
PIC/VGA events that bound those waits.

The thirteenth slice independently predicts all 6,498 captured OPL waits,
including final PIT/VGA/CPU state. A recovered live-state instruction planner
also predicts all 90 complete MIDI calls in a short capture without supplied
wait durations or recorded instruction paths. See `testing/wr1_thirteenth_slice.md`
for the initialization scope: hardware still starts from a checkpoint at each
MIDI call, so continuous whole-IRQ and level admission remain unverified. The
runtime planner matches original-binary work on 2,588 pre-repeat events, plus
startup and short overlapping recordings. Forty-two additional constructed
source experiments cover uncommon controller and voice branches.

The fourteenth slice now verifies the whole INT 63h service on 561 native
calls, including the 17,824-cycle service crossing the first medium admission
boundary. Both Python and Godot predict its completion and all final hardware
fields from generated work and entry hardware state. The dispatcher uses a
runtime CS:4 flag that differs from its initial file byte; this is now observed
directly. See `testing/wr1_fourteenth_slice.md` for scope and retained evidence.
The extended recording now also matches all 9,281 pre-repeat service completions
and final hardware states. Two IRET-at-millisecond-boundary cases established
that the next-instruction hook observes PIC's next block admission, after its
overshoot loss. Song-repeat timing and outer IRQ/main-loop integration remain
pending.

The fifteenth slice completes the measured WR1.5 repeat path: all 9,641 music
services, including the 596,049-cycle repeat, now match completion time and
modeled hardware/register/music state in Python and Godot. The runtime timer
ownership flag is observed directly, and 12 isolated REP operations verify
their pending-cycle accounting. See `testing/wr1_fifteenth_slice.md`. Outer
IRQ delivery, speaker/BIOS work, and main-loop admission remain separate gaps.

The sixteenth slice completes the measured outer timer body through the
before-IRET hook: all 9,641 bodies match timing and modeled state, including
2,410 BIOS calls and 64 speaker advances. Master-PIC state explains a waiting
keyboard interrupt's budget handoff at EOI and the timer requests left pending
by long music services. See `testing/wr1_sixteenth_slice.md`. Final IRET/delivery
and continuous main-loop waiting/rendering work remain open; the gameplay gate
still uses its earlier approximation.

The seventeenth slice predicts complete idle waits from one checkpoint per
wait, including IRQ entry and return. All 65 waits, 517 timer entries and 24
keyboard entries match in Python and Godot when given the same externally timed
key changes. The 11 initial differences all coincided with omitted button
changes; the recovered IRQ1 handler and controller scheduling account for them
without offsets. Input delivery times are still supplied as guest-cycle replay
inputs, and work inside gameplay updates/rendering remains the next boundary.
See `testing/wr1_seventeenth_slice.md`; this does not yet resolve the older 122
admission-frame residuals or replace the runtime gate.

The eighteenth slice measures the remaining update interval: 64 complete
updates contain 1,050 aligned EGA rectangle copies and 198 masked sprite draws,
together about 90% of renderer time. Shared device lookup and all 129 measured
drawing-page selections now have exact instruction/hardware models in Python
and Godot. Copy and sprite work remain to be recovered; their measured durations
are profiling evidence only. See `testing/wr1_eighteenth_slice.md`.

The nineteenth slice recovers all 1,050 measured aligned EGA rectangle copies,
including their per-call BIOS mode query and row REP work. Python and Godot
match completion, modeled hardware and arguments from entry state alone.
These samples copy between different pages without clipping or an intervening
timer interrupt; broader copy paths and IRQ delivery during graphics remain
open. Masked-sprite work is next. See `testing/wr1_nineteenth_slice.md`.

The twentieth slice recovers all 198 measured masked-sprite draws from their
live image headers and call arguments. Python and Godot match timing and
modeled hardware; pixel values do not select this routine's branches. Coverage
is aligned, four-plane conventional-memory images with no intervening timer
IRQ. Both dominant drawing primitives now have verified work models for the
route; generating their calls and the surrounding renderer/update work remains
open. See `testing/wr1_twentieth_slice.md`.
