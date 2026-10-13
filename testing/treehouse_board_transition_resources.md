# Board-transition resource preparation

## Ordinary original route

`capture_resource_startup.py --fixed-clock --choose boy --board` follows the
existing cold boot and character-selection input, then clicks the board inlet
at the first completed room display. It reaches the original Money/robot
options panel. Its fixed input waits are capture data only, never runtime
resource or timing inputs.

`resource-room-board-transfer-a` records transfer entry/return ownership;
`resource-room-board-animation-a` records the two transition constructors as
well as the earlier startup constructors. `resource-room-board-control-b`
repeats the route without observers and asserts arrival in options scene 10.
All 439 control checks pass in `room-board-control-b.json`, including ordinary
images, audio, RAM, callback timeline and every common operation event.

The generated first-room ownership matches the original at transfer entry.
`room-board-entry-seam-a.json` checks the complete arena, near heap, DOS state,
file list and catalogs. The continuous verifier additionally checks modeled
source/font/cursor/sound payloads at that boundary.

## Implemented preparation

`OriginalStartupResources.beginRoomTransfer` follows main 5204 through the
opening ring constructor: load palette 980, start looping sound 1015, select
the wrapper's busy cursor, obtain an independent SCR copy, and preload the
animation's images/surface/backup from the original script.

Two missing inputs/operations were exposed by this integration:

- Digital sound preparation requires the selected device's supported rate
  range. The pinned Sound Blaster driver returns it at executable 21C10/21C13;
  resident 19888/1988C stores it. `resource_inputs()` now derives those bounds
  from the executable, and the startup state carries them to sound loading.
  This does not implement resampling for unsupported rates.
- Constructor C74F composes the initial animation background before restoring
  palette flags. For the opening room ring, C9ED draws the standing child.
  `OriginalAnimationMemory.prepare` now exposes `composeInitial` for this
  caller-owned work. The default new-game objects do not intersect the ring;
  arbitrary relocated foreground-object composition is not covered here.

## Evidence and limits

All evidence paths are under `testing/output/treehouse/`:

- `transfer-resource-baseline-a`: transition preparation was absent.
- `transfer-resource-check-a`: missing device limits prevented digital sound
  preparation; the failure is retained.
- `transfer-resource-check-b`: preparation reached the constructor but omitted
  its child composition, leaving two allocator comparisons failed.
- `transfer-resource-check-c`: all 264 native comparisons and six focused
  ownership/cache checks pass continuously from generated startup.
- `transfer-animation-regression-a`: all 24 comparisons over six earlier
  constructors and 80 shape loads pass with the optional composition hook.

The native before/after states are offline expectations. The model consumes
executable/platform/archive inputs and the previously documented semantic
entrance events. It does not consume native allocation requests, resource
addresses, frame schedules or initial heap RAM.

This checkpoint ends after the opening-ring constructor. It does **not** prove
the transition's playback/cleanup, room teardown, board entry or redraws,
complete payment behavior, live event integration, converted pixels, or exact
animation/audio timing. Those remain required. No payment correction is
delivered by this component work, and full clone parity remains false.


## Completed transition resource lifecycle (2026-10-05)

The resource model now continues through the opening ring, bubble, inlet
closure and room release. The verifier uses the playable Animation interpreter
to produce the authored displays, sounds and callback; it does not inject a
recorded frame schedule. Resource hooks select the normal cursor, compose the
child at each ring display, release animation/script ownership, replace the
child backing while the ring is visible, and open the board inlet.

The first new comparison (`transfer-resource-check-d`) failed seven fields.
Its catalog differences identified exactly two missing SND resources, 10034
and 10035. Main 4338..43A7 loads PSL1103, visits its sound IDs in authored order,
prepares each sound, then frees the PSL source. Adding this operation made all
276 native comparisons and seven focused checks pass in check E.

Check F extends through sound replacement and transition cleanup: all 282
comparisons and nine focused checks pass. Check G additionally follows main
3217: release room-object backgrounds in list order, release theater and child
backgrounds, mark the four room palettes discardable, and pack the heap. All
294 comparisons and ten focused checks pass. Earlier startup boundaries remain
part of each continuous check.

`resource-room-board-release-a` supplies two new original snapshots at 3217
and 3289. Paired with the earlier animation capture and plain control,
`room-board-release-control-c.json` passes all 439 comparisons. Control B was
an invalid single-capture invocation: ordinary outputs matched, but its required
independent event comparison lacked a second capture. That report is retained.

Evidence bundle: `transfer-resource-evidence-b/report.json`. The fresh build C
matches the delivered playable SHA. The resource module remains unbundled.
This work does not deliver a payment fix. Arbitrarily relocated objects, board
initialization/lifetimes, live event hooks, converted pixel contents, exact
audio/presentation timing, and full-game replay remain unverified or unfinished.
The old section ending at the opening constructor describes the earlier checkpoint.
