# Money payment: bounded resource dependency

## What this establishes

The payment discrepancy can be described without emulating CPU instructions.
For a direct payment the original calculates an unused second amount using
`cursor source offset + 36`, with the ordinary pair-direction random draw
selecting addition or subtraction. Mystery payments use a zero delta. Both
amounts go through randomized coin preparation, even though only the first
payment is displayed. The actual displayed payment then uses greedy coins.

An independent calculation matches all nine payments in the complete original
loss recording: requested/paid amounts, displayed coins, unused coin arrays
and final random states. `board-payment-dependency-a.json` passes 36 checks.
Each calculation starts from its own native payment input, including its
cursor location. This is **not** a continuous browser-game verification.

| Checkpoint | Requested payment | Unused amount | Cursor source offset |
|---|---:|---:|---:|
| step-02, mystery | 14 | -14 | 10 |
| step-05, mystery | 23 | -23 | 10 |
| step-07 | 26 | 20 | 10 |
| step-10 | 18 | -64 | 10 |
| step-15 | 23 | 23 | 10 |
| step-20 | 22 | -68 | 10 |
| step-24 | 15 | 35 | 14 |
| step-28 | 29 | -79 | 14 |
| step-31, mystery | 28 (22 available) | -28 | 14 |

The current behavior omits random consumption at four of these direct payments.
A fixed offset of 10 happens to produce the same final random states in this
recording, but produces the wrong unused arrays at two checkpoints. It is not
a justified general solution and has not been inserted into the game.

## Resource identity and movement

The normal pointer is embedded `CURS 0`, found in the resident catalog at
image `31660`, record 25. It is absent from the loaded DAT catalogs at DS:204E.
Its handle is 25630 throughout this recording, and the cached payload is checked
byte for byte against the pinned executable's 68 cursor bytes. It stays at
source offset 10 through step-20 and moves to offset 14 during step-21.

Read-only operation capture identifies the trigger: loading board SHAP 4001
allocates 24,961 converted bytes after a 64,000-byte backing surface allocation.
The allocation's fallback packing request is 24,968 bytes. Packing moves twelve
resources, including the cursor, whose header moves from physical address
409892 to 385976. A second 25,932-byte packing request moves another 110
resources. Neither operation replaces the cursor handle or changes its payload.

## Independent implementation

`OriginalHeap.pack(payload)` reconstructs resident 6652's forward packing:
coalesce a hole, move an unlocked following resource into it, preserve its
size/padding and payload, update its handle, then advance the hole. Locked
resources and raw allocations remain fixed. Stop once the requested space
is available or the arena is exhausted.

`board-heap-packing-fixed-b` compares both complete operations with before/after
native fixtures. All block geometry, flags, payload hashes, handles, search
cursor and available-byte results match, including all 122 moves. The baseline
fails because this operation was absent. This helper is not included in the
playable bundle yet; it cannot supply the initial resource state by itself.

The existing 52 heap preparation cases and five boundary checks also pass in
`board-heap-packing-regression-b`. That command explicitly uses `--state-only`:
complete allocator state is checked, without instruction counts. Attempt A
hit an existing instruction verifier API error (`OriginalGraphicsWork.repeatString`
is absent); this is retained as a separate failed diagnostic, not represented
as a passing instruction test. The default verifier behavior is unchanged.

## Controls and retained failures

- `board-cursor-relocation-a`: ordinary inputs with resource-boundary observations.
- `board-cursor-relocation-control-a`: identical inputs without observations.
- `board-cursor-relocation-c`: adds paired allocator snapshots using an existing
  diagnostic core. All 244 ordinary PNG/WAV/RAM and callback control checks pass
  in `board-cursor-relocation-control-proof-a.json`. Final images also match
  the prior original step-21 image. Extra `live/` scanout images are diagnostics.
