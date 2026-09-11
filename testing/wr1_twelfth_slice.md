# Twelfth slice: instruction work and emulator time slices

The non-IO part of the original MIDI driver is now explained by executed
instruction paths plus DOSBox's millisecond accounting. The gameplay clock
has not yet been changed: OPL wait prediction is the next dependency.

## Executed instruction paths

`tools/wr1_driver_cpu.py` is a bounded research interpreter for the supported
WR1 executable's 16-bit MIDI handlers. It uses the actual handler instructions
and one initial voice state, and treats the OPL busy-wait routine separately.
It checks the executable hash and rejects unsupported instructions. It is not
part of the Godot runtime.

The interpreter matches all register output for:

- 90 MIDI events in the short WR1.5 capture;
- 69 initialization events in WR1.4;
- 2,588 WR1.5 events from the post-load checkpoint to immediately before repeat.

These intervals overlap. On the long interval, simple instruction counts match
2,578 of the 2,588 native non-OPL costs. The ten differences are losses of
1, 2, 7, 9, 21 or 26 cycles, not different note or voice behavior.

## Why cycles disappear

DOSBox's dynamic core accounts instructions at block exits. A block can finish
slightly past its cycle budget. `PIC_RunQueue` preserves that debt within a
millisecond, but `TIMER_AddTick` replaces the remaining budget with the next
millisecond's 27,000 cycles. The overshoot therefore disappears from elapsed
emulated time.

`account_blocks` models that behavior using the driver's actual control-flow
boundaries and 32-instruction maximum block length. All ten losses are derived
from the instruction path and millisecond phase, without event-specific offsets.

One boundary case ends the OPL routine exactly at the millisecond boundary.
Its four POP instructions are still pending in the dynamic block. RET adds
one more cycle, and that cycle is discarded when the next millisecond begins.
Accounting for that pending epilogue resolves the final one-cycle difference.

**All 2,588 measured MIDI-call endpoints now match when native OPL interval
durations are supplied as opaque work.** This isolates and verifies the
non-IO accounting. It is not yet an independent prediction of whole driver
latency, since the busy-wait durations remain measured inputs to this diagnostic.
No such future durations have been added to gameplay replays or runtime code.

## Retained timing evidence

`prepare_wr1_opl.py` now retains native `event_cycles`, `event_begin_cycles` and
`event_end_cycles` alongside its existing complete call pairs and register
durations. The three music fixtures were regenerated from their hashed traces.

The startup fixture now includes 363 complete IRQ calls, including four final
event-free calls during the loader transition. Its 69 events and 200 register
writes are unchanged. The old 359-tick fixture remains in `testing/output`.

`testing/test_wr1_driver_cpu.py` verifies the instruction accounting against
all three recordings. Set `WR1_EXE` to the original executable to run this
optional original-binary test. Without the original executable it reports a
skip, rather than claiming that the disassembly was tested.

The eight focused Python music/OPL/instruction tests pass in 2.300 seconds;
the Godot register tests pass at 561, 363 and 9,641 ticks. `git diff --check`
passes. Logs are `testing/output/wr1_twelfth_python_tests.log`,
`wr1_driver_cpu_tests.log` and `wr1_twelfth_opl_tests.log`.

## Hardware-event probe

The new PIC probe records CPU budgets while the driver is inside its OPL wait.
`testing/output/wr1_pic_native.json/.jsonl` is the native evidence; the matching
link map is `testing/output/dosbox-pure-trace/wr1_trace.map`.

The PIC callback limiting a slice is identified by its code offset relative to
`PIC_RunQueue`, then resolved through that build's link map. After the initial
playable checkpoint, the observed limiting callbacks are:

- `VGA_DrawPart`
- `VGA_VerticalTimer`
- `VGA_VertInterrupt`
- `VGA_DisplayStartLatch`
- `VGA_PanningLatch`

For the first medium admission error, these display callbacks split the driver
at approximately 13102.526, 13102.531, 13102.908 and 13102.971 ms, followed by
the next millisecond. They shorten individual IO delays through the core's
remaining-budget clamp. A model with only the music IRQ period misses these
display events.

The probe preserves all 491 comparable gameplay instruction observations against
the contemporary complete-loop capture, including their launch calls, RNG and
actors. Older short captures have a different initial RNG/actor configuration;
startup seeding remains a separate open question. No claim is made that all
captures share the same unmeasured boot seed.

## Next dependency

Reproduce the OPL routine's IO delays and its PIT polling from source. A word
read at port 40h reads both PIT channel 0 and channel 1, through
`IO_ReadDefault`; channel 1 is registered too. Therefore the comparison value
is not a simple current 16-bit channel-0 count. Initial PIT latch/read state and
VGA event phase will be needed to predict the waits from one checkpoint.

Once those waits are independently verified, port the execution-cost model to
the runtime and connect service completion to main-loop admission. Existing
gameplay residuals, native PCM validation, runtime audio, remaining levels,
original menus and the ending remain open.
