# Room return and character reminder continuity

## Reproduction

The previous complete theater journey matched all 29 images but ended with the
wrong random state. A single ordinary return click from the original settled
theater snapshot reproduces it. `theater-return-native-a` and `-b` repeat their
two checkpoint states, images, full callback timeline and audio exactly
(`theater-return-native-repeat.json`).

`theater-return-baseline-b` matches both images but has final seed 741076434,
while the original has 4031028557. The browser is missing one random draw. The
minimized verifier restores the initial room state and theater choices once,
including the selected category read from DS:530E. The earlier baseline A
omitted that category, producing an unrelated initial-strip mismatch.

## Corrections

1. **Completing a character action schedules the next ambient event.** Original
   wrapper 392B calls BC43 at 39B4 after the action returns. The browser's
   `finishAction` omitted it. An overdue hunger reminder (action 13) exposed the
   missing draw. The reset now runs before the action's caller resumes.
2. **The activity return effect precedes overdue room reminders.** Browser
   `updateRoomTravel` serviced needs in its preparation phase, allowing action
   13 before the return effect. Normal activity returns now finish the effect
   first. Telescope movement retains its separately owned character action.
3. **Returning gives urgent needs ten seconds before interrupting.** Original
   room rebuild 1F24 calls helpers 575D and 579B after the return effect
   (22C8/22CD). If hunger or fatigue is at least 3 and its signed low-word due
   interval is below 600 ticks, the helper sets its deadline to now + 600.
   `postponeWarnings` implements that rule at return-effect completion.

These are ordinary action/transition rules. No instruction execution model,
reference seed reset, captured frame, or recorded timing schedule is added to
the runtime.

## Evidence and intermediate failures

- Candidate A fixes the omitted ambient reset. The short comparison and the
  full 29-checkpoint comparison pass image/state checks. The added ordering
  check still fails: action 13 starts during return preparation.
- Candidate B also fixes ordering. The short and full comparisons retain the
  correct random state, but their final image differs by 1,104 pixels around
  the clock/balloon. The ordinary delay check fails because urgent needs still
  start immediately after the effect. All 60 preexisting regression suites pass;
  those suites did not assert the missing return grace period.
- Candidate C adds the original 600-tick grace period. The minimized native
  comparison passes both complete images, state/random values and return order.
- `verify_room_action_continuity.py` uses fresh ordinary controls: choose the
  boy, spend time in the music activity, return, and let the reminder finish.
  It observes real dispatch and completion without installing gameplay state.
  It checks return grace time, reminder order, and the exact ambient random
  draw/deadline after action 13. Baseline fails both ordering and completion;
  candidate B fails grace time; candidate C passes all four assertions.

Candidate C SHA:
`a59674954b51d942f4afd9ce65d0ff68caa643c293db1a4b558e9f0e3da4ebfc`.

The full theater journey and ordinary return check are now registered suites.
Complete regression/delivery results are recorded in the completion ledger.
Exact callback timing and full audio waveform fidelity remain separate open
requirements; these checkpoint comparisons do not establish either.

## Delivery

`theater-return-regression-b` passes all 62 suites together, including all 29
full native theater images/state/random checkpoints and ordinary return checks.
`theater-return-environment-b` passes all 183 environment image states.
`theater-return-delivery-a` preserves the previous build and confirms the live
HTTP response matches candidate C. Known board and strict timing failures were
rerun on this build and retained; full clone parity remains false.