- Capture B stopped because its selected DLL lacked the snapshot API. It is
  preserved. Capture A's `heap.relocate` label at resident 6FD8 was inaccurate;
  that address is coalescing. The tool and capture C correctly name it.

The current playable file is unchanged:
`d2ecc31d6a0a8f254c519335ffa16739c566806f915fe75f5685203274f06d13`.
A fresh build in `board-payment-dependency-build-a` produces the same hash.
`board-full-loss-current-a` still fails: 12/33 images and 11/33 states match;
the first state discrepancy is step-10 and the next roll visibly differs.
The matching isolated loss ending does not establish this complete game.

## Required integration

Generate the cursor source location from resource lifetimes during startup,
activity transitions, and board redraws, then use that generated offset in
payment preparation. Original RAM/offset schedules must stay offline fixtures.
The verified packing operation supplies one missing rule; it does not close
the lifetime integration or full-game discrepancy. No CPU instruction-count
requirement or fixed random-state adjustment has been added.

## Complete allocation and background-load integration

The allocator now tries forward packing when its ordinary searches find no
space. This follows the original operation order: packing precedes cache
eviction. `board-resource-allocation-fixed-b` reproduces the complete 24,961-byte
handle allocation, its returned handle, all allocator/handle metadata and
twelve resource moves, including the cursor. The baseline failed on this
pressure path. Fixed attempt A incorrectly deferred packing when discardable
resources existed; its failure is retained and the ordering is corrected.

`board-background-loading-check-c` extends this to the whole SHAP 4001 load.
Starting from one offline allocator fixture and the pinned resource bytes, it
generates allocation, temporary decoding storage, cleanup, resize and flag
restoration. The final allocator and handle state matches the original. This
comparison checks existing payload hash preservation; newly converted image
bytes remain the renderer's separate responsibility.

Source-cache behavior is now independent of instruction accounting.
`OriginalResourceLoading` derives resident/reload/new-source decisions and
ownership flags directly. Its optional `observeWork` switch preserves existing
diagnostic consumers. The complete background-load check runs with that switch
off and never loads any instruction-work module. Both modes also pass all nine
cache/layout checks and the 2,337-shape header inventory in
`board-resource-semantic-shapes-a` and `board-resource-observed-shapes-a`.

The existing continuous resource-state regression still passes all 104 memory
checkpoints, 79 generated shape loads, twelve scene phases, 2,399 generated
sound loads and four focused checks (`board-resource-semantic-lifetimes-a`).
It begins with an offline native fixture and retains 159 observed allocation
requests and 43 frees; it does not prove generated startup or whole-game
resource behavior. Its optional instruction comparison flags are disabled.

The new allocation and whole-load reference captures preserve the plain
control's ordinary images, audio, RAM and callback timeline in all 248 checks
(`board-resource-controls-a.json`). Both end at the same original step-21 image.

Retained failed attempts: `board-background-loading-check-a` omitted a work
module required by the then-coupled loader; check B passed with it present.
`board-resource-allocation-lifetimes-a` selected a reference without the full
sound route; B and the current semantic lifetime regression use the complete
reference. These failed attempts are not reported as passing runs.

The fresh `board-resource-semantic-build-a` remains byte-for-byte identical to
the served `d2ecc31d6a0a` build. **No payment fix has been delivered by these
component changes.** The full loss-game failure remains open. The next required
integration is to generate initial resource ownership and subsequent scene
lifetimes so the payment's cursor offset comes from the running model, not an
offline snapshot. Internal instruction equality remains outside that task.

Initial arena constructors and repeatable cold-boot observations are now
implemented and checked in [resource startup](treehouse_resource_startup.md).
The near heap is generated from executable stack parameters. The conventional
arena still takes the DOS allocation result as an explicit platform input;
growth and complete startup resource requests remain required. The reference
clock correction is confined to new startup captures and does not modify the
existing money-game recording or playable file.


## Character-selection resource ownership (2026-09-29)

