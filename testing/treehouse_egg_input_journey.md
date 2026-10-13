# Egg input and return to the room

## Reproduced behaviour

The original egg is not draggable. Its shared object gesture waits up to 15
game ticks, ending early when the button is released, then dispatches the click.
The browser previously started the hatching sequence immediately on mouse-down.
This made its cracked/head/hatching states run ahead while the button was held.

`capture_prize_object_journey.py --kind 0` restores the original earned egg
room save, then captures the press, all hatching states, flight and return to
normal room activity. `--gesture drag` additionally holds and moves the pointer:
the egg hatches in place instead of following the pointer. The first exploratory
drag capture incorrectly asserted that the egg would remain; its failed report
is preserved. The later captures assert the observed disappearance.

The short-press captures are `egg-native-journey-c/d`; the held-motion captures
are `egg-drag-native-b/c`. Repetition evidence is `egg-native-repeat-a.json`.
Captures use original inputs and elapsed emulation, with no original RAM writes.

## Corrections in candidate e8ad0a585e54

- The egg has a pending click gesture, promoted in the object draw order immediately.
  It waits for release or the 15-tick hold threshold; pointer movement does not
  drag it. The existing cancellation path cancels the pending gesture.
- Every completed bird flight refreshes the ambient timer. The higher-level
  flyby handler also refreshes it. The original AABE/ABF6 and B9C6/BB3F handlers
  own separate resets; the previous browser implementation omitted the first.
- After a room object animation finishes, due balloon/cloud updates are serviced
  before the next ambient activity starts. Previously back-to-back animations
  could prevent those updates from running between activities.

These changes implement visible input, animation and idle-room behaviour.
They do not emulate CPU instructions, registers or interrupts.

## Evidence and remaining difference

`egg-browser-baseline-a` shows the previous build advancing egg states too early,
using a different later random state and producing a 535-pixel cloud difference.

`egg-native-check-d` matches all seven complete RGB checkpoint images and all
compared state fields except the final balloon rectangle. Its final seed matches
the original. `egg-drag-check-d` matches all four held-motion checkpoints in
complete RGB and compared gameplay/object/random state. The existing airplane
and caterpillar journeys also still pass in `egg-plane-regression-d` and
`egg-caterpillar-regression-d`.

**The full short-press journey still fails acceptance.** At its final checkpoint
the balloon is one step ahead. An event observation of the original and browser
shows the browser hatch/flight sequence finishing several ticks early. Its
earlier balloon update is then repeated on the normal cadence. Image membership
can find the correct earlier frame, but the final state comparison correctly
retains the failure. No time shift, mask, arbitrary extra delay or excluded
checkpoint is used to make it pass.

`observe_prize_journey.py` records only game-level object, balloon, cloud and
random/timer changes. `egg-native-events-a` and `egg-browser-events-a` preserve
this diagnosis. The diagnostic observer does not feed the browser runtime.

Other click-only room objects still need the same pending-gesture audit. They
currently dispatch immediately in `RoomCharacter.begin`; this correction is
specifically verified for the egg. Full intermediate-frame timing, sound output
and the existing board/yard fidelity failures remain open.


## Delivered increment

Build `e8ad0a585e548bbe58f827039242a74e81f29283e277436945f7285d5a64f55b`
is served locally. All 75 registered suites pass in one complete batch
(`egg-regression-d/report.json`), and all 183 environment states pass. The
previous live HTML/build metadata/verification are backed up in
`egg-input-delivery-a`, whose report confirms the HTTP-served hash.

The full short-press egg comparison is included as a **failed native journey**
in `completion_verification.json`, alongside the existing board/yard failures.
It was not converted to a passing partial suite. The held-motion journey is
included separately with its full four-checkpoint scope. Full clone parity
remains false. This delivery improves input and room behaviour while retaining
all known fidelity requirements.
