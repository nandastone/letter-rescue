# Twenty-ninth slice: contact scans and original text work

The Python and Godot contact planners now reproduce 64 complete contact calls
from C1AA to the pre-return checkpoint at C6F8. They derive each nearby-cell
scan and generated graphics call from the initial live attributes, word state
and graphics device. Every final state/attribute byte, graphics state, hardware
checkpoint, child argument and child entry/return cycle matches the capture.

The current route contains 51 initially inactive and 13 initially active word
scans, one word revelation, and no successful/failed match or pickup handler.
Durations are 187..4,138 guest cycles. The planner generates 64 fill-style calls
and eight additional calls for the reveal (four text styles, drawing-page
selection, string length, cursor and text). Matching-result and pickup
subroutines remain explicit unsupported boundaries; they are not claimed
complete by this evidence.

## Contact behavior

`wr1_contact_work.py/.gd` preserve the two source scan loops, including their
short-circuit bounds and immediate return when the first relevant cell is the
current source/last-touched location. A reveal changes the source attribute by
seven, selects the rotated word index, records source/last coordinates, starts
the DS:04BA speaker sequence when enabled, and writes the word to HUD page 5.
Subsequent renderer state must inherit these changes.

`wr1_contact_work_native.json/.jsonl/.map` is the immutable capture under
`testing/output`; `prepare_wr1_graphics.py` produces
`testing/fixtures/wr1_contact_graphics.json.gz`. The observer adds paired
contact/text hooks, complete 88-byte GX state, font context and input strings.
The former 64-byte graphics state omitted text settings at offsets 50..56.
Older fixtures remain unchanged and still exercise their original scope.

## Text work and the SCAS discrepancy

`wr1_text_work.py/.gd` model foreground/background style, cursor movement,
NUL-terminated string length, copying the string to the original local buffer,
alignment and the initialized EGA glyph loop. Font height, horizontal alignment,
transparency and string length select work. Glyph pixels do not choose branches
in this routine. This is timing/state work, not new framebuffer emulation.

An initial six-cycle discrepancy in both length and text was traced to the
emulator source. `core_dyn_x86/decoder.h` has no SCAS opcode case. The fallback
returns BR_Opcode; `core_dyn_x86.cpp` transfers the remaining budget into
CPU_CycleLeft, gives the normal core one cycle and runs it. The normal SCAS
loop and outer instruction-loop tests leave CPU_Cycles=-2 after each byte,
then a new dynamic block handles the next byte. This differs from dyn-x86's
MOVS/STOS REP loop, so the hardware models now have a separate `scas:N`
operation. No fitted six-cycle adjustment is used.

The first capture verifies seven text primitive calls including `bat`. A
second capture, `wr1_text_matching_native.json/.jsonl/.map`, replays
`wr1_matching.replay` from frame 350 to 849. Its fixture
`wr1_text_matching_graphics.json.gz` preserves 2,201 graphics calls across 85
completed updates, including 151 text primitives. The text tests exercise
`cop`, `5`, `10` and `15`: one-, two- and three-character strings, aligned and
shifted output, opaque and transparent glyphs. Text-string durations span
476..2,914 cycles. All 158 text primitive calls across both captures match
their native hardware, final graphics state and timing; strlen return values
also match.

Font initialization/change, text clipping, other font heights/backends and
unaligned cursor transforms still need recovery/coverage before claiming the
entire text library. The currently supported initialized EGA path is sufficient
for the observed word, score and reward text primitives.

## Validation and next integration

The focused 47-test Python regression suite passed in 167.583 seconds while
native capture and Godot verification also ran
(`wr1_twentyninth_python_tests.log`). After adding the second text fixture, all
three text/contact tests passed in 2.708 seconds (`wr1_text_contact_python.log`).
Godot passes 1,642,365 contact/primitive checks with zero failures
(`wr1_contact_work_godot.log`) and 23,381 checks across both text fixtures
(`wr1_text_work_godot.log`). Existing Godot idle/keyboard coverage also passes
83,057 checks (`wr1_contact_idle_regression.log`). The maintained core patch
reverse-applies cleanly; the standalone observer source remains separate.

The next reuse is the renderer's visible reward-popup branch BFFC..C111.
Its source selects font mode (D86:0036 / file 10296), switches text background
by page, invokes the small cursor+string wrapper at A333, decrements the
reward timer and restores font transparency. Static evidence is in
`wr1_reward_render_work.txt`, `wr1_reward_tail.txt`, `wr1_text_font.txt` and
`wr1_text_at.txt`. The font setter includes an INT10 font-info callback for
the active device; this call and initial reward text pointers/bytes need
measurement before composing the branch. The branch is still unsupported in
the current complete renderer planner; the standalone text tests do not prove
the entire caller.

Whole updates still need entity/action work at 50E8, fuller contact outcomes
and one continuous initial-state integration. Runtime admission has not been
replaced; earlier admission-frame residuals remain open. No new pixel parity
is asserted here. All levels/characters/difficulties, original audio output,
menus and ending remain part of the active exact-clone objective.
