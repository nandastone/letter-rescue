# Eleventh slice: original AdLib driver and complete music loop

The clone now has independently implemented CMF sequencing and AdLib register
generation. Both Python and Godot match the native driver from one initial
checkpoint through a song restart. These modules are not yet connected to
the gameplay clock or audible runtime playback. Loading duration remains
outside the gameplay comparison requirement.

## Native evidence

| Recording | IRQ ticks | MIDI events | Register writes | Result |
|---|---:|---:|---:|---|
| WR1.4 startup | 363 | 69 | 200 | Exact events, register order/values and state |
| WR1.5 short gameplay | 561 | 90 | 205 | Exact events, register order/values and state |
| WR1.5 through restart | 9,641 | 2,665 | 6,498 | Exact events, register order/values and state |

The short gameplay recording overlaps the long recording; these are not
independent totals. Every comparison starts from one observed state and then
advances the models. No later native state, voice assignment, event or register
value is injected into either implementation.

The startup fixture was extended from 359 to 363 ticks in the twelfth slice:
the improved observer also records the four final event-free driver calls
during the loader transition. The earlier fixture is preserved under
`testing/output/wr1_opl_startup_359_ticks.json`.

Maintained fixtures:

- `testing/fixtures/wr1_opl_startup_ticks.json`
- `testing/fixtures/wr1_opl_ticks.json`
- `testing/fixtures/wr1_opl_loop_ticks.json.gz` (deterministic gzip of native JSON)

Each fixture records source BSV, executable, core, trace and CMF hashes.
`tools/prepare_wr1_opl.py` checks trace integrity, CPU configuration, complete
IRQ/call pairs and requested boundaries. A missing OPL return is a hard error.

Raw captures remain under `testing/output`: `wr1_opl_native.json/.jsonl` and
`wr1_music_loop_complete_native.json/.jsonl`. The earlier long capture
`wr1_music_loop_native.json/.jsonl` lacks music-state fields during cached
reloads, so it is retained as a diagnostic rather than used for fixture states.

## Recovered logic

`scripts/wr1_opl.gd` and `tools/wr1_opl_reference.py` implement the embedded
driver's MIDI dispatcher and note handlers, EXE1ec59..1f26a. They reproduce
channel/program voice assignment, silent-voice reuse, note release, instrument
operator writes, pitch calculation, volume scaling and rhythm-bit toggling.

The immutable frequency, operator, drum and instrument tables come directly
from the supported executable through `tools/extract_wr1_audio_driver.py`.
The CMF's 16-byte instrument records supply the 11 bytes used by the driver.
The native percussion setup table stores value/register pairs, which the
driver swaps before writing them; the extractor preserves the resulting order.

At repeat, EXE1f1e9 resets the nine instruments and voice allocations but
preserves channel volumes and percussion type. The CMF sequencer now signals
that restart separately from MIDI events. The measured restart occurs at
post-checkpoint IRQ 9,282, native worker call 7,336. That IRQ contains a final
drum event plus 100 reset writes: **101 writes, about 22.076 ms** in total.

Control messages 104/105 and unusual all-notes-off traversal still need broader
native coverage. The latter explicitly reports unsupported use. Other modes
(PC speaker and external MIDI) are not implemented by this AdLib module.

## Timing findings

The observer now records MIDI dispatcher entry/return at driver CS:58f1/599f
and OPL writer entry/return at CS:579e/57c3. It recognizes the driver through
the live interrupt vector and tick-function fingerprint, preserving WR1's
separate data segment.

Across 6,498 measured OPL calls, entry-to-return cost ranges from 5,774 to
5,896 emulated cycles. The modal cost is **5,893 cycles** (4,618 calls). The
return instruction itself is outside these boundaries. DOSBox's IO-delay
clamping at CPU-slice boundaries explains why a single fixed cost is insufficient.
Occasional costs above the minimum-loop estimate remain to be accounted for.

The first medium gameplay admission error includes three register writes.
The complete driver call costs 17,824 cycles; its individual OPL intervals
cost 5,839, 5,893 and 5,815 cycles. The remaining 277 cycles cover the dispatcher,
sequencer and call/return work. These are measurements, not constants inserted
into the gameplay clock.

The existing 122 one-frame admission residuals remain recorded. Gameplay timing
has not been declared fixed by this slice.

## Faster continuous captures

`capture_wr1_replay.py --sample-frames ... --run-between-samples` runs normally
between sparse samples, then pauses and steps to each exact requested counter.
Instruction tracing remains continuous. It rejects overshot counters.

Comparing the two 7,600-frame long captures preserves all **6,504 gameplay
instruction observations**, **14,691 OPL observations** and **5,734 MIDI call
observations** (including their launch calls). This validates the faster capture
path against the fully frame-stepped recording rather than assuming equivalence.

## Listening previews

The GPL-2.0-or-later offline helper `tools/wr1_opl_render.cpp` links the existing
DOSBox Pure DBOPL source. It does not add emulator code to the Godot runtime.
Build it using `tools/build_wr1_opl_renderer.py` against the pinned source checkout.
`tools/render_wr1_music.py` feeds independently reconstructed register events to
that renderer and writes WAV, event stream and provenance metadata.

Generated research previews:

- `testing/output/wr1_4_reconstructed.wav` — 93.52 seconds
- `testing/output/wr1_5_reconstructed.wav` — 97.87 seconds
- `testing/output/wr1_6_reconstructed.wav` — 65.01 seconds

Durations include a one-second release tail. All are non-silent and remain
within signed 16-bit range without clipping. These previews use ideal IRQ
spacing: intra-IRQ CPU work and native mixer resampling are not yet reproduced.
They are not claims of exact native PCM parity, and WR1.6's complete register
sequence has not yet been captured independently.

## Validation and next work

The five Python AdLib tests pass, including incorrect pitch-table rejection and
missing-call rejection. Godot matches all three retained fixtures. The earlier
487-tick sequencer fixture remains unchanged and still passes its 3,896 checks.
The full Python suite passes **63 tests in 143.655 seconds**; `git diff --check`
also passes. Logs are `testing/output/wr1_eleventh_python_tests.log`,
`wr1_opl_python_tests.log`, `wr1_opl_godot_tests.log` and
`wr1_eleventh_music_tests.log`.

An additional timing observation: ordinary event-free driver ticks usually cost
68 cycles (70 on the beat-counter rollover), with rare lower measured costs.
The CPU's time-slice accounting therefore needs investigation even outside the
OPL IO loop; fitting only a per-register delay would leave part of the problem.

Next, derive dispatcher/sequencer instruction work and IO-slice effects from
the recovered code, connect music service completion to the main-loop gate,
and rerun the retained gameplay admission comparisons. Native PCM capture,
original sound effects, runtime music integration, remaining later-level routes,
menus and the ending remain open.
