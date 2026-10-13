# Basket handoff and stationary drag completion

## Reproduced defects

The held open-basket comparison retained a 49-pixel worm difference. On the
current baseline `efc57996b725`, the browser draws the new worm immediately.
The original creates it and saves its background before waiting for the nested
press gesture; the worm is not drawn during that wait.

Extending the ordinary original hold to 60 frontend frames exposed a gameplay
defect as well. Releasing without moving drops the original worm onto the room
floor. The browser instead clicks the worm, starting its animation and causing
the bird to take it. Later object state and the shared random sequence diverge.

## Source rule and correction

Main A00B–A044 creates the worm, saves its background through 9112, and enters
the ordinary 9141 gesture. That handler waits 15 game ticks before entering
drag routine 67F2. The drag routine starts another 15-tick window. On release,
6A9F–6ACD treats an expired window as a placement even if the pointer has not
moved. A shorter stationary press remains a click.

`RoomCharacter.end` now applies this shared stationary-hold rule. It preserves
the separate click-only path. Rendering defers a newly created basket worm
during its first press wait, and the update at the end of that wait requests a
redraw. Release or cancellation removes the pending gesture normally.

No native frames, recorded timestamps, random values or CPU state drive these
runtime rules. The existing object placement routine handles falling, timers,
and later interactions.

## Evidence

All paths below are under `testing/output/treehouse/`.

- `basket-handoff-baseline-a`: the minimized initial/press/hold sequence
  reproduces the 49-pixel difference on the previous delivered build.
- `basket-handoff-long-baseline-a`: the new long hold exposes wrong release
  and settled object/random state, with 564 and 1,070 differing pixels.
- `basket-handoff-native-60-a` and `basket-handoff-native-60-b`: ordinary-input
  original captures repeat. All 141 action, checkpoint, timeline, image, RAM
  and audio comparisons pass in `basket-handoff-native-repeat-a.json`.
- `basket-handoff-draw-check-a`: changing only the initial draw fixes the
  held image while retaining both long-hold failures. This isolates the two
  causes; the failed report is preserved.
- `basket-handoff-check-a`: all 14 complete RGB checkpoint images and all
  compared gameplay/object/random states pass across short, held and long-held
  gestures, starting from one snapshot per journey.
- `stationary-drag-check-a`: 50 production mouse/touch checks pass for airplane,
  magnifier, flower, pillow and worm at 5, 20, 29, 30 and 35 held ticks. The
  previous build fails all 20 placement cases in `stationary-drag-baseline-a`.

The immutable candidate is `basket-handoff-candidate-a/index.html`, SHA-256
`27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413`.
Both new suites are registered in `verify_all.py`.

These native comparisons establish full checkpoint image membership and the
listed gameplay fields, not exact presentation or audio timestamps. The
money-loss divergence, nature/theater intermediate displays, room-return
timing, full audio comparison and remaining whole-session coverage stay open.
All 100 suites pass in `basket-handoff-regression-a`; all 183 environment
states pass. A fresh rebuild is byte-identical and the served HTTP hash matches.
Prior live files and verification are backed up in `basket-handoff-delivery-a`.
The completion gate remains failed while the larger requirements are open.
