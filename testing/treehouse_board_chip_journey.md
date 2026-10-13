# Complete native chip-game comparison

## Capture and replay

`capture_board_completion.py --chips` restores the original chip/friend game
once, then plays 48 ordinary mouse actions through victory. The capture includes
three required carries, four wrong-stack attempts, two payment landings, and
the ending at balances 35/58. It records 98,428 video callbacks with snapshot
protocol 2. No native RAM writes are used.

Reference: `output/treehouse/board-native-chips-b/run.json` and `state/`.
The earlier `board-native-chips-a` attempt was explicitly stopped because its
capture harness used money reward scene 16 instead of chip reward scene 24.
It is incomplete evidence, recorded in `aborted.json`.

`verify_board_native_chips.py` initializes the browser from that first snapshot
only. All subsequent choices use real canvas inputs. The comparison checks
mode, opponent, goals, players, roads, balances, movement, directions and random
state after each action. Native images must appear among actual generated
frames. It waits at modal exchanges, allowing the captured wrong/correct stack
clicks to be replayed instead of automatically accepting a trade.

## Results

- Previous live build `4b59ef60e033`: the first payment at `step-23` diverges in
  random state and image, followed by different roads, turns and ending.
  Evidence: `output/treehouse/board-native-chips-baseline-a/report.json`.
- Payment candidate `4144de5beb39`: all 49 state checkpoints and the final ending
  check pass. The full game reaches the original 35/58 result without resetting
  intermediate state or random values. Evidence:
  `output/treehouse/board-native-chips-check-a/report.json`.
- 48 of 49 full RGB checkpoint images match exactly. **The full visual
  comparison still fails** because `step-15` contains a partial redraw.

## Remaining trade-flash redraw

Native callbacks 34072–34074 show the complete red flash. At 34075, the saved
checkpoint, clearing has reached the lower portion of the stack: rows 37–49
remain red at x275. At 34076 the flash is completely cleared. The browser
draws the complete clear, so it never generates that intermediate partial
rectangle. The checkpoint differs by 312 pixels.

Machine-readable adjacent-frame evidence:
`output/treehouse/board-native-chips-check-a/partial-redraw.json`.

No checkpoint was dropped, shifted or replaced with a nearby image. The failed
visual result remains recorded. These observations establish complete gameplay
state/random continuity for this route, not native presentation-time equality,
audio waveform equality, all routes or fresh-entry random equivalence.

## Godot display diagnosis — 2026-10-05

The earlier description of a partial clear describes the captured image, not
proof that the original fill routine clears the rectangle bottom to top.
The pinned reference's VGA PART renderer reads four 50-row bands independently.
The row-50 boundary is consistent with a top band read before clearing and
the next band read after clearing.

The production Godot presenter now reads independently rendered framebuffer
commits on that four-band clock. The unchanged full Chip replay still passes
49 gameplay/RNG states and 48 full images. Its 420-tick observation window at
step-15 contains four flash-to-clear transitions but no matching mixed display.
Evidence: `output/treehouse/godot-chip-scanout-observe-a/report.json`.

For each of those four transitions, combining the old top 50 rows with the
new lower rows gives the native checkpoint exactly. The new frame already
contains the first exchange shape, so a separate missing clear-only stage is
not needed to explain these pixels. This diagnostic composition is **not a
frame presented by the game** and does not resolve the failed checkpoint.
Evidence: `output/treehouse/godot-chip-scanout-phase-a.json`.

The observed transition ticks have display phases 2.540, 0.546, 12.819 and
10.824 ms; the first two band reads are at 3.178 and 6.356 ms. The native
checkpoint requires the clear to occur between those two reads. The replay
settles actions rather than following native input times, and runtime drawing
costs/absolute phase remain unreconstructed. Do not fit a phase offset, extend
the matching window, or insert a captured delay to count this failure as fixed.

Separately, the production Godot presenter matches all 306 native question
animation callbacks when supplied explicit native clock fixtures and existing
independently generated reference-clone source images. An atomic-frame baseline
matches 291/306, detecting removal of scanout. This is presenter component
evidence only: `output/treehouse/godot-scanout-native-b/report.json`.
