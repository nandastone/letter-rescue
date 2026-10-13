# Money loss: ending corrections and remaining full-game divergence

Delivered `63151140a6de463d86a3603f9de4b70210861e176f0abf50a9dde4c6a8e816b2`
corrects two independently demonstrated behaviors. All 77 registered suites
pass in one complete batch, plus all 183 environment states. The HTTP-served
HTML hash is verified; previous live files are backed up in
`board-mystery-payment-delivery-a`. Full parity remains false.

## Unaffordable payment label

The original final payment requests 28 cents but takes the player's remaining
22 cents. Its ending still says **Pay 28 Cents**. The browser changed the label
to **Pay 22 Cents** on entering the result phase. `drawRewards` now keeps the
requested amount for money payments, as it already did for chip payments.
The displayed coins and balance still reflect the amount actually paid.

## Mystery-node coin preparation

Original overlay 3 prepares both amount arrays before replacing the actual
payment array with greedy denominations. The browser already prepared the
actual amount, but omitted the unused second amount.

For a mystery node, the resolver calls resident `3BA6` at overlay `1CE8`.
Its unsigned remainder operation pushes a zero high word at the stack location
later read as the uninitialized amount delta (`34B5`, `[bp-6]`). Consequently,
both generated amounts equal the requested payment. The browser now prepares
the second amount in this case, in the original order after phrase selection.
This is derived from the operation, not a captured amount or seed constant.

The ordinary-input diagnostic `board-payment-observe-d` records the final
mystery payment: delta 0, both generated amounts -28, phrase selection, then
two coin-preparation random calls. The focused browser ending now matches the
original random state `1212983284` without resetting it after initial setup.

## Verification and semantic comparison

`verify_board_loss_ending.py` replays `step-30` to `step-31`, with actual pointer
input and no subsequent state/RNG assignment. Both complete images and compared
state pass in `board-loss-ending-fixed-b`. The same comparator fails the old
live build in `board-loss-ending-baseline-b`: seed mismatch and 219 differing
pixels. This bounded ending comparison does not prove the preceding game.

Original `20D1..20DA` changes the logical active player to the prize recipient,
while leaving the losing dashboard visible. The browser retains the displayed
player and calculates the recipient separately. The verifier now compares the
recipient meaning, reports `displayPlayer`, `loser` and `recipient`, and still
requires the complete original image. This does not waive dashboard differences.

## Direct payment dependency remains open

`verify_board_payment_second.py` isolates the earlier 18-cent direct payment
(`step-09` to `step-10`). Both images match, but random state fails on the live
build in two repeated runs. The subsequent roll changes from the original four
moves to five and the board's prize locations change, so this is an observable
gameplay discrepancy, not merely an internal-state metric.

Read-only diagnostics identify its source: the earlier cursor conversion leaves
its source offset plus 36 in SI. The cursor copy routine saves SI at the stack
location later reused as the amount delta. In `board-payment-origin-a`, the
cursor resource pointer offset is 10 and delta is 46; another payment has delta
50. These offsets depend on resource allocation. No constant delta, seed reset,
recorded draw schedule or partial CPU emulator has been inserted into the game.
The complete original loss journey remains failed until this dependency and any
subsequent discrepancies are resolved.

CPU tracing here is a bounded diagnostic of a reproduced game difference. CPU
instruction/register equivalence remains outside the completion requirements.


The uninstrumented control (`board-payment-control-a`) agrees with the traced
final payment in all 163 normal PNG/WAV files, input actions and callback
timeline; its ending image also matches the existing full-loss reference.
`board-payment-control-proof-b.json` records this. Proof A incorrectly included
41 trace-only live-scanout diagnostic PNGs in the file inventory and is retained;
no normal capture file is excluded in proof B.
