# Initial board and options resource ownership

Checkpoint: 2026-10-05. This component work is not a delivered payment fix.

## Source-derived implementation

`OriginalBoardResources` continues the generated startup state after room
release. Overlay 3:0000 loads six palettes. Its 0625 routine creates a temporary
screen, draws the board and current-player backdrop, paints the balance stacks,
exit control, board nodes, heading and hint, then releases the screen. AC5
creates the options surface and palette; EAE, F64, 107D and 13FB paint its
selection marks, icons and goal labels before releasing that surface.

The existing `BoardGame` algorithm supplies the initial nodes, directions,
balances and board types. In this check it receives **one native board-entry
RNG seed**. These generated fields and its ending RNG state match the original.
This is an explicit semantic input; it does not establish continuous startup
RNG or clock behavior. No captured heap, allocation request stream, resource
addresses or shape-call list initializes or drives the resource model.

The implementation currently covers the initial Money/robot settings and the
default central-room route. Settings changes and subsequent game turns require
additional resource event coverage. The resource module remains unbundled.

## Evidence

All report paths below are under `testing/output/treehouse/`.

- `board-start-resource-check-a`: 348 native comparisons and ten focused checks
  pass through palette loading and initial backdrop preparation.
- `board-start-resource-check-b`: 360 comparisons and eleven focused checks
  pass through the complete board draw and options palette preparation.
- `board-start-resource-check-c`: retained failure; two allocation-state
  comparisons fail after painting options, while resources and payloads match.
- `board-start-resource-check-d` and final `board-start-resource-check-e`:
  366 comparisons and twelve focused checks pass after adding temporary
  surfaces for the three goal labels. Resident 3CED owns these surfaces;
  transparent 3CB0 text used on the board does not.
- `board-start-room-regression-a`: 204 comparisons and six focused checks pass
  for girl startup/room construction with the updated verifier.
- `board-start-control-a.json` and `board-options-control-a.json`: each passes
  439 plain-original image/audio/RAM/callback and common-observer comparisons.
- `board-start-resource-build-a/index.html`: identical to the delivered
  `27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413` build.

The new captures are `resource-board-start-palette-a` and
`resource-board-options-a`. The options observer uses the pinned overlay slot
and verifies that slot against a unique original-code signature after capture.
Observer addresses are never runtime model inputs.

## Faster verification

Archive and payload bytes cross Playwright as base64 strings rather than one
protocol object per byte. Passing state comparisons retain a canonical SHA256;
failed comparisons still include complete expected/actual state. Every field
is still compared before the report is summarized. All first 360 comparison
results and state hashes are identical between checks B and C. Measured elapsed
time decreased from 113.3 seconds to 32.0 seconds for those runs, although C
also added the final options comparison. Historical reports are preserved.

## Remaining integration

Reproduce starting-game and subsequent board resource lifetimes from semantic
gameplay events. Replace the remaining observed requests in the older payment
lifetime harness. Connect live rendering/input/RNG events, then verify a full
money-loss game. Converted pixels and exact animation/audio timing are outside
this resource check and remain required by the overall goal. The full-game
completion gate must remain failed while those requirements are open.
