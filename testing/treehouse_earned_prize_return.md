# Earned magnifying-glass return

## Visible defect and correction

After the child used an earned magnifying glass, the browser recreated it at
its default prize position. The original places it from the released drag
rectangle onto the room floor. Skipping placement also skipped its ambient
timer update, shifting the shared random sequence used by later activities.

Original main 94D2–94F3 removes the offered object, runs character action 24,
recreates type 2 and rejoins ordinary placement at 96C5. The surface code at
97AE computes the floor position; placement resets the object timer at 9A94.
`RoomCharacter.offer` now follows that sequence, retaining the released bounds
and using the existing placement generator. No reference positions, timestamps,
random seeds or captured allocation sequence drive the runtime change.

## Ordinary player journeys

`verify_earned_prize.py` begins two fresh games: mouse/boy and touch/girl. Each
earns the magnifying glass through actual quiz controls, drags it to the child,
leaves and reenters the room, then reloads the page. It never installs gameplay
state or RNG. All ten checks pass on candidate `b5744fce90a3`; the previous
served build fails six geometry/revisit/reload checks. The original floor and
object-size data imply the expected returned rectangle `[147,155,173,183]` for
the tested drag. This expectation is test data only.

- Candidate: `output/treehouse/earned-prize-input-a/report.json`
- Red baseline: `output/treehouse/earned-prize-input-baseline-a/report.json`

## Pinned-original continuation

`capture_earned_prize_journey.py` continues the saved endpoint of the existing
ordinary quiz win/prize/room-return recording. It clicks the earned object,
offers it by held drag, leaves/reenters, and clicks it again. Capture F and G
agree on all 29 checks covering checkpoint images, RAM, audio, actions and
model checkpoints: `output/treehouse/earned-prize-native-repeat-a.json`.

`verify_earned_prize_native.py` replays the parent quiz recording and this
continuation in the **same browser session**, starting with one initial quiz
snapshot. No state/RNG resets occur at the room return or continuation seam.
The original hunger/fatigue deadlines are restored once at initial setup for
this longer comparison. Existing shorter suites retain their initialization.

The candidate preserves the original RNG at all **22 checkpoints**, compared
with 18 on the old build. Full compared state improves from 14/22 to 16/22.
Image membership remains 16/22; the remaining object-state mismatches are
balloon timing. After the later room reentry, all compared state matches, but
one pixel at the magnifier/child overlap still differs. The earlier click also
has animation/cursor differences. **This full comparison remains failed.**

- Continuous candidate: `output/treehouse/earned-prize-continuous-b/report.json`
- Continuous baseline: `output/treehouse/earned-prize-continuous-baseline-a/report.json`
- Separate room-only diagnostic: `output/treehouse/earned-prize-check-d/report.json`
  matches all 8 state/object/RNG checkpoints and 4/8 images. This diagnostic
  initializes at room entry and does not replace the uninterrupted comparison.

Whole audio waveforms, exact presentation timestamps, other prizes, robot
shelf continuity and the existing money-loss discrepancy remain open.

## Retained capture attempts

Capture A clicked the wrong exterior location for reentry and failed its scene
assertion. B–E exposed the core's stale pre-restore frontend image at the first
checkpoint: clearing the observer image or waiting one callback does not clear
the core's cached presentation. F/G retain a 60-frame ordinary wait after
restore, following the established room-capture procedure. That wait is recorded
and replayed in the continuous comparison. No pixels are masked or checkpoints
dropped. Earlier failed capture/check reports remain available.

## Delivery verification

The immutable candidate is `output/treehouse/earned-prize-candidate-a/index.html`,
SHA-256 `b5744fce90a3433acad289ecebe0498dccfd854dbbe794a53ab11f82e9462352`.
The new fresh-input regression is registered in `verify_all.py`. All 183
environment states pass. All 96 registered suites pass on this immutable build. The served HTTP hash
matches, with previous files backed up in `earned-prize-delivery-a`.


All 96 regression suites and 183 environment states pass. An earned magnifying glass now returns through original floor placement after the child uses it, preserving its position through room visits/reload and its placement random draw. Ten fresh mouse/boy and touch/girl checks pass; the previous build fails six. The uninterrupted quiz/prize/use/revisit comparison preserves all 22 random checkpoints (previously 18), while full state improves from 14/22 to 16/22. Images remain 16/22; balloon timing and click/overlap rendering differences remain explicit failures. Strict nature remains 614/984 callbacks with 12 missing displays; theater remains 385/580 intermediate images. Money-loss RNG, other resource lifetimes and whole-session audio/timing remain unresolved. Unrefreshed supplemental reports retain their prior build hashes; full fidelity is not established.
