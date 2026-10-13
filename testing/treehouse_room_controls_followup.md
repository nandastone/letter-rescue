# Room controls follow-up — 2026-09-29

This pass fixes three bounded behaviors in the playable game. It does not extend
CPU emulation or claim that the full room journey now matches.

## Navigation during the calendar

Choosing another friend (including the Home button) cleared `resident.selected`
before `setScene` rejected departure during narration. That left the room active
without its selected friend. Back, Go outside and Make some music already checked
the room's busy state before mutating anything.

`chooseFriend` now performs that same check. The regression uses actual buttons
with desktop/boy and touch/girl entrances, during both spoken date and rolling
calendar phases. It checks retained selection and scene, completion of the
calendar, and successful navigation once the action ends. No gameplay state is
installed by this regression; only the production clock is accelerated.

- Before: `room-navigation-baseline-a/report.json` has eight failed assertions
  across Home and Choose another friend (narration phase).
- After: `room-navigation-fixed-a` and `room-navigation-fixed-b` each pass the
  initial 40-check narration test. The registered `room_navigation` suite adds
  the rolling phase for 80 checks on the final candidate.

The failure came from duplicated navigation preconditions. New navigation
controls should apply those preconditions before changing selection or scene
state; the new real-control regression covers these two entry points.

## Clock completion

The isolated original clock journey already matched every pixel but missed
one idle-timer reset after the final spoken fragment. Resident code at 1516
calls CD40 to speak, then at 151B calls BC43 to schedule ambient behavior.

Room speech now accepts an optional completion callback, clears it before
invocation, and drops it when speech is replaced or the room is left. `tellTime`
uses it to schedule the friend after speaking. Other speech callers retain
their existing completion behavior.

- Before: `room-clock-baseline-c/report.json` fails only random state.
- After: `room-clock-fixed-a/report.json` matches both complete images and
  gameplay/random checkpoints. `room_clock` is registered for future builds.

## Returning chalk to the tray

The white stroke itself matched. All 54 different pixels were the arrow cursor:
the original showed white while the clone showed yellow. Native code installs
the arrow before resetting its logical color to 14 (DBC–DCB), so the displayed
arrow retains the tool color until the next pointer movement. It then resets
the friend's ambient timer (DD3 → BC43).

The chalkboard now retains that displayed color until the next movement and
notifies the app once on tool return. Scene changes clear the retained color.
This uses ordinary input and tool state, not reference image or trace data.

- Before: `room-chalk-baseline-b/report.json` has 54 pixel differences and a
  random-state mismatch after returning the tool.
- After: `room-chalk-fixed-a/report.json` matches the complete image and state.
  `chalk_native_stroke` is registered for future builds.

## Remaining scope

`room-native-check-f/report.json` retains the full 24-checkpoint journey.
The first eleven checkpoints now pass through the clock. Spider completion is
the first failure, followed by later room interactions. At that checkpoint the
browser is still busy, delaying the hunger update; environment completion also
does not reset the ambient timer. These are leads to verify with a short replay,
not established fixes. The full report remains failed.

Other retained board, yard, strict presentation and audio discrepancies remain
open. Exact presentation timestamps and waveforms are not established by the
passing image-membership comparisons described above.
