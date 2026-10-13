# Earned prize object journeys

## Player-visible defects

The airplane landed at the correct location, but the balloon did not move out
of its drop rectangle. This left the balloon 22 pixels below its original
position after landing. A caterpillar dragged across the friend was drawn
behind the character; the caterpillar placed in the friend's hands was also
covered by the character animation.

The captures begin from original earned-prize room saves, then use ordinary
pointer movement, held dragging, release, waiting and (for the airplane)
clicking the landed plane to send it away. They do not modify original RAM.
`capture_prize_object_journey.py` records both the initial state and subsequent
input intervals. The plane and caterpillar captures each repeated identically:
all 215 and 147 compared PNG/JSON/WAV files respectively match, including the
run manifest and its timeline digest. Evidence:
`testing/output/treehouse/prize-object-native-repeat-a.json`.

## Implementation

- Clear the released object's rectangle by moving the visible balloon upward
  two pixels every two ticks. Hide the released object during this clearance,
  and retain the original visible pointer.
- Recreate the released object before offering or placing it; reset its timer
  at placement completion. These scheduling changes preserve the random
  sequence used by later gameplay.
- Draw the held object and the caterpillar in the friend's hands above the
  character. Promote the balloon when its normal movement redraws it.
- Departure of the airplane, egg and caterpillar does not itself reset the
  ambient timer. Character action completion remains responsible for its own
  timer reset.

Existing original code documents this behaviour: release/clear/recreate at
9310–9344, balloon clearance at 8CF4, placement timer at 9A94, object timer at
B8A3, and airplane departure at A14C. These are diagnostic source references;
the runtime implements object behaviour rather than CPU execution.

## Comparison boundary

The original stores a held object's starting rectangle while drawing its drag
image elsewhere. The browser stores both as `drag.rect` and the current object
rectangle. The verifier now compares the starting rectangle for stored state
and reports the displayed rectangle separately. The complete RGB image is
still compared without masks at every checkpoint. No pixel, random-state or
timing failure was removed to accommodate this representation difference.

Candidate `43a8cda7163cc8b06b0f8ab1c5621e3183ab10629de502c82c07a5c5e94bb9dd`
passes all five airplane and four caterpillar checkpoints, including complete
RGB image membership and the compared gameplay/object/random state:

- `testing/output/treehouse/plane-clearance-verified-b/report.json`
- `testing/output/treehouse/caterpillar-clearance-verified-b/report.json`

The prior failing reports remain in `plane-browser-baseline-a` and
`caterpillar-browser-baseline-a`. Intermediate candidate reports are retained.
The corrected verifier was also rerun against the previous live build:
`plane-clearance-baseline-c` still fails with 1,353, 992 and 911 differing
pixels after release, landing and departure; `caterpillar-clearance-baseline-c`
still fails with 83 and 113 differing pixels while held and after release.
This confirms that mapping the stored drag origin does not hide the defects.
Both journeys are registered in the aggregate runner. These nine checkpoints
do not prove every intermediate display time or audio waveform; the existing
strict timing and audio work remains open.


## Delivery

The candidate above is now served locally. `object-clearance-delivery-a/report.json`
confirms the HTTP hash and preserves previous live files. The complete 73-suite
batch passes; adding the two separately run prize suites gives 75 passing suites
on identical HTML. All 183 environment states pass. The money-loss, chip, yard
and strict nature comparisons were rerun and remain failed. Full clone parity is
still false.
