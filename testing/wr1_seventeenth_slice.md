# Seventeenth slice: continuous idle clock and keyboard delivery

All 65 measured idle waits now predict the next gameplay admission exactly in
Python and Godot. Each wait starts from one native checkpoint and advances its
own CPU block budgets, hardware queue, interrupt delivery, game timer, speaker
sequence, BIOS ticks, music and OPL state. The model predicts 517 IRQ0 entries
and 24 IRQ1 entries, including their saved main-code return addresses and the
carry/zero flags used by the idle loop. Later hardware snapshots are expected
results only.

The first experiment starts at frontend call 561, the playable-level checkpoint,
and predicts five timer interrupts before the next admission. The other
experiments start at a completed gameplay update (main CS:0D72) and end before
the next timer reset/admission (CS:0444). This is continuous across each wait,
not yet across rendering and gameplay updates between the waits.

## Idle loop

`tools/wr1_idle_clock.py` and `scripts/wr1_idle_clock.gd` recover the ordinary
polling path at file 034BA..037A4, with the preceding update return at 040D2.
The ordinary loop contains 25 instructions. It compares the original control
flags, then compares the 16-bit timer and threshold as unsigned values.
Completed loops can be skipped only while they cannot exhaust the current CPU
budget; the final partial loop still determines the exact block that admits
the next hardware event. IRQ prologues, bodies and IRET are executed using the
previously verified work and hardware models.

The first idle capture produced 54 exact waits and 11 timing differences of
-14..+15 cycles. Every difference occurred in a wait containing a changed
replay button. All waits without changed buttons were exact. The first
divergence at call 674 followed newly pressed down/right buttons, while the
preceding five timer entries in that wait were exact. The original fixture
retains those residuals as a diagnostic experiment with the future inputs
deliberately omitted; no offset correction was added.

## Keyboard handler and controller

The original handler is file 0C714..0C95F, with port-60 input at 0C722 and IRET
at 0C95F. `wr1_keyboard_work.py` / `.gd` recover scan-code normalization, custom
binding precedence, the original 80-entry dispatch table, held control flags,
latched actions, activity flag and PIC acknowledgement. The static catalogue
contains instruction boundaries and dispatch targets, not recorded paths.

The observer now captures read-only keyboard controller state and the guest
keyboard handler before its first IN instruction and before IRET. All 24 native
bodies match duration, game keyboard state, hardware queue, controller buffer
and PIC state. They cover extended prefixes and down/right make/break codes.
Additional Python source-derived cases check custom binding precedence and
latched fire release behavior; those are not new native route coverage.

The controller model schedules each buffered byte using DOSBox's 0.300 ms
delay. Reading port 60 consumes the changed flag and schedules the next byte.
Scheduling an earlier callback can hand the current CPU budget back to the
PIC, as in the source. IRQ1 preserves the interrupted main-code state, executes
the original handler and returns to the same idle loop.

## Input timing contract

The final 65-wait experiment supplies the 12 changed key events at their
recorded **guest-cycle input delivery times**. These are external replay inputs,
not recorded IRQ entries or corrections to the next gameplay admission. The
model schedules their byte transfers and predicts all subsequent IRQ entries
and gate times independently. All 11 former input-related wait residuals
disappear when this missing work is included.

This does not yet derive those delivery times from frontend frame numbers.
The current bounded input executor requires delivery between idle CPU blocks;
input during an IRQ body and typematic repeat injection remain unsupported.
Menu and joystick paths fail explicitly outside the recovered ordinary loop.
The gameplay runtime still uses its previous approximate gate. The earlier
122 admission-frame residuals have not been rerun or declared resolved.

## Evidence and checks

Native captures are retained with matching immutable link maps:

- `testing/output/wr1_idle_clock_native.json/.jsonl/.map`: initial 54 exact waits
  plus 11 omitted-input residuals.
- `testing/output/wr1_keyboard_clock_native.json/.jsonl/.map`: keyboard handler
  bodies and input-boundary experiments.
- `testing/output/wr1_idle_keyboard_native.json/.jsonl/.map`: completed-update
  checkpoints including the controller and game keyboard state; all 65 waits.

Fixtures `wr1_idle_clock.json.gz`, `wr1_keyboard_hardware.json.gz` and
`wr1_idle_keyboard_clock.json.gz` preserve the experiments. Their preparers
verify complete captures and trace hashes and retain core/map/source hashes.
Absolute phase is taken from each experiment's own checkpoint; it is not
assumed identical across different core builds or captures.

Validation:

- 27 focused Python tests pass in 21.914 seconds, including catalogue extraction
  against the original executable and prior full-song driver/IRQ coverage.
- Godot idle tests pass 83,057 cumulative checks across both idle fixtures.
- Godot keyboard-body tests pass 2,093 checks.
- Existing Godot OPL/MIDI hardware tests pass 380,296 checks.
- Existing Godot IRQ tests pass 1,603,455 cumulative checks across the short and
  full-song fixtures. These overlap and are not independent sample counts.
- `git diff --check` passes.

Logs: `wr1_seventeenth_python_tests.log`, `wr1_idle_keyboard_godot.log`,
`wr1_keyboard_godot.log`, `wr1_seventeenth_hardware_godot.log`, and
`wr1_seventeenth_irq_godot.log`, all under `testing/output`.

## Next work

Recover the CPU work spent inside a gameplay update and rendering, from the
admission hook through the completed-update hook. That interval currently
requires a fresh native checkpoint afterward. Removing that boundary is
necessary to run the clock continuously from the first playable frame, wire it
into the clone, and rerun the admission-frame regressions. Frontend input
delivery cadence also needs an independently derived contract.

Original audio/PCM, remaining character/difficulty routes and levels, menus,
and the ending remain part of the active exact-clone goal.