Resource ownership now continues through actual boy/girl selection, both departure scripts, the chosen climb, and cleanup of four saved backgrounds and two palettes. Each variant passes 192 native comparisons and six focused checks from generated startup; plain-original control comparisons pass 423 and 407 checks. The verifier supplies the default cloud and two observed visible credit-change events before selection; their timer schedule and live renderer hooks remain unintegrated. No captured allocation requests, resource addresses or initial heap RAM drive the model. Native comparisons A/baseline failures are preserved. The playable build is byte-identical and the money-loss divergence remains unresolved.


## Board-transition resource preparation (2026-09-29)

Generated startup now matches the ordinary board-transition entry and opening-ring constructor. All 264 native comparisons and six focused checks pass. Device rate limits are derived from the original Sound Blaster backend; the constructor now includes caller-owned initial child composition. The six earlier constructor cases retain 24 comparisons and 80 shape loads. Ordinary controls pass 439 checks. Playback/cleanup, room teardown, board lifetimes, live event integration and complete payment replay remain required. Playable bytes and the money-loss failure are unchanged. See `testing/treehouse_board_transition_resources.md`.


## Outgoing board transition and room release (2026-10-05)

Generated startup now matches the complete outgoing board-transition resource lifecycle and room release: 294 native comparisons and ten focused checks pass. The shared SCR interpreter drives the ring and bubble, including both authored sounds and the child-removal callback. Added PSL sound preloading, child-backing replacement, board-inlet ownership, sound replacement, animation cleanup and room teardown. Original observer controls pass 439 checks. This is default central-room resource ownership at semantic completion, not pixel/audio/timing parity. Board initialization, live event integration and the complete payment replay remain required. The playable file and money-loss discrepancy are unchanged. See `testing/treehouse_board_transition_resources.md`.


## Board initialization resources (2026-10-05)

Generated resource memory now reaches the initial Money/robot options screen: 366 native comparisons and twelve focused checks pass, including the complete initial board draw and options resource lifecycle. The existing BoardGame algorithm reproduces nodes, directions, balances, board types and final RNG state from one native board-entry seed; that seed remains a stated semantic input, so upstream RNG/clock integration is not established. Girl startup/room regression retains 204 comparisons and six focused checks. Both new capture-control reports pass 439 checks. Temporary filled-label surfaces were the final options mismatch. Archive/payload transport is compacted without changing the first 360 comparison results. Playable bytes are unchanged; board gameplay resource lifetimes, live integration and full money-loss replay remain open. See `testing/treehouse_board_initialization_resources.md`.

## Godot allocation and ownership port — 2026-10-13

The recovered allocation semantics now have GDScript implementations in
`resource_heap.gd`, `resource_near_heap.gd`, and `resource_memory.gd`. They
implement first/last-fit allocation, forward packing, handle relocation, near
allocation with explicit growth limits, locking, promotion, resize, discard,
raw/handle ownership transfers and catalog backlink cleanup. No CPU instruction
accounting or captured address schedule was added.

- `godot-resource-heap-b/report.json`: 402 passing checks. All 52 original
  preparation operations and both cursor-moving packing operations match,
  preserving payload hashes, block geometry, handles and search cursors. The
  operations make 171 moves in total. A continuous near-heap replay matches
  all 104 checkpoints and 237 allocation returns through 206 frees. Six focused
  checks cover padding, locking and bounded growth.
- `godot-resource-memory-c/report.json`: 668 passing checks. From one initial
  fixture, all 104 complete near/far structures and active/static handles match
  through 159 far allocations and 43 raw frees. Return-pointer assertions and
  eight focused ownership/resize checks also pass.

The fixtures are hash-checked original RAM and observed semantic operation
requests, used only by offline test drivers. This establishes the port of these
components; generated live resource requests and a complete payment replay
remain required. The game does not call these modules yet. The preview remains
`godot-scanout-build-a`; the current source inventory has advanced beyond that
export, so its browser evidence must not be described as testing these changes.

