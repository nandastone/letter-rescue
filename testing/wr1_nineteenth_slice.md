# Nineteenth slice: aligned EGA rectangle-copy work

All 1,050 measured aligned rectangle copies now match completion time, modeled
hardware state and resulting arguments in Python and Godot. The work planner
uses each call's arguments, device record/descriptor and observed library mode
flags. It does not read the recorded completion time or substitute measured
durations for the original routine.

This removes the largest measured graphics primitive from the list of work
routines still to recover. It does not yet connect rendering and idle timing
into one continuous gameplay clock.

## Recovered path

`tools/wr1_graphics_work.py` and `scripts/wr1_graphics_work.gd` now include:

- Copy setup at file `138D8..13ADC`, including device lookup, source/destination
  bounds calculations, bit alignment and byte counts.
- The original EGA aligned-copy dispatch at `13C91..13D79`.
- Coordinate-to-VRAM work at `163B6..163D8`, called for source and destination.
- EGA mode/register OUT costs and one REP MOVSB per copied row.
- The BIOS video-mode query at `1919A..191D7` and its observed ROM handler.

Every measured call has the library mode-check flag set, so every copy performs
INT 10h/AH=0Fh before drawing. The observer captures that flag, copy-initialized
flag, display type, BIOS mode byte, video interrupt vector and its five code
bytes. The bytes match DOSBox's callback/IRET template. The source callback
returns the BIOS video mode without scheduling further hardware work. The
planner validates the template and includes the software interrupt, callback,
IRET and enclosing function's work.

The existing REP executor also matches this VRAM-copy path: its iteration
counts, CPU-budget exhaustion, re-entry accounting and pending instructions
predict every observed copy return. EGA OUT instructions contribute their IO
costs. EGA graphics-controller registers and VRAM pixel contents are not modeled
by this timing result.

## Coverage and limits

The 1,050 copies span 15 dimensions, from 8x24 and 16x16 tiles to 288x152,
320x32 and 16x168 regions. Observed durations range from 525 to 7,121 guest
cycles. Every sample copies between different pages and begins within bounds;
the returned coordinate arguments are unchanged. Thus these samples verify
the ordinary bounds/alignment path, not clipping behavior.

The source-derived planner includes clipping calculations and forward-copy
selection, but same-page overlap, shifted copies, invalid calls and other
graphics descriptors do not yet have equivalent native coverage. Unsupported
paths fail explicitly. Copy initialization itself remains outside the tested
interval because the first playable frame already has the library initialized.

The game timer and music state remain unchanged across each observed copy.
These copies contain no intervening timer interrupt. An interrupt arriving
during a graphics routine still needs a continuous executor/experiment; the
copy model is not evidence that this delivery case is complete.

## Retained evidence

- `testing/output/wr1_copy_work_native.json/.jsonl/.map` first establishes that
  the BIOS mode check is enabled on every copy. Its fixture is
  `testing/fixtures/wr1_copy_work.json.gz`.
- `testing/output/wr1_copy_bios_native.json/.jsonl/.map` adds the observed BIOS
  vector/template and mode byte. The authoritative fixture is
  `testing/fixtures/wr1_copy_bios.json.gz`.
- Both preserve the complete-update profile and final death/restart tail
  separately, as described in the eighteenth slice.
- The graphics preparer now retains returned arguments and initial/expected
  timer, music and keyboard context for future interrupt-delivery experiments.

Validation:

- 29 focused Python tests pass in 21.399 seconds, including original-executable
  catalogue reproduction and the prior driver, IRQ, keyboard and idle tests.
- Godot passes all 1,050 copy experiments and the preceding 129 page-selection
  experiments: 136,390 cumulative checks, zero failures.
- The maintained observation patch still reverse-applies cleanly against the
  instrumented core checkout.

Logs are `testing/output/wr1_nineteenth_python_tests.log` and
`testing/output/wr1_copy_godot.log`. The earlier analysis file
`wr1_copy_work_analysis.json` records the explicitly unsupported BIOS check;
`wr1_copy_bios_analysis.json` records zero cycle differences for the final
1,050-copy experiment.

## Next work

Recover the masked-sprite routine, including its image/header inputs and
alignment branches. It accounts for roughly 36% of the renderer interval in
the profiled route. The remaining renderer control flow, contacts/entities,
display work and IRQ delivery during those routines must then be composed
with the idle clock.

The gameplay gate is still unchanged. The older admission-frame residuals,
frontend input cadence, broader graphics/routes/levels, audio/PCM, menus and
ending remain open parts of the exact-clone objective.
