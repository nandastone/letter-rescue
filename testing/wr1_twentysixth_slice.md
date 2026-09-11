# Twenty-sixth slice: complete renderer work on the captured route

The Python and Godot planners now reproduce every one of the 75 complete captured
renderer calls, from AB25 to the final pre-RETF checkpoint at C1A9. It generates
all 1,741 graphics calls from the initial renderer state and matches each
call's arguments, entry/pre-return timing and modeled hardware state, plus the
overall endpoint and renderer-owned state changes.

This closes the renderer timing model for this route. It does not prove every
renderer branch, every game update, or full-game fidelity. Each interval still
starts with one native renderer-entry checkpoint. Continuous execution across
updates has not yet replaced the runtime gate.

## Final renderer section

`RendererWork.complete` extends the actor model through the original tail:

- Traverse the foreground list after actors and redraw visible cells using
  their original source-X/source-Y tile tables.
- Clear the action-busy flag and process enemy rescue/effect states.
- Process miss and reward timers and their visibility checks.
- Copy the HUD top, left, right and bottom borders from page 5.
- Commit the newly drawn page to DS:807C, select it as the drawing page, set
  the original success return value and unwind the renderer stack.

The generated work stops before the outer RETF, matching the native probe. A
caller composing this renderer with surrounding game work must include that
RETF separately. Nested graphics returns are already included.

The tail model includes source-derived foreground, rescue animation, corpse,
miss and offscreen reward paths. Rescue completion that updates score/text and
visible reward text explicitly remain unsupported. The complete fixture does
not exercise them: every initial score, miss timer and reward timer is zero,
all enemy states are -1, and action-busy is zero. Those gaps must be resolved
and measured before claiming renderer coverage beyond this route.

## Complete native evidence

`testing/output/wr1_renderer_complete_native.json/.jsonl/.map` is the authoritative
capture. `prepare_wr1_renderer_complete.py` creates the hash-checked fixture
`testing/fixtures/wr1_renderer_complete.json.gz`, pairing renderer entry with
0812:1689 (file C1A9). It validates nested graphics-call pairing and the saved
renderer return address. No later checkpoint or captured call is supplied as
work-planner input.

The 75 complete intervals include 64 ordinary updates and 11 renderer calls
during the death/transition tail. They contain 20 foreground entries each and
generate 199 visible foreground copies, 300 HUD-border copies and 75 final
drawing-page selections beyond the earlier actor section. Total call counts:

- 1,223 rectangle copies.
- 234 masked-sprite passes.
- 150 drawing-page selections.
- 75 fill-style changes.
- 59 filled rectangles (their nested raw EGA calls are modeled internally).

Durations span 35,665..68,164 guest cycles. No timer-body entry occurs inside
these intervals, so this does not verify interrupt delivery during rendering.
There is no new framebuffer comparison in this slice.

## Validation and next work

40 focused Python tests pass in 88.621 seconds, including original executable
catalogue extraction and all prior hardware/music/IRQ/keyboard/graphics and
renderer fixtures. Log: `testing/output/wr1_twentysixth_python_tests.log`.

Godot passes 1,151,866 cumulative renderer checks with zero failures across all
eight interval fixtures, including every complete-renderer endpoint and child
call boundary. Log: `testing/output/wr1_renderer_complete_godot.log`. The
maintained observation patch reverse-applies cleanly to the core checkout.

The next integration boundary is the complete ordinary game update: movement,
contacts, speaker/actor work, this renderer, display selection and the idle
clock must share continuous hardware state. The source call order at
3D7E..3D9E is preserved in `testing/output/wr1_camera_3d72.txt`. The runtime
`player.gd` gate remains approximate, and the earlier 122 admission-frame
residuals have not been rerun or declared resolved.

Remaining scope also includes renderer paths absent here (full rebuilds,
additional directions/types, visible exit/blink, score/reward text), original
PCM, wider gameplay/character/difficulty/level coverage, menus and ending.
Loading duration stays excluded; synchronization begins at the first playable
level frame. The exact-clone goal remains active.
