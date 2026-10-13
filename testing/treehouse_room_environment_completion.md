# Room environment completion — 2026-09-29

## Reproduced defect and fixes

The original 24-checkpoint room journey pops its balloon before visiting the
calendar, clock, spider and nest. The browser removed the balloon from the room
but `beginEnvironment` still checked its old rectangle and moved the invisible
balloon out of the animation area. This delayed the spider and subsequent needs
updates. The clearance check now ignores a hidden balloon, as other room paths
already do.

The short replay `clock` → `spider` isolates this defect:

- `room-spider-baseline-b`: 998 pixel differences; seed and hunger differ.
- `room-spider-hidden-balloon-a`: complete image and hunger match; seed differs.
- `room-spider-fixed-a`: complete image, gameplay and random state all match.

The remaining seed difference was a missing completion action. Original spider
handler 604F ends with BC43 at 6083; nest animation ends with it at 4D66; chirping
ends with it at 3D30. All three reset ambient scheduling after completing.
`TreehouseRoom` now calls its supplied environment completion callback at those
boundaries, including interruption of a finished animation's remaining sound.
Leaving the room cancels its activity without invoking a completion callback.

The first full batch (`room-environment-regression-a`) caught a consequence of
that change: the nature-game return consumed one extra random draw. Its automatic
nest event was scheduling once before starting and again at completion. Original
dispatch at 883B–88AF chooses the handler without a preliminary reset; existing
`room-return-native-b` evidence shows the choice at tick 12035 and the single
reset at 12106. The selector's preliminary reset has now been removed, leaving
scheduling with each handler. A short nature Exit replay changes from failing
(`room-environment-return-baseline-a`) to passing
(`room-environment-return-fixed-a`), with both complete images exact.

The next batch identified a test assumption in `verify_exterior`: it required
the timer to change two ticks after starting an ambient animation. That is the
old premature scheduling behavior. Its replacement checks that an animation
actually starts while the friend sleeps, completes, then schedules the next
event with the friend still asleep. All fifteen full-image comparisons and all
other yard assertions are unchanged. The corrected suite passes separately in
`room-environment-exterior-fixed-a` on the same candidate HTML.

The clone uses its own interaction and animation state. No saved random values,
reference pixels or recorded callback timestamps were added to runtime code.

## Whole original room journey

`room-native-check-h/report.json` passes **all 24 checkpoints**, with full RGB
image membership and compared gameplay/random/object state:

- Initial room and popping the balloon three times.
- Calendar open, dismissal, next/previous day, close and cloud change.
- Clock, spider, chirping and nest.
- White and red chalk selection, strokes and return to tray.
- Erase question, decline, repeat, confirm, calendar reopen and close.

The journey starts from one native snapshot and subsequently uses only recorded
mouse actions and elapsed game ticks. There are no checkpoint resets. It is now
registered as `room_native_journey` in the full regression runner.

This proves complete image membership and the listed state fields for the
journey. It does not prove exact presentation timestamps or audio waveforms.

## Ordinary feeding, sleep and waking

`verify_room_care_journey.py` uses visible controls for desktop/boy and touch/girl.
Only time is accelerated through the production update loop; hunger, fatigue,
pose, inventory and random state are never installed by the test.

Both sessions refuse a pillow before tiring, eat an apple when hungry, nap,
remain asleep when clicked, leave for the yard and return while asleep, wake
naturally, tire again, nap again, wake to enter music and return to the room.
The checks include returned pillow inventory, fatigue and usable navigation.

`room-care-journey-c` and `room-care-journey-repeat-a` pass all 22 checks with
identical actions and checkpoint states. This integration journey supplements
the older focused native sleep/wake evidence described in
`treehouse_character_research.md`; it is not a new paired full-audio comparison.

Earlier harness attempts are retained: `room-care-journey-a` failed report
serialization of a Date; `room-care-journey-b` incorrectly required a particular
standing pose after a hungry friend's activity departure. The final assertion
requires an awake friend, cleared wake time and returned pillow. Hungry/tired
standing poses remain valid and were not changed to satisfy the test.

## Remaining work

Exact room presentation/audio timing and further object-drag paths remain open.
The board-loss sequence, chip partial redraw, yard-return balloon cadence and
strict nature presentation discrepancies also remain in the completion report.
The passing room journey does not imply complete-game parity.

## Delivery

Served build: `61f8e694fe1b772846ec0cf6d9c4bd9844960b7ec175f226543f98d2dab31cfc`.
`room-environment-regression-b` ran all 72 registered suites, passing 71; the old
exterior scheduling assertion failed. Its corrected suite passed twice on the
identical HTML, including all 15 image comparisons. Aggregate
`room-environment-regression-c` records 72 passing suites with this provenance,
without claiming a third full batch. The full room and nature-return comparisons
both pass in batch b. The final care journey also repeats identically in
`room-care-journey-repeat-b`.

All 183 environment image states pass. The separately rerun board-loss, chip,
yard-return and strict nature comparisons retain their documented failures on
this same build. `room-environment-delivery-a` backs up the previous live files
and verification and records the matching HTTP-served hash.
