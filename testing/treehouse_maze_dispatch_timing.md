# Maze sound dispatch timing audit

## Current result

The served build remains `d2ecc31d6a0a8f254c519335ffa16739c566806f915fe75f5685203274f06d13`.
There is no runtime correction or new playable delivery in this checkpoint.

Two new complete ordinary-input replays (`maze-ending-baseline-a` and
`maze-ending-clock-a`) retain all eleven matching RGB checkpoint images and
gameplay/random states. Both fresh mouse/touch automatic-hint checks pass.
All 184 observed native sound sources/rates occur in order within their player
input intervals. The existing ten raw checkpoint-split misses remain.

`audit_maze_dispatch_timing.py` now exposes dispatch timing separately from
source coverage. The browser observer records its clock origin explicitly.
The native origin is the initial snapshot tick (5158), not a fitted offset.
The audit binds the HTML and input reports by SHA-256 and verifies native
control equality. It never changes runtime state or inserts delays.

### Repeated sounds need explicit ambiguity

Greedy source matching initially suggested two errors of 395 and 445 ticks.
Those pairings were not unique: automatic auditions can replay the same source
and rate within one input interval. The first report remains preserved as
`maze-ending-clock-a/dispatch-timing.json`.

The revised audit finds the earliest and latest feasible ordered source/rate
matches without considering timestamps. It lists every possible dispatch
between those bounds. Eight of 184 observations are ambiguous and cannot prove
an individual dispatch-time difference. Of the 176 uniquely paired observations,
76 share the observed native tick; the remaining differences range up to 25
ticks early. See `maze-ending-clock-a/dispatch-timing-b.json`.

## Final-note route, anchored elapsed ticks

These events have unique source/rate sequence matches:

| Event | Native observed tick | Browser dispatch tick | Browser minus native |
|---|---:|---:|---:|
| Frog disappears after the last earned note | 12934 | 12933 | -1 |
| Song chooser opens | 13029 | 13023 | -6 |
| Collected melody begins | 13077 | 13071 | -6 |
| Collected melody's eighth note | 13133 | 13127 | -6 |
| Song chooser closes | 13159 | 13147 | -12 |
| Player jumps | 13204 | 13193 | -11 |
| Frog appears for departure | 13272 | 13261 | -11 |
| Full victory song begins | 13834 | 13811 | -23 |
| Full victory song's last observed note | 14010 | 13987 | -23 |

The eight collected notes have matching eight-tick onset intervals. The final
song has a stable 23-tick offset except one callback at 24 ticks. This evidence
rules out changing the song tempo as a correction for this route. It localizes
the missing time to transitions around those sequences; it does not yet prove
which drawing, resource, or waiting operation accounts for each increment.

The native observer samples active sound at video callbacks, rather than
instrumenting every start. Its observed tick is not an exact start timestamp.
Consequently even perfect observed-tick agreement would not establish waveform
or sample scheduling parity. This report fails observed-tick alignment and
explicitly keeps full audio parity false.

## Next bounded investigation

Compare the disappearance-to-chooser boundary, collected-song cleanup and
victory-scene construction against the original's calls. Relevant overlay-1
boundaries are `6C8F..6DD0` (collected song), `7C84..826C` (chooser), and
`862D..8983` (victory transition), followed by `84C8` (full song).
Change the responsible operation once demonstrated; do not apply the measured
6/12/23-tick offsets as runtime constants. Chip partial clearing, money-game
randomness, other strict timing failures and full-session coverage remain open.
