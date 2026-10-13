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

## Godot scene ownership through board options — 2026-10-13

Added GDScript palette/shape/animation ownership and lifecycle modules for the
title, child selection, initial room, board transition and initial board/options
construction. The normal source extractor now includes the original EXE palette
masks, rectangles, SCR code and child archives used by these modules. Palette
byte updates explicitly preserve Godot PackedByteArray copy-on-write semantics.

The sequence generates requests from these source structures and current game
fields. It releases saved character backgrounds, animation objects, temporary
screens, sound locks and source-cache links at the corresponding semantic
boundaries. Board transition display/sound/callback events come from the actual
Godot SCR interpreter: the ring completes 18 displays; the bubble completes 13
displays, sounds 10034/10035 and callback [0,0]. Initial board layout is produced
by the actual Godot BoardGame rules.

Evidence under `testing/output/treehouse/`:

- `godot-resource-board-c/report.json`: **377 checks pass**, including all 366
  native allocator/DOS/catalog/source-payload comparisons through initial Money
  options, and 11 gameplay/interpreter/ownership checks. Uses the normal asset
  bundle for both resource metadata and board tables.
- `godot-resource-room-girl-b/report.json`: **209 checks pass**, including all
  204 native comparisons through girl selection and room construction, and
  five ownership/cache checks, also using the normal asset bundle.
- `godot-resource-startup-f/report.json`: all **108 startup checks** remain
  passing after the shape/catalog integration.
- `godot-resource-scene-assets-a.log`: normal asset generation succeeds with
  all 2,337 shapes and 356 scripts. Current asset SHA-256 is
  `a83014cbf1c508a975dfaed72b5451fab8ebf561b9b519ba9e51d14f8cbd1fb1`.

Earlier passing title/room/transfer checkpoints remain as
`godot-resource-title-boy-a`, `godot-resource-room-boy-a`,
`godot-resource-transfer-a`, `godot-resource-board-a/b` and
`godot-resource-room-girl-a`. They cover intermediate versions or direct
extraction; the current reports above bind the final source and normal assets.

Limits: these are headless resource ownership comparisons at semantic completion,
not live browser gameplay or elapsed-time proof. The route supplies cloud 5,
two visible credit changes, noon, the five source-defined room objects, and one
native RNG seed at board entry. Those are explicit test inputs; they must not
become runtime fixture schedules or seeds. Converted shape/surface pixels remain
the graphics decoder's responsibility and are outside these resource comparisons.
The modules are not yet hooked into the playable event loop. The preview remains
the prior scanout build; full completion and its source/export check still fail.

Next is generating board start, turn, sound and redraw resource events after
options dismissal, then connecting the live lifecycle and deriving the payment's
cursor-dependent second amount. The full losing Money replay, seven native
discrepancies, timing and waveform work remain open.


## 2026-10-13 — Godot board options to first-turn readiness

The source-generated Godot resource chain now continues through Play: the click
sound, preference dismissal, fresh board draw, pawn saved background, dashboard
animation and three opening prompt flashes. Board start uses the production
BoardGame preparation and continues its RNG without reseeding. Dashboard sound
comes from the production SCR interpreter. Click completion is an explicit
caller event, as are animation completion and each prompt draw; this component
comparison does not claim an elapsed-time implementation.

Evidence under `testing/output/treehouse/`:

- `godot-resource-play-c/report.json`: **415 checks pass**, including 402 native
  allocator/DOS/catalog/modeled-payload comparisons and 13 focused, interpreter
  and gameplay checks. Uses the normal generated asset bundle.
- `godot-resource-startup-g/report.json`: **108 startup checks pass** with that
  same bundle.
- `resource-board-play-controls-a.json`: **468 checks pass** comparing the Play,
  restart, redraw and dashboard observers against the plain control. Ordinary
  PNG/WAV/RAM files, callback timelines and input/source metadata agree.
- `resource-board-play-a`, `resource-board-restart-a`, `resource-board-redraw-a`,
  `resource-board-dashboard-a`: new paired original snapshots, obtained by
  restoring the existing fixed-clock options state and clicking Play normally.
- `godot-resource-play-a/report.json`: preserved failing first candidate. Its
  three failures were the click sound's lock bit, which the original releases
  during the button flash. The corrected model exposes sound completion to its
  caller. `godot-resource-play-b/report.json` preserves the intermediate pass.
- `godot-resource-play-assets-a.log`: normal asset generation retains all 2,337
  shapes and 356 scripts. Asset SHA-256:
  `032f0d9a81ac39c473dc5bc35d9c17f1ce9184270a8fb51c4997513f12bb78a8`.

Limits: one board-entry seed and room/credit/sound completion semantic inputs
remain explicit fixture inputs. Converted surface pixels, live lifecycle,
absolute frame timing and audio waveform parity are not proved by these checks.
No native discrepancy or issue was closed. The preview still serves the prior
scanout export. Next: roll/movement/landing/payment lifetimes, live integration,
then the full losing Money replay and a fresh playable export.


## 2026-10-13 — First roll, restored button flash and refreshed preview

The Godot board now reproduces the original question-mark button flash before
rolling: red for 12 ticks, white for 12 ticks, then eight faces at their authored
6-through-13-tick intervals, followed by three 12-tick pawn blink pairs. The
new production events drive the resource model's prompt surfaces and saved
pawn image. Starting from the existing generated startup/board chain and its
one entry seed, the roll result and final RNG agree without reseeding.

`godot-resource-roll-c/report.json` passes **443 checks**: 426 native resource
boundary comparisons and 17 gameplay/interpreter/focused checks. The first roll
matches native relative PIT ticks for every prompt draw and all nine sound
dispatches, completing at tick 172. This is logical-event evidence; absolute
scanout timing and audio waveform parity remain open. The original observers
match their ordinary control in **230 checks**. An initial candidate's closure
ownership leak is preserved in `godot-resource-roll-a`; weak ownership fixed it,
and attempts B/C terminate cleanly.

The new `godot-roll-build-a` Web export passes **21 browser checks** across
Money and Chips: options, roll, legal movement, persisted mode and room return.
The resource test and Web test have build-bound evidence envelopes. All nine
served files match the immutable export at http://127.0.0.1:8768/ (PID 6764).
PCK SHA-256: `b1f96ec656ea3d6dc6832210ae31d3f6879250be1ea08feeb0294cb2ac1927fd`.

`godot-roll-money-loss-a/report.json` retains exactly the previous checkpoint
pixel counts and state differences: 12/33 images, 11/33 states, first RNG
mismatch at step-10, losing ending not reached. No issue was closed. Resource
lifecycle integration, movement/landing/payment lifetimes and seven native
failures remain open. Prior suite results need refreshing on this export.

Automatic approval review rejected the bulk completion-index replacement
without a detailed reason. The existing index was preserved; the new export,
hashed evidence and remaining work are recorded in
`testing/treehouse/roll-build-progress.json`. The remaining-work ledger points
to that record. No acceptance was promoted or historical evidence discarded.
