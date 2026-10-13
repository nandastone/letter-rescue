# Robot prize journey and character warning completion

## Complete robot reward route

`capture_nature_journey.py --robot` plays an ordinary original guessing game.
The human makes legal wrong guesses; the robot chooses its own questions and
eventually wins. The recording continues through both animal reveals, prize
selection/delivery, the room, automatic telescope shelf selection, shelf replay,
room return, a theater visit and another room return. No original RAM is patched.

Two recordings (`robot-prize-native-a` and `robot-prize-native-b`) agree in all
117 repeat checks: checkpoint PNGs/RAM/audio, actions, semantic checkpoints,
capture tool hash and the complete callback timeline digest. See
`output/treehouse/robot-prize-native-repeat-a.json`.

The browser replay initializes once at the original quiz's initial state and
then uses the same mouse choices and elapsed game ticks. It compares quiz/RNG,
robot shelf flags and telescope visit mask throughout. Room endpoints also
compare object state/geometry and character pose/hunger/fatigue.

The current candidate matches **33/35 full checkpoint images and all 35 random
states**. All quiz turns, both reveals, prize delivery, first shelf view, shelf
replay and theater entrance match. Three room endpoints retain balloon-state
differences, and two retain full-image differences. Complete state is 32/35.
This is still a **failed full-fidelity comparison**, not a closed whole-game
requirement. Sources/rates, unaligned waveforms and exact intermediate display
timestamps remain separate requirements.

- Baseline: `output/treehouse/robot-prize-check-a/report.json`
- Candidate: `output/treehouse/robot-prize-check-b/report.json`

`verify_winning_journeys.py` now covers six fresh ordinary-control routes,
including explicit mouse/boy and touch/girl robot winners. It checks automatic
shelf selection immediately after earning a robot prize, without pressing the
explicit shelf-view button, and verifies ownership after another activity and
its original session-only lifetime after reload. All 69 checks pass on the
previous build in `robot-prize-input-b`; this strengthens coverage rather than
claiming a new shelf implementation. The candidate is also exercised by the
full regression run.

## Warning-order defect found by the longer route

At the last room return, the original had begun a hunger warning but still
stored hunger 3. The browser had already stored hunger 4. The warning's deadline
had advanced in the original, so this was not an uninitialized timer.

The independent focused recording `capture_need_warning.py` begins from the
ordinary shelf-return save and waits through the next warning without modifying
state. It observes hunger 3 before the warning, at its start (tick 34881), and
during playback (34932), then hunger 4 on completion (35187). Its long deadline
remains 42081 throughout. Two recordings agree in all 23 repeat checks covering
PNG/RAM/audio, actions and model checkpoints.

The original source establishes the full ordering:

- Main 5578/564E first schedule hunger/fatigue's long deadline.
- Warning actions/window scripts run synchronously.
- 575D/579B postpone the other urgent need using a signed low-word comparison.
- Urgent retry deadlines are set after playback at 5622/5731.
- The need counter increments after those operations at 5636/5745.
- A suppressed urgent warning (the other need is already 5) keeps its counter
  and does not invoke the other-need grace-period routine.

`RoomCharacter.updateNeeds` now performs those completion steps in the actual
character-action callback or after the window-script generator finishes. The
long deadline is established at entry; the urgent retry and grace period are
based on completion time. No native timestamps or delay corrections are used.

All 576 ordering checks across 96 controlled initial-state cases pass for both
characters, inside/outside, hunger/fatigue, and warning/suppression branches.
The prior build fails 164 checks. These use production scripts and sound
durations, but are component tests rather than fresh-input/native timing proof.

- Red: `output/treehouse/need-warning-order-baseline-b/report.json`
- Green: `output/treehouse/need-warning-order-a/report.json`
- Focused native: `output/treehouse/need-warning-check-a/report.json`
- Repeat: `output/treehouse/need-warning-native-repeat-a.json`

The focused native replay now matches hunger at all five checkpoints; its
complete state and image results remain 2/5 because of balloons. The longer
robot route no longer differs in hunger. No balloon or image failures were
excluded to obtain these bounded results.

## Next rendering discrepancy

During the focused warning, the original raises an overlapping balloon from
top 61 to top 51 before the character animation. The browser leaves it at 61.
Original wrapper 43AC–43D7 calls balloon evacuation 8CF4 on the relocated script
rectangle before playback. The boy's SCR 20513 bounds are `[95,143,168,186]`;
pose 1 translates this to `[92,202,165,245]`. Evacuating a 38-pixel-high balloon
upward in two-pixel steps against the rectangle's two-pixel margin explains the
five observed steps. Character-action preparation currently lacks this call.
Implementing that sequence remains required; this is distinct from the known
room-rebuild deadline differences and needs its own native/frame regression.

## Retained harness failures

- `robot-prize-baseline-a` stopped at an unrecognized native theater scene 13;
  `robot-prize-check-a` covers the complete route with that scene decoded.
- `robot-prize-input-a` checked room return before theater curtain completion.
  Its corrected waiter now services the existing theater presentation; no
  production change was made for this harness failure.
- `need-warning-order-baseline-a` did not mark the controlled exterior fixture
  as having a selected child. Corrected fixture baseline B remains red.
- The initial full regression retains two exterior assertions for immediate
  need increments. They are contradicted by the source ordering above. The
  revised checks assert the old counter during playback, the initial long
  deadline and the increment after completion; all 15 native exterior images
  remain checked. The previous build fails those revised assertions.

## Verification and delivery

Candidate SHA-256:
`9b6d63debe08a863c5a6ba57bbe99342cc2c96dfc44668cdf175f32249990d3e`.
All 183 environment states and 97 suites pass on this immutable build.
The full batch passed 96 suites; the source-corrected exterior suite passed
on rerun. `need-warning-regression-b/report.json` records that provenance,
without claiming a second complete batch. The HTTP-served hash matches, and
previous live/verification files are backed up in `need-warning-delivery-a`.
The game-wide completion gate remains required.


97 regression suites and 183 environment states pass on one immutable build: the full batch passed 96 suites, and the exterior suite passed after replacing two immediate-increment assertions with original warning-completion ordering. The failed batch is preserved. Hunger/fatigue increments, urgent retry deadlines and the other need grace period now follow warning completion. All 576 branch checks pass (164 failures on the prior build). A complete original robot quiz/prize/shelf/theater journey matches 33/35 images and all 35 random states; three room endpoints retain balloon-state differences, and full state remains 32/35. The prior hunger mismatch is fixed. Strict nature remains 614/984 callbacks with 12 missing displays and theater remains 385/580 intermediate images. Money-loss RNG, balloon clearance/return timing, full audio timing and other required integration remain open. Unrefreshed supplemental evidence retains historical build hashes; full fidelity is not established.
