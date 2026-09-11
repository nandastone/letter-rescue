# Twenty-seventh slice: renderer through the next admission

Python and Godot now predict 64 ordinary renderer-to-next-admission intervals
from one renderer-entry checkpoint each. The complete renderer, its outer
return, main-loop display selection, display return, iteration increment and
following timer/keyboard idle wait share the same hardware, game and music
state. No intermediate clock reset or future IRQ schedule is supplied.

The model matches all four intermediate checkpoints (renderer return, display
entry, display return and update-done), then every IRQ return location/flags,
hardware checkpoint and final admission cycle. This capture contains 512 IRQ0
entries, 24 IRQ1 entries and 12 externally timed changed keys. Total intervals
span 2,230,670..2,266,494 guest cycles. Their renderer portions span
45,375..68,180 cycles. These numbers belong to this capture's clock phase;
the previous renderer fixture uses a different build and initial phase.

The ordinary post-render path is C1A9 -> 3DA3/3DAA -> 409B/409F -> display
17606..17695 -> 40A4 -> 40B1/40B6 -> 40CF -> idle 40D2. The comparison at
40B1 clears carry and the iteration increment determines zero before the
idle jump. Successful display selection returns AX=0. These CPU values are
derived from the source and initial main iteration counter, not read from the
future idle checkpoint.

`wr1_renderer_clock.py/.gd` compose the existing work planners with IdleClock.
`prepare_wr1_renderer_clock.py` preserves and validates the immutable capture
`testing/output/wr1_renderer_admission_native.json/.jsonl/.map`, producing
`testing/fixtures/wr1_renderer_clock.json.gz`. The observer now includes the
initial display, clock/music/keyboard and caller iteration state at renderer
entry. The fixture explicitly excludes 11 death-transition renders; it also
rejects captures with input or IRQ preemption during rendering/display.

42 focused Python tests pass in 87.858 seconds, including executable catalogue
extraction and all existing timing/music/keyboard/graphics/renderer fixtures.
Godot passes 83,851 checks with zero failures for this composed experiment.
Logs: `testing/output/wr1_twentyseventh_python_tests.log` and
`testing/output/wr1_renderer_clock_godot.log`.

This is exact for the measured ordinary route, not continuous across complete
updates yet. Movement, contacts and entity work before renderer entry remain
the next timing integration gaps. Rendering interrupted by an IRQ explicitly
raises instead of reporting false parity. External key changes still use the
recorded guest-cycle delivery contract; frontend input timing is not inferred.
The earlier 122 runtime admission-frame residuals remain open and the runtime
gate has not been replaced. No new framebuffer comparison is claimed here.

Loading duration stays outside the target: comparisons begin at the first
playable level frame. Wider renderer branches, all gameplay routes/levels,
original audio output, menus and ending remain open. The exact-clone goal
remains active.
