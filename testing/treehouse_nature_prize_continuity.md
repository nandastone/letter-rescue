# Animal-game prize and next-game continuity

## Original journey

`capture_nature_journey.py` restores one pinned original snapshot, selects a
friend game without help through its controls, asks a question, makes a wrong
guess, recovers, wins, reveals the other animal, chooses a magnifier prize,
starts the next game and returns to the room. All subsequent actions are mouse
inputs; the capture does not write RAM.

`output/treehouse/nature-native-journey-c/run.json` is the complete reference.
Its 11,126 video callbacks, captured audio and checkpoint images repeat the
preceding capture exactly (`nature-native-journey-repeat.json`). This proves
reference repeatability, not browser audio or timing parity.

## Two defects corrected

1. After revealing the other animal, opening the prize chooser redrew the
   winner's cards behind it. The original retains the other player's displayed
   scene while switching the logical player to the winner. `openPrizes` now
   takes the background before changing the logical player.
2. Creating a non-balloon room object must reschedule ambient activity, consuming
   one shared random draw (resident B8A3 calls BC43). `RoomCharacter.create`
   omitted that scheduling. Collecting the magnifier therefore generated a
   different next hand. The first native hand starts `[36,52,18,66,83]`; the old
   browser hand started `[44,36,52,18,66]`. Later rejection sampling equalized the
   ending seed, so a seed-only check could not detect the wrong deal.

The corrected routine also initializes the original object due time: current
tick by default, plus 48 ticks for balloons, with existing nut/food delays.

## Evidence and limits

- Baseline on delivered build `4144de5beb39`:
  `output/treehouse/nature-native-journey-check-b/report.json`.
  The chooser differs by 1,435 pixels; the next hand differs.
- Candidate `0d57eba7c465`:
  `output/treehouse/nature-native-journey-fixed-a/report.json`.
  All 13 checkpoints through the new game and return to nature match in full
  RGB and active gameplay/random state. The prize is present in the inventory.
- Focused regression:
  `output/treehouse/nature-prize-regression-a/nature_prize/report.json`.
  `verify_nature_prize.py` ends at return to nature and is registered in
  `verify_all.py`. It makes no claim about the later room return.

The browser starts from one native quiz/object/environment snapshot and then
receives ordinary canvas inputs at recorded integer game ticks. No checkpoint
state or random seed is injected after initialization. Each checkpoint image
must occur in that action's generated interval; this does not establish exact
presentation timestamps. Only active scene state is compared: the original
reuses quiz scratch storage after leaving, and question flags remain stale
when no question is active.

The complete journey **still fails at room return**: 717 pixels differ, largely
the balloon position, and random state differs. The fixture initializes the
calendar, clock, cloud, character needs and balloon position once, but complete
room timer initialization and transition timing remain unproven. The complete
failure is preserved separately; the focused prize regression does not waive it.

From the matching seed at return to nature, the browser consumes seven random
draws before the room checkpoint; the native checkpoint is ten draws later.
This is a lead for the room transition audit, not permission to insert three
arbitrary draws. Their owning operations still need to be identified.

## Regression coverage correction

The first candidate regression run passes all twelve individual board journeys
but fails the aggregate requirement that both winning and losing endings occur.
After the corrected startup random consumption, all twelve routes happen to
produce wins. No assertion was removed: the board suite now additionally runs
the explicit highest-goal money-payment loss route already covered by
`verify_board_money_loss.py`, and requires that route to end in a loss. The
first failing aggregate report remains at `nature-prize-regression-a/report.json`.

## Delivered build

Build `0d57eba7c465c0101d717f057f4ff4179e6e5566f9759ffd7a6236b087e9b515`
is served locally after **all 50 suites** passed together in
`nature-prize-regression-b/report.json`, including the thirteen board games and
the focused native prize comparison. All **183 environment states** also pass
(`nature-prize-environment-a/report.json`). Candidate, live file and HTTP bytes
match (`nature-prize-delivery-a/report.json`); the previous live file and
verification record are preserved there.

Strict timing remains 614/984 callbacks with 12 missing native displays
(`nature-prize-strict-a/report.json`). Full native chip and money-loss checks
were rerun on this build; their known failures remain in
`nature-prize-native-chips-a` and `nature-prize-native-loss-a`. Completion
verification additionally includes the failing full nature/prize/room journey.
No full-game completion or exact timing/audio claim is made.
