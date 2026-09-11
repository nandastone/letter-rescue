# Fourteenth slice: complete music-interrupt timing

The complete INT 63h music service now matches all 9,281 measured completion
times and final hardware states before song repeat, plus the overlapping
561-call short medium-drip recording. Its
sequencer and voice state advance continuously from one initial checkpoint.
The model computes instruction work and hardware waits; neither recorded
instruction paths nor future wait durations are prediction inputs.

Hardware still starts from the observed state at each interrupt entry. This
validates a whole service routine, not yet the continuous gameplay clock.

## Work recovered

`tools/wr1_music_work.py` and `scripts/wr1_music_work.gd` recover the software
interrupt dispatcher, CMF track traversal, counter/delay arithmetic, running
status, event argument reads, MIDI handler calls, and variable-length delays.
They use the static instruction catalogue plus live CMF/music/voice state.
`wr1_hardware` executes the generated work and the independently modeled OPL
waits through IRET, preserving INT/IRET block boundaries.

Some native entry observations are inside an existing dynamic block, with 19
instructions pending. Hardware initialization and execution now preserve those
pending instructions. Assuming a fresh block at every hook would lose this
information. Existing MIDI-call and OPL tests still pass.

## One conditional instruction

The first complete-service model was one cycle short on most calls. The
dispatcher conditionally executes `MOV ES,DX` according to driver byte CS:4.
That byte is zero in the executable file but **one in the running game**.
The second probe records this runtime flag directly; the fixture supplies it
once as initialized dispatcher state. Modeling the conditional instruction
resolves the mismatch without a timing correction constant.

The native captures are retained separately:

- `testing/output/wr1_music_hardware_native.json/.jsonl/.map` — initial probe;
- `testing/output/wr1_music_hardware_complete_native.json/.jsonl/.map` — includes
  the measured dispatcher flag and supplies the maintained fixture.

The preparer verifies capture/trace hashes, fixed CPU configuration, mapped
callbacks, paired interrupt entry/return, and continuity of music and voice
state between calls. `testing/fixtures/wr1_music_hardware.json.gz` contains
561 complete calls and their expected register, music, voice, and hardware
results. Per-call final states are expected outputs, not injected music state.

## The original admission discrepancy

This recording includes the music service that crosses the frontend boundary
at the first medium timing residual. It begins at 13102.457222 ms and ends at
13103.117370 ms, taking **17,824 cycles** and writing three OPL registers.
The model now predicts that full interval, including its final hardware state.
This explains the dominant variable delay; the game's outer IRQ body, BIOS
tail, main-loop execution, and frontend delivery still need integration.

## Validation and remaining work

Seventeen focused Python tests pass in 10.160 seconds. Godot passes 1,418,636
cumulative checks across the 561-call short and 9,281-call pre-repeat recordings.
Earlier hardware checks still pass at
380,296 cumulative checks, and CMF/register tests still match the 561-, 363-,
and 9,641-tick recordings. These intervals overlap. `git diff --check` passes.
Logs are `wr1_fourteenth_python_tests.log`,
`wr1_music_hardware_godot_tests.log`,
`wr1_fourteenth_hardware_godot_tests.log`, and
`wr1_fourteenth_opl_godot_tests.log` under `testing/output`.

The work planner explicitly rejects track-end/repeat and tempo-port programming
until their costs are recovered. The existing sequencer and OPL generator
already match repeat state/register output; this remaining gap concerns their
complete execution time. The full-song hardware capture at
`testing/output/wr1_music_hardware_loop_native` is complete; its retained fixture
contains 9,641 complete INT 63h calls. The verified comparison checks 9,281
services before repeat: completion time, all final hardware fields, register
output, sequencer state, and voice state agree throughout. Its results are
preserved in `wr1_music_hardware_loop_analysis.json` and permanent Python/Godot
regression tests.

The long recording exposed two IRET boundary cases, originally predicted 2 and
6 cycles late. Both services had no OPL writes and exhausted the final CPU
budget of their millisecond. Native observation of the next instruction is
after PIC admits its block, which discards the overshoot. Advancing that block
entry before observing the model's result resolves both cases and matches their
entire final hardware states. No per-case offsets are used.

The next case, index 9,281 at worker 7,336, enters the explicitly unimplemented
song-repeat work path. Disassembly for its reset and CMF initialization is at
`testing/output/wr1_repeat_work_disassembly.txt`. REP string instruction charging
and the driver's conditional PIT programming require additional accounting.

The 122 recorded gameplay admission residuals remain open. The gameplay gate
has not yet changed. Complete IRQ timing from one playable-level checkpoint,
runtime audio/PCM validation, remaining gameplay routes and levels, original
menus, and the ending remain part of the active goal.
