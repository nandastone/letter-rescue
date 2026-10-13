# Continuous yard and squirrel-hollow journey

## Original reference

`capture_yard_journey.py` restores one selected-yard state, then uses ordinary
mouse input for a 24-checkpoint journey. It visits the hollow, tosses four nuts
(the fourth must do nothing), wakes both squirrels, interrupts sign speech,
returns outside, changes the cloud three times, plays sun/birdhouse/all three
pond animations, calls the friend, revisits the hollow, tosses another nut,
returns to the yard and climbs back into the room.

Captures `yard-native-journey-a` and `-b` repeat exactly: inputs, decoded state,
all checkpoint images, 12,563 callback records and recorded audio. See
`yard-native-repeat.json`. Original RAM is read only. The browser comparator
initializes from one snapshot, then never resets gameplay state or random seed.

## Hollow completion side effects

The first nut toss previously consumed one extra R(10) draw. The original keeps
both seed 1083259673 and ambient deadline 5127 unchanged throughout the hollow
visit, including nut tosses, squirrels and sign speech. The generic browser
object/ambient completion paths instead called `scheduleAmbient()`.

`RoomCharacter.runObject` and `playAmbient` now accept a `resetAmbient` option,
defaulting to true. The hollow's toss, sign and squirrel callers explicitly
disable that reset. Other callers retain their existing behavior, including
natural wake. This corresponds to the original hollow loop's direct flight,
speech and animation calls at resident `3D39..3F33`.

The isolated `hollow` → `nut-1` replay fails before the change and passes after
it: `yard-nut-baseline-a` / `yard-nut-fixed-a`. Candidate A then matches every
checkpoint's random state, while exposing the remaining visual differences.

## Pond final image

The original keeps the frog on the rock after SCR1000 and SCR1001. The browser
removed the completed animation and repainted the empty background, causing
138 differing pixels in rectangle x15..31, y177..187. The original pond wrapper
at `608C..60DF` uses animation flag 0x2000 and preserves its final display.

The browser now retains the current pond animation's display after completion.
The next pond animation replaces it; entering the yard clears it along with
the original pond-cycle reset. It is drawn only outside. The focused
`birdhouse` → `pond-1` comparison fails on candidate A and passes on candidate B:
`yard-pond-baseline-a` / `yard-pond-fixed-a`.

## Complete comparison and remaining room timing

Candidate B `c279d12d4977` generates all 24 full RGB reference images. The first
23 checkpoints also match all compared gameplay, object and random fields.
At final room return, random/gameplay state matches but the balloon is one
movement step ahead: expected bounds [64,133,102,162], actual [65,135,103,164].
The correct image occurs earlier in the interval; the final state mismatch
remains a failure in `yard-native-check-c/report.json`.

Two comparator errors were corrected before this result: initialize the saved
indoor cloud X position even when starting outside, and read the balloon's
current bounds instead of the object's cached rectangle. No pixels are masked,
and no later state is installed to hide the remaining timing discrepancy.

`verify_yard_interactions.py` registers the 23-checkpoint yard/hollow portion as
a regression. The full 24-checkpoint comparison remains a separate required
completion input, including its failing room-return check. Neither comparison
establishes exact full animation timing or browser audio waveform parity.

## Older sequence fixture correction

The first integrated run fails `exterior_sequence` only in its 17 friend-window
frames, each differing by the same 138 frog pixels. That verifier chained a
pond interaction from the `native` capture into `credits-window`, whose capture
script explicitly restores a separate yard snapshot before using the window.
It now enters a fresh yard at that fixture boundary, preserving exact whole-RGB
and ordered-frame comparisons. This does not change the continuous yard
verifier, which keeps its frog and all state across the actual player journey.
The failed integrated evidence is retained in `yard-regression-a`.

## Delivery

Build `c279d12d4977` is served. `yard-regression-a` ran all 66 suites: 65 passed,
and the exterior fixture failed as described above. The corrected fixture
passes twice (`yard-exterior-sequence-fixed-a` / `-b`), with identical reports.
`yard-regression-b` combines those results transparently on the same unchanged
HTML; it is not a second 66-suite batch run. All 183 environment image states
pass. Known strict nature, money-loss and chip failures were rerun on this build.

`yard-delivery-a` preserves the previous build/report and records matching
candidate/served hashes. The full yard failure is now an explicit completion
input, so the new image/state coverage cannot hide its remaining timing gap.
