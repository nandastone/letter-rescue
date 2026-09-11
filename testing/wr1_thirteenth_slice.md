# Thirteenth slice: independently predicted hardware waits

The OPL busy waits can now be predicted from their entry hardware state, rather
than supplied as measured durations. Python and Godot agree with every duration
and final hardware state in 6,498 calls spanning the WR1.5 song and its repeat.
These are isolated routine experiments, with a native checkpoint at each call;
they are not yet a continuous prediction of an entire level from one checkpoint.

## Recovered hardware behavior

`wr1_hardware_reference.py` and `wr1_hardware.gd` model the fixed 27,000-cycle
DOSBox configuration, deferred dynamic-block instruction accounting, millisecond
overshoot loss, IO budget clamps, PIT channels 0 and 1, and the VGA event queue.
Queue scheduling preserves the original float32 rounding and callback origin.
Unknown callbacks or unsupported PIT modes fail explicitly.

The word read at port 40h combines one byte from each of two PIT channels.
Channel 0 alternates low/high latch reads; channel 1 supplies its own LSB. One
of the 6,498 observed writes needs an extra polling iteration, and the model
predicts it from the latch and timer phase. Its 5,903-cycle cost is not a fitted
constant. The queue includes display callbacks and pending keyboard transfer;
hardware interrupt delivery remains blocked inside the current handler.

The model also predicts all 90 complete MIDI-call endpoints and final hardware
states in the short capture. Initially this used paths derived by the bounded
original-binary interpreter; it now uses the live-state work planner described
below. This combined experiment supplies no recorded instruction paths or OPL
wait durations to the model. Voice state persists across MIDI events; hardware
state is still initialized separately at each MIDI entry.

## Runtime instruction-work planner

`scripts/legacy/wr1_driver_work.gd` and `tools/wr1_driver_work.py` recover the handler's
control flow using current voice, channel, controller, and note state. They do
not interpret the original binary. `driver_work.json` contains only static
instruction addresses, mnemonics, and following addresses; no operands, guest
bytes, or recorded event paths. The extraction tool verifies the supported
executable hash. This catalogue preserves actual block boundaries while the
readable planner chooses which spans execute.

Both planners match every instruction and its address for 90 short-sequence
events, 69 startup events, and 2,588 pre-repeat song events. The original-binary
interpreter independently derives these paths, and its register output agrees
with native captures. Godot checks path digests while independently sequencing
the CMF and updating voice state from a single initial checkpoint.

In particular, voice allocation preserves the original search path, including
its switch back to the channel scan after an occupied unassigned candidate.
Finding the same eventual voice is insufficient for reproducing its cost.

The 90-call hardware test now generates the instruction path from live state,
checks the resulting registers, then feeds that generated work to the hardware
model. This removes the binary interpreter and recorded work from its prediction
inputs. The resulting final states and endpoints remain exact.

## All-notes-off correction and source experiments

The previous controller-123 placeholder was based on a mistaken reading of the
voice-table pointer. Its loop target at driver IP 57fc reloads the table base on
every iteration. The implemented AdLib handler scans all nine voices, clears
A0/B0 for matching channels, and clears their note fields. It preserves voice
assignment and does not use the ordinary note-off frequency/volume sequence.

Forty-two constructed experiments check this handler, note-off, exhausted and
recycled voices, bend branches, volume clamping, rhythm setup, and ignored
messages against execution of the original handler. Python and Godot match
instruction paths, register writes, and final voice state. These are explicitly
source-level experiments, not newly observed native game routes. The optional
original-executable test regenerates the catalogue and every digest fixture.

## Evidence and validation

Native captures and their immutable matching link maps are retained under
`testing/output/wr1_hardware_native`, `wr1_hardware_loop_native`, and
`wr1_driver_hardware_native`. Fixture preparation verifies trace hashes, paired
entry/return observations, register output, and callback identities resolved
through that capture's map. Compressed fixtures retain entry and expected final
states, not future callback schedules as model inputs.

Fifteen focused Python tests pass, including regenerating work paths from the
supported executable. Godot passes 380,296 cumulative checks across the short
205-write capture, the 6,498-write song capture, and 90 whole MIDI calls. The
short interval overlaps the long one. Logs are
`wr1_thirteenth_python_tests.log`, `wr1_driver_work_godot_tests.log`, and
`wr1_driver_work_paths_godot_tests.log`. `git diff --check` passes.

## Limits and next step

The newer full-hardware capture matches all 6,504 comparable completed gameplay
states in the earlier complete-loop capture, but two late launch-call indices
differ by one frame. Many subroutine timestamps differ by about a cycle from
startup. The cause has not been established; do not assume that changing the
observer/core build preserves the previous absolute clock phase. Each capture
retains its own provenance and entry hardware state.

The 122 previously recorded gameplay admission residuals remain unresolved.
Next, model complete IRQ service and main-loop admission from a single playable-level
checkpoint. Runtime audio, native PCM comparison, remaining routes and levels,
original menus, and the ending are still open.
