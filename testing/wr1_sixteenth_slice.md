# Sixteenth slice: game timer body, speaker and BIOS work

All 9,641 measured timer-interrupt bodies now match completion time and modeled
hardware, game-timer, speaker, BIOS, music, and voice state in Python and Godot.
The observation interval starts at the timer increment (CS:0232) and ends
immediately before IRET (CS:0313), after the registers have been restored.

Music and voice state advance continuously from one checkpoint. Hardware and
game/speaker state are still initialized at each interrupt entry. This verifies
the interrupt body; it does not yet predict interrupt delivery or main-loop
admission continuously from the first playable frame.

## Recovered outer work

`tools/wr1_irq_work.py` and `scripts/wr1_irq_work.gd` recover the timer increment,
32-bit speaker elapsed counter, signed speaker duration comparison, advancing
at most one speaker entry, stopping/programming the speaker, BIOS countdown,
interrupt acknowledgement, and register restore. The work executor models the
ordinary IO costs for these paths separately from the AdLib wait primitive.

The live saved BIOS vector and INT 1Ch vector are observed, along with their
instruction bytes. Their code matches DOSBox's CB_IRQ0 and CB_IRET templates.
The model validates those templates and includes the callback, nested software
interrupt, IO acknowledgement, and return instructions. The BIOS tick counter
matches after the callback. Speaker waveform generation and PIT channel-2 audio
state are not part of this timing result.

The full interval covers 2,410 BIOS calls, 1,113 bodies with an active speaker
sequence, and 64 speaker-sequence advances or stops.

## Pending interrupt handoff

The initial outer-body comparison matched elapsed time but found one internal
budget mismatch: a keyboard transfer became pending while IRQ0 was in service.
On EOI, DOSBox's master PIC signals that waiting interrupt and moves the unused
CPU budget back into `CPU_CycleLeft`. The current instruction block's deferred
cycles remain pending. Ignoring that handoff preserves the sum of the budgets,
but produces the wrong state for subsequent execution.

The observer now records the master PIC request, service and mask registers,
active priority, mode flags, and IRQ-check signal. The hardware model raises the
timer/keyboard request bits, preserves requests while blocked by IRQ0, and
performs the source-derived EOI priority check and budget handoff. Unsupported
PIC priority modes fail explicitly. The caller must supply initial PIC state
when executing an acknowledgement; no default controller state is guessed.

All final master-PIC fields now match. Four bodies end with an interrupt pending:
one keyboard request and three timer requests, including song-repeat work.
The pending request is a bit, so repeated timer edges can coalesce while the
handler remains busy. Delivering that request after the final IRET is the next
piece of the continuous clock model.

## Evidence and regression coverage

- Initial outer-body probes are retained under
  `testing/output/wr1_outer_irq_native` and `wr1_outer_irq_loop_native`, each
  with its capture JSON, trace JSONL, and matching immutable link map.
- The authoritative probe with master-PIC state is
  `testing/output/wr1_irq_pic_native.json/.jsonl/.map`.
- `testing/fixtures/wr1_irq_hardware.json.gz` preserves the first 561 complete
  bodies; `wr1_irq_hardware_loop.json.gz` preserves all 9,641. The short interval
  overlaps the long one. The former short fixture without PIC state is retained
  at `testing/output/wr1_irq_hardware_before_pic.json.gz`.
- Preparation verifies capture and trace hashes, fixed CPU configuration,
  paired boundaries, mapped callbacks, and continuity of music/voice state.
- Both Python IRQ tests pass. Godot passes 1,603,455 cumulative checks over the
  short and long body fixtures, including all modeled hardware fields.
- The broader set of 21 focused Python tests passes in 22.249 seconds. Existing
  Godot music-service and REP tests still pass at 2,809,541 cumulative checks.
  `git diff --check` passes.

Logs are `testing/output/wr1_irq_hardware_python_tests.log` and
`wr1_irq_hardware_godot_tests.log`. The broader regression run is recorded in
`wr1_sixteenth_python_tests.log` and `wr1_sixteenth_music_godot_tests.log`.

## Next integration

The next step is interrupt entry/delivery and the original main loop's waiting
work, using one initial hardware checkpoint. The final IRET, pending interrupt
delivery, and periods spent rendering/updating between interrupts must be
accounted for before replacing the gameplay clock gate. The 122 recorded
admission residuals remain open and the gate has not yet changed.

Original runtime audio and native PCM comparison, remaining character/difficulty
routes and levels, menus, and the ending remain part of the active goal.