Retained attempts: `godot-resource-heap-red-a` used the wrong reference filename;
`godot-resource-heap-red-b` reports the missing Godot modules before implementation.
The first ownership run matched every memory state but its final empty-stack
assertion failed: the native window ends after preparation, inside one raw
allocation. The corrected assertion requires exactly that pending raw allocation;
its subsequent far allocation and return are present just beyond the observed
window. `godot-resource-memory-a/report.json` preserves the failed assertion.

Next: port generated startup/catalog loading into these Godot components, then
generate board redraw ownership and connect the live payment dependency. The
seven native fidelity discrepancies and all strict timing/audio requirements
remain open.

## Generated Godot startup resources — 2026-10-13

The allocation port now has a generated starting state. New Godot modules model
DOS conventional allocations and growth, startup near allocations, cached source
resources, archive directories, font/cursor conversion, saved surfaces, direct
raw copies, and digital-sound preparation. `resource_startup_assets.gd` composes
these through all seven startup archives and the retained initial sound.

`resource_startup_inputs.py` extracts the inputs from the pinned original EXE and
DAT bytes plus the documented DOS/Sound Blaster launch profile. The normal
`build_godot.py` now includes this compact base64 transport in
`original.json.resource_ownership`. No captured RAM, allocator addresses, call
stream, CPU instruction counts or native elapsed times enter this generation.

Evidence under `testing/output/treehouse/`:

- `godot-resource-startup-e/report.json`: all 108 checks pass using the normal
  generated asset bundle. This includes 98 native boundary-field comparisons
  (complete arena/near/DOS state, active payload hashes, files and catalog entries),
  five boundary-count checks and five focused cache/conversion checks. Native
  boundaries are comparison outputs only.
- `godot-resource-startup-d/report.json`: all 108 checks pass with direct source
  extraction; the normal bundle exercises the same production `from_data` entry.
- `godot-resource-memory-d/report.json`: all 668 continuous ownership checks
  still pass after the startup integration within the resource modules.
- `godot-resource-startup-assets-a.log`: normal resource generation succeeds,
  retaining all 2,337 shapes and 356 scripts. Asset bundle SHA-256:
  `57a482dfbd65ef1f52a51a4c80ab1a83ea2411e19c72c5f66e8d06b441474f2b`.

Early attempts A/B retain Godot identifier collisions (`Font` and global
`convert`) and their compile failures. They were renamed; no native mismatch
was waived. Attempt B's specific failed Godot child was stopped after its
compilation errors; the successful later runs exited normally.

This resource startup is still separate from the playable event loop. Title,
selection, room and board lifetime hooks remain required before its cursor
address can drive payment preparation. The preview still serves the previous
scanout export, and completion correctly fails because source has advanced as
well as because gameplay/timing/audio work remains open. Next is porting
palette, shape and animation ownership through the existing native title
boundaries, then continuing to board gameplay.

## Godot ownership reaches initial board options — 2026-10-13

Godot resource ownership now continues from generated startup through all three title animations, selection previews/departures/climb, initial room construction, outgoing ring/bubble transfer and initial Money/robot board options. Normal built-asset comparisons pass 377 checks for the boy-to-board route (366 native boundary/state/payload comparisons plus 11 checks), 209 for girl-to-room (204 native comparisons plus five checks), and 108 startup regression checks. Transfer resource events are driven by the production Godot SCR interpreter; initial board state uses production BoardGame with one explicitly supplied native entry seed. Room time/cloud/objects and two visible credit changes remain explicit semantic fixture inputs. These resource modules are not connected to the live game event loop. Board start/turn/redraw lifetimes and payment integration remain open; no Money fix or native timing/audio parity is claimed. Preview remains the prior scanout export.

See `treehouse_board_initialization_resources.md` for current evidence and semantic-input limits.
