# Payment journeys and remaining random-state divergence

## Fresh browser losing game

`verify_board_money_loss.py` plays a fresh money/friend game at the highest
goal using visible controls. It prefers payments and smaller awards. It checks
zero-balance loss, the other player's prize, delivery, new-game restart, room
return and reload. It never assigns gameplay state.

`output/treehouse/board-money-loss-a/report.json` passes ten checks on live
build `4b59ef60e033`, reaching balances 0/5 after nine turns. The same check
passes on payment candidate `4144de5beb39` in `board-money-loss-b`.

## Original losing game and first correction

`capture_board_completion.py --seek-loss` restores the original board, uses
the original options controls to select friend/highest goals, and drives both
cars through payment routes. `output/treehouse/board-native-loss-a/run.json`
records a complete loss at balances 0/8 after 32 ordinary mouse actions from
the new-game snapshot. No RAM writes or debugger-injected calls are used.

The continuous browser replay initially diverges on the first payment at
`step-02`. Its amount is correctly 14 cents, but the message and following
random stream differ. The original amount generator always draws R(1) at
overlay 3 `37C4..37C8`, including payments; the browser returned early.
Consuming that draw corrects the message, full checkpoint image and seed.

- Full baseline: `board-native-loss-check-a/report.json`.
- Minimal baseline: `board-payment-baseline-b/report.json` (initial image
  matches, payment image and seed fail).
- Minimal corrected replay: `board-payment-fixed-a/report.json` (both full
  images and all compared state fields match).
- Full corrected replay: `board-native-loss-check-b/report.json`.

The full corrected replay matches through `step-06`. At `step-07`, the payment
image and balance still match, but random state differs. Subsequent roads and
turns diverge. **The full native money-loss journey is not yet reproduced.**

## Second discrepancy: first payment array corrected, unused second array open

The original money landing routine prepares coin arrays for *both* generated
amounts before deciding whether the landing is a payment (`1D74..1E29`). For
payments, the first array is later replaced with greedy payment coins. This
otherwise unused preparation can still consume random draws.

There is a further original quirk: the payment branch of `34B5` leaves the
second-amount delta local at `[bp-6]` uninitialized, then reads it in the common
pair calculation at `37D5..37F1`. The unused second amount varies in native
captures. For example, 26-cent and 18-cent payments leave second coin arrays
totalling 20 and 64 cents respectively. This affects the count of random draws
during unused coin preparation, despite no second payment being displayed.

The browser previously omitted this preparation; the 2026-09-29 follow-up below
restores preparation of the actual payment amount. The unused second array
remains unresolved. Do not claim its payment random
stream is fully equivalent, invent a constant second amount, reset seeds at
checkpoints, or use captured random schedules as runtime input. Preserve this
as an explicit remaining fidelity issue. Following the user's priority, the
next work is complete observable game comparisons before further investigation
of this scratch-state quirk.

Native loss also toggles the logical active player to the prize recipient while
leaving the losing dashboard visible (`20D1..20DA`). The browser keeps the
displayed player and calculates the other prize recipient separately. A future
loss-end comparison must compare both meanings explicitly rather than treating
the two storage layouts as identical.

## Delivery

Candidate `4144de5beb39` is now served after all 49 regression suites and 183
room-environment states passed. The full chip game independently confirms the
payment random-draw correction through victory (see `treehouse_board_chip_journey.md`).
Both remaining full-journey failures are retained in completion verification
and required by the completion gate. Delivery evidence:
`output/treehouse/board-payment-delivery-a/report.json`.

## Actual payment coin preparation (2026-09-29)

The original routine at `1D9A..1E23` takes the absolute value of each amount and
prepares denomination counts. For the actual 26-cent payment, the 25-cent coin
causes one random draw, even though greedy payment coins replace this array
before display. The browser now calls its existing coin-preparation routine for
the actual payment amount in money mode. The call follows message selection,
matching the original operation order. Chip payments are unaffected.

The isolated ordinary-input replay from `step-06` to `step-07` fails on the old
build only in random state; both images already match. With the correction,
both full RGB images and all compared gameplay/random fields match. Evidence:
`board-large-payment-baseline-a` and `board-large-payment-fixed-a`. This focused
check is registered as `verify_board_payment_large.py`.

The complete loss replay on candidate `c6795ecc633c` now matches continuously
from the initial state through `step-09`. At `step-10`, the visible 18-cent
payment and balance still match, but the original also prepares an unused
64-cent second amount. Its 50-cent coin consumes one additional random draw:
browser seed 2527103840 advances to original seed 2204794019. Later turns still
diverge. Evidence: `board-large-payment-loss-a/report.json`.

This is a bounded correction to a known original gameplay operation. No
checkpoint seeds, captured schedules, or constant scratch-memory values have
been inserted into the runtime. Full money-loss fidelity remains open.

Delivered `c6795ecc633c` after all 65 suites ran together and passed, plus 183
environment image states. Known strict nature and chip partial-redraw failures
were rerun and retained. Served/candidate hashes agree; previous build and
verification are backed up in `board-large-payment-delivery-a`.
