# Character animation balloon clearance

## Defect and original behavior

The original animation wrapper (main 43AC–43D7) calls 8CF4 with the
relocated script rectangle before beginning playback in the room. For child
actions the balloon moves upward by two pixels every two ticks until it no
longer overlaps the rectangle, including a two-pixel vertical margin.

The captured boy hunger warning uses SCR 20513, bounds
`[95,143,168,186]`, translated by `(+59,-3)` in pose 1. The resulting
`[92,202,165,245]` rectangle requires five upward balloon steps, moving its
top from 61 to 51. The previous browser build began playback with top 61.

## Implementation

`RoomCharacter` now prepares each character action with the existing balloon
clearance generator. Preparation contributes to busy state and keeps the idle
character visible. Animation construction, its start clock and pose changes
follow clearance. Non-overlapping, hidden and exterior balloons cause no delay.
The action queue preserves completion callbacks.

Preparation has its own task because offering a dragged object can enqueue a
character action from inside the object-placement generator. Replacing that
generator would lose its return/cleanup. STATUS.DAT import cancels preparation
along with the other resident tasks. The character script coverage loop now
waits through preparation as well as playback.

## Comparison evidence

Candidate SHA-256:
`efc57996b72588e9144516acede437714c79840d1e67b71080dad3968d645bfc`.

All paths below are under `testing/output/treehouse/`.

- `balloon-clearance-order-a`: 84 controlled checks pass for both children
  and all three standing poses, covering relocated bounds, margin, cadence,
  delayed animation construction, queues and non-overlap cases.
- `balloon-clearance-baseline-a`: the previous live build fails 30 of the
  same checks. The baseline is retained.
- `balloon-clearance-warning-a`: all five complete original images are now
  represented, previously two. Three of five checkpoint states match. The
  initial warning checkpoint has already moved two pixels in the browser;
  the completed checkpoint has one extra ambient movement. The playing and
  settled states match. No timing offset or per-checkpoint reset was added.
- `balloon-clearance-robot-a`: the uninterrupted robot quiz/prize/shelf/theater
  route retains 33/35 exact images, 32/35 complete states and all 35 random
  states. Three room balloon-position failures remain.
- `balloon-clearance-earned-a`: the joined human quiz/prize/use/revisit route
  retains 16/22 complete images, 16/22 states and all 22 random states.
  Balloon timing and two one-pixel overlap differences remain.
- `balloon-clearance-character-a`: all eight native model images and ten
  script/interaction checks pass.
- `balloon-clearance-environment-a`: all 183 original environment states pass.

The native comparisons check image membership within each recorded input
interval, not exact presentation timestamps. Their state/timing failures remain
open. All 98 suites pass in `balloon-clearance-regression-a`. The candidate rebuild
is byte-identical and its HTTP-served hash matches. Prior live files and
verification records are backed up in `balloon-clearance-delivery-a`.
Full-game completion remains unproven.
