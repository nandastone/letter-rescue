# Nature quiz: reminders, sound cues, and random order

Primary sources: `output/treehouse/research-resources/overlay2-disassembly.txt`, resident `all-disassembly.txt`, original `source/reference-v1.zip`, and ordinary-input DOSBox recordings under `output/treehouse/research-nature-final-audit/`. No guest RAM was changed. `nature-final-audit-capture.py` records source-state hashes and input actions. `nature-final-audit-analyze.py` extracts 24 named original frames and independently reconstructs the RNG transition.

## Concrete gaps found

At the initial audit, NatureQuiz omitted the idle reminders, sound1008 on each question reveal, and blocking robot sound1011. It also skipped one starting-player RNG call in robot mode; that last issue was already corrected in the working runtime while this research ran.

### Idle timer and button feedback

Overlay2 `2BBF..2BCF` invokes `3C9F(0)` when DS201A expires. Recognized input resets DS201A to300 at `2BE2`. Reminder completion resets it to300 at `3DBA`. This is a delay measured after each reminder finishes, not a fixed repeating300-tick wall-clock interval. Initial question availability also sets300 at `304B`.

| State | Exact recipe | Source |
|---|---|---|
| Ready / answered | `28CE(1,0)`, wait8, `28CE(0,0)` | `3CA8..3CBA`, `3E27..3E64` |
| Awaiting a question | Iterate available attribute IDs **ascending**, not offer order. Render question off, wait18, render on, sound1008, wait6. Finally guess control background red12, wait24, restore white15. | `3D34..3DB7` |
| Awaiting a guess | Iterate surviving card indices ascending. Play `1050+random(5)`, redraw that candidate on red12, wait6, redraw with default surviving white15. Crossed-out candidates are skipped. | `3CBD..3D2E`, `1EB9..1FA0` |

Ready feedback is **not a red fill**. `28CE` uses `modules` shapes5650+17+flag, i.e. **5668 lit → 5667 normal**, at the existing die button rectangle. Its alternate DS55EA!=0 branch draws trophy relative22 with red12/white15 background. Arguments shown above are in caller push order; `bp+8` is the highlight flag, `bp+6` the optional full redraw flag.

The card red background is the entire existing thumbnail rectangle `quiz_rectangles[20+i]`. `1EB9` selects the animal's existing thumbnail/palette and calls centered-shape helper6C2E with that background. It does not substitute a red border or change the manual crossout strip. For these reminder calls, its third argument is0, so no crossout-control sound/redraw side effect is requested.

Question-off uses `198A(attribute,0,0)` and restores via `198A(attribute,1,1)`, including the original per-question background restoration (the question symbols are not all standalone opaque rectangles). Guess control uses `299D(12,0)` / `299D(15,0)`.

The off call hides **both the question background shape and the question icon**. `19C3..19C9` jumps to `1A1A`, which restores saved-background handleDS5538 through resident438B; `1A23..1A29` then skips the glyph. Thus a complete-frame renderer should skip the entire offered-question draw for the reminder-hidden attribute. Native confirmation: off ID1 rectangle(218,70,245,96), ID2(261,55,278,72), and ID6(234,110,254,126) each matches the original ready/no-question scenery crop exactly, with zero changed pixels. See `question-off-restoration.json`. The turn's existing `questionHidden` threshold is a separate case and must not automatically inherit this full-background hiding rule.

`3C9F(1)` is also invoked by invalid attempts such as pressing guess after answering/already guessing (`3054..306E`). In the answered branch, that flag adds nonblocking sound1017 before the same8-tick die feedback (`3E30..3E3D`). An idle reminder uses flag0 and does not play1017.

The waits call resident56DB, the same interruptible wait used elsewhere. A faithful reminder should keep the original input interruption semantics instead of locking out input for the full reminder.

### Named native frames

All files below are under `research-nature-final-audit/fixtures/`; exact source hashes, callbacks and ticks are in `fixture-index.json`.

| Fixture sequence | Native observations |
|---|---|
| `ready-idle-{baseline,lit,restored}.png` | Lit callback2059/tick4582, restored2068/4589. Pixel change confined to `(141,13)..(158,28)`. Next repeat begins tick4890. |
| `question-idle-*` | Available IDs1,2,6. ID1 off tick5640, on5659; ID2 off5664,on5683; ID6 off5688,on5706. Guess red settled5713, white5737. Next reminder begins6036. Callback boundaries can show a one-tick partial raster redraw. |
| `guess-idle-card-{0..7}-red.png` | Complete cycle starts tick9608. Next settled cards at9613,9619,9626,9631,9637,9643,9649; restored9655. Same eight-candidate cycle consumes **eight RNG calls**, one per cue. The initial restored source state was already inside an earlier reminder, so use the named complete second cycle. |

