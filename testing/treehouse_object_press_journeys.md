# Object press and yard consumption completion

Candidate `d7a51afab75241553a1094e409c740e96321350f9ad3ce06b172a4596502498c`
implements the original 15-tick held-press distinction for click-only objects.
A released press dispatches on the next game tick. The canvas ignores duplicate
capture-loss events after pointer-up, which previously cancelled that dispatch.
Opening the basket preserves the original handoff to its newly created worm.

Clicking a nut pile now consumes a nut or starts the yard squirrel animation.
Clicking dropped food starts its consumption animation. Object-specific timer
ownership removes extra random calls after nut, basket, bird and worm actions;
pile consumption schedules its long timer after the animation completes.

## Evidence

- `object-press-regression-e` contains the complete 76-suite run: 75 passed.
  The exterior fixture incorrectly required every random ambient choice to
  start an activity. Choice 7 is an original no-op. The corrected fixture covers
  all eight choices and passes twice on the identical HTML, retaining all image
  assertions. Delivery combines those results explicitly; it does not claim a
  second complete batch.
- The registered object-press suite passes 234 mouse/touch checks, including
  release, hold, blur, hidden-document and pointer-cancellation behavior.
- `object-click-comparisons-f.json` contains 16 ordinary-input original journeys:
  short and held presses for nuts, closed/open basket, bird, broken flower,
  nut pile, dropped food and the outdoor airplane. Fourteen journeys pass.
- Of 72 checkpoints, 71 match complete RGB image membership and 71 match compared
  gameplay/object/random state. The short nut press has one intermediate flight
  position discrepancy; the held open-basket journey has a 49-pixel worm image
  discrepancy. Neither failure is excluded from the delivered verification.
- Raw storage order of non-overlapping objects is reported as a diagnostic.
  Object identity, state, geometry, full rendered images and subsequent input
  remain required comparisons. Membership comparisons do not prove exact timing.
- All 183 environment states pass. Full money-loss, chip partial-redraw,
  yard-return balloon, short egg and strict nature timing failures remain open.
  Full audio parity is unproven.

The original captures use ordinary input and pinned saved states, without RAM
writes. Repeat proof compares actions, checkpoints, timeline hashes and all
PNG/WAV files. CPU instruction equivalence is not a completion workstream.
