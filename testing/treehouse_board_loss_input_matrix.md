# Money loss through repeated ordinary play

## Scope

The explicit payment-loss regression previously exercised only a desktop
friend game. It now covers friend and robot with both mouse and touch, from
fresh character selection through a payment loss, prize delivery, new game,
room return and reload. Each session uses visible controls. The test reads
legal paths and reward amounts to choose actions and advances animation time;
it does not assign board state or random state.

`verify_board_money_loss.py` remains registered in `verify_all.py`. Its shared
implementation is `verify_board_journeys.py`; the ordinary thirteen-game
coverage remains intact.

## Findings

The first expanded attempt, `board-loss-input-matrix-a`, passed both friend
routes but failed its expectation of an immediate robot payment loss. The
robot legitimately reached its winning balance first. This was a coverage
assumption, not a demonstrated game defect. That failed report is retained.

The test now completes prize selection and delivery after each ending and
continues the naturally generated next game, with a bound of eight games.
It still requires an actual payment loss before accepting the session. It
checks every intervening ending, winner/loser balance, prize recipient,
delivery, and new-game readiness.

On build `a89b3f65ac50ce1a548fa6618f795261e0a79507c057e3a87b4a305d9747d322`,
`board-loss-input-matrix-b/report.json` passes 101 checks across four sessions.
Each friend session loses in its first game; each robot session reaches the
payment loss in its seventh game. Thus sixteen complete games are exercised.
Mouse and touch reach the same final balances for each opponent. There are
no runtime changes in this follow-up.

## Limits

This establishes browser input and repeated-game integration for these routes.
It is not a paired original run, a real-time playback check, or audio parity
evidence. The pinned-original money-loss comparison still diverges at its
direct payment; that failure remains open. See `treehouse_board_loss_ending.md`.
The delivered 89-suite batch predates this stronger test; subsequent focused
results are recorded separately rather than described as another complete batch.

## Repetition and shared-verifier regression

`board-loss-input-matrix-c/report.json` repeats all 101 checks with identical
actions, endings, compared states and four final full-page PNGs.
`board-loss-input-repeat-a.json` records the equality checks.
`board-loss-input-regression-a/report.json` passes all 126 checks across the
existing thirteen money/chip journeys, including both carry and borrow.