Fixture correction: card3 now uses callback2229/tick9626, which remains unchanged through2234. The previous callback2228/tick9625 was the intermediate frame after restoring card2 and before painting card3; it was identical to baseline. That partial callback is retained separately in `partial-callbacks/`, outside the settled fixture set. All eight settled candidate frames were checked against baseline: their changed-pixel counts are367,336,430,428,352,291,290,342, confined to the corresponding candidate thumbnail. The fixture index now includes exact source image, RGB hash, and final consecutive callback with identical pixels.

Missing guess reminders are also an RNG correctness issue: every surviving candidate consumes random(5), even though that choice only selects a sound.

## Question reveal sound and robot wait

Every newly offered question is drawn at overlay2 `3033`, then `3036` calls resident `5B9B`. That helper loads1008 (`5BA4`) and invokes nonblockingE5E2 (`5BA8`). The same cue follows every restored question in an idle reminder (`3D7E`). Current `enterTurn` originally exposed each question without the cue.

The automatic branch (`2B24..2BBC`) runs only when unanswered and either robot role or sole remaining correct candidate:

1. Wait60 ticks (`2B45..2B4D`, resident56DB).
2. **Only for robot role**, play **1011 through blocking57A9** (`2B54..2B63`).
3. Already guessing: choose secret. Sole correct candidate without guessing: enter guess mode. Otherwise rejection-sample random0..7 until an available question is selected.

The digital1011 resource has5116 samples at11000Hz, duration27.9054545 game ticks. It is not sufficient to fire the cue and make the decision in the same update. Using the existing blocking-audio duration convention gives28ticks. Ordinary native capture `robot-roll` shows third question settled tick6660, decision starts tick6749: approximately60+28ticks plus raster/control boundary. The named `questions-ready` and `decision-after-cue` frames bracket it. Human sole-candidate automatic actions do **not** play1011.

For robot-roll, RAM seed changes at selection tick6570,6599,6629, then at decision6749. Native selected question order is3,2,4. Source generates each question immediately before its own30-tick wait, rather than generating all three ahead of entrance animation. No intervening RNG call was observed in this transition, so the final selected set/seed is unchanged by moving these three calls earlier. The source order is still useful for exact trace timing.

## Exact start / roll RNG proof

Original helper2084 creates each player's eight cards, rejecting duplicate **attribute vectors**, then picks that player's secret index. After both hands, `228E..2297` always performs random(1) and writes currentplayer. Only afterward `229A..22A9` overrides currentplayer=1 for robot mode. The next roll switches to player0.

Captured ordinary options state seed **991CFBE5** yields:

- Player0 cards:47,89,67,55,58,17,40,24; secret2.
- Player1 cards:64,43,61,59,16,87,36,8; secret0.
- Final starting-player random(1)=1; resulting seed **6AA986A8**.
- First roll selects attributes **6,1,2**, ending seed **317A079D**.

All16 cards, both secrets, start seed and roll seed independently match the ordinary native RAM snapshots. Complete21-call start trace is in `rng-proof.json`. The existing source states are `research-nature/quiz-roll-capture/state/quiz-{options,ready,roll}.{state,ram-0}`. The new `start` capture repeats the ordinary Play click at45,96, starting from the same unmodified options state.

The masked random helper at resident11711 (D51:4201) makes one random(count−1) call, linearly probes already-used bits, and after a complete cycle resets the temporary mask to the exclusion mask before continuing. Nature passes exclusion0 and no callback. Its outer loop rejects an attribute already present in the current3-question offer. The existing runtime mask/probe algorithm has the same result and RNG count for this use.

## Packaged defaults

This project's original `source/reference-v1.zip` contains `TheTreeh/status.dat`; file offset **03B6 is2**, followed by help words0,0,1. Its untouched title→room→nature→quiz route, preserved in `quiz-roll-capture/run.json`, does not alter opponent options. Native options RAM at live3169:03FE is2, and the screenshot selects robot. The runtime's default opponent2 / help[false,false,true] therefore matches this package. A package with03B6=1 would need its own native startup proof; that is not the file used here.
