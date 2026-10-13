# Room return: scheduling and balloon movement

## Reproduction and competing explanations

The complete animal/prize journey ended with a different room image and a random
stream three draws behind the original. A minimized ordinary Exit-button replay
starts once at the original `back-to-nature` snapshot:

```powershell
python tools/treehouse/verify_nature_native_journey.py --html testing/output/treehouse/playable/index.html --start back-to-nature --output NEW_OUTPUT
```

The preserved baseline `output/treehouse/room-return-baseline-a/report.json`
fails in about six seconds: initial image matches, final room differs by 723
pixels and random state differs. The earlier whole-journey report differs by
717 pixels because its initial clock fixture had a different accumulated time.

Ranked explanations were a missing room-entry scheduling operation, transition
timing changing ambient/balloon service, and incomplete initial fixture state.
Each was checked against its observable effect; no guest instructions or RAM
were modified and no processor-equivalence implementation was added.

## Scheduling cause and correction

`capture_room_return.py` restores the pinned original nature snapshot and clicks
Exit normally. It observes only function boundaries and random-call arguments.
`room-return-native-b` and `room-return-native-c` reproduce the original final
PNG and seed exactly using snapshot protocol 2. The initial `-a` capture used
Y=11 instead of the original Y=12; it is preserved as a harness mismatch.

Original BB48 schedules the long event, refreshes the indoor nut timer when
present, and then calls BC43 to schedule a short ambient event. Room reset
B95C calls BC43, BB48, cloud reset, and each present object's timer reset.
The browser previously omitted BB48's short-event scheduling and nut refresh.

The original return consumes eight draws during reset. That sequence schedules
the nest event early enough to run before the checkpoint: one draw chooses it,
and one schedules the next event on completion. The old browser used seven
draws during reset and did not reach that nest event. `scheduleLong()` now
implements BB48 and is used by both room entry and long-event expiry.

Candidate `room-return-candidate-a` removes the random-state failure while
retaining the image failure (`room-return-check-a`), isolating this cause.

## Balloon and fixture corrections

Original ordinary balloon movement runs when `now > due`, scheduling the next
deadline at `now + 48`: successive unobstructed moves are 49 ticks apart.
Vertical movement wins an equal-distance tie. Both rules are now reflected in
the browser. The separate chalk-clearing lift retains its own two-tick cadence.

The verifier previously invented a noon clock and used a cached minute from the
last room visit. This snapshot actually has a 16-hour BIOS clock, and the cached
minute remains stale while playing an activity. Initialization now reads BIOS
ticks at 0x46C from the saved low-memory region and advances that time with the
browser game clock. The native clock-read observation independently confirms
16:22 at room return. This correction affects the verifier only.

`room-return-check-c/report.json` passes both full-RGB checkpoints and the random
stream, with the room image generated at tick 1473 within the action interval.
The native checkpoint is at relative tick 1550. **This is image membership and
gameplay continuity, not exact transition or room-event timing.** Final balloon
positions at the two checkpoint times still differ by one motion step. Existing
strict timing failures remain required work; this report does not waive them.

## Complete journey and regression coverage

`room-return-full-a/report.json`, on candidate `d367f5d54d5c`, passes the entire
original question/wrong-guess/win/prize/new-game/room-return journey: all fourteen
RGB checkpoints, active gameplay state, shared random state, delivered prize and
final scene. It starts from one snapshot and does not reset state between inputs.

The first broad candidate run (`room-return-regression-a`) exposed a verifier
assumption: choosing the first available question with help enabled can leave
only the correct animal, making the subsequent required wrong guess impossible.
The verifier now chooses the offered question leaving the most candidates.
It still uses only visible controls; candidate attributes are a read-only
answer oracle, and the wrong-guess assertion remains required.

Because the corrected random sequence also changes who wins incidentally,
`verify_winning_journeys.py` now includes a fifth explicit robot-winner route.
The human keeps asking questions while the robot narrows its candidates and
wins. This route requires robot victory, prize delivery to its shelf, telescope
visibility and the correct reload lifetime. Both human and robot prize ownership
are now aggregate requirements. All five journeys and 53 checks pass in
`room-return-winning-b/report.json`.

The cause was omitted side effects in a scheduling helper, plus two balloon
movement rules. Keeping BB48's coupled deadlines in `scheduleLong()` prevents
entry and recurring-event callers from implementing different subsets of it.
There is no temporary runtime instrumentation; the observation tool remains a
separate diagnostic capture tool.

## Delivery

Build `d367f5d54d5cd4e057b7512f72eaa2022c4d9eb4da4eee2d996eae186b9e377e`
is served locally. All **51 suites** pass together in
`room-return-regression-b/report.json`, including the complete native animal
journey and five browser winning/prize journeys. All **183 environment states**
pass in `room-return-environment-b/report.json`. Live, candidate and HTTP hashes
match; prior files are backed up in `room-return-delivery-a`.

Strict timing remains 614/984 with 12 missing displays
(`room-return-strict-b/report.json`). Complete native chip and money-loss
comparisons were rerun on this build and retain their documented failures
(`room-return-native-chips-a` and `room-return-native-loss-a`). Completion gate
`completion-gate-ap.json` remains failed for the open fidelity requirements.
