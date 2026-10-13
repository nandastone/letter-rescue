# Animation resource preparation

## Purpose

The full money-loss journey still diverges at step 10. Its unused second
payment amount depends on the current cursor resource location. Generating
that location requires the original resource lifetimes, including animation
setup. This work supplies a complete constructor operation without executing
CPU instructions or consuming a recorded allocation schedule.

`OriginalAnimationMemory.prepare` follows main C39D through C77C: allocate the
animation object, scan the whole script for shape ranges, preload each marked
shape in ascending order, release temporary surface ownership, allocate the
surface and optional backup, and restore the palette's ownership flags.
Actual shape loads are supplied by the caller's persistent resource loader.
Only whole-palette ranges beginning at 1 are supported. Palette conversion
must already have been performed by the caller, as in the observed wrappers.

## Evidence

- `resource-startup-animation-a` captures six complete original constructors
  during an ordinary cold boot. The observer changes no game state.
- `resource-startup-animation-control-a.json` passes all 209 comparisons with
  the plain reference and the existing sound observer: screenshots, audio,
  complete ordinary RAM captures, callback timing and shared event timelines.
- `animation-memory-check-d` passes 24 comparisons over six constructors and
  80 generated shape loads. Each call starts from its own offline initial RAM
  fixture. Instructions come from matching SCR code in the pinned archives;
  adjusted rectangles are explicit caller inputs. All returned object/image
  handles, active handle flags and complete near/far allocator state match.
  Instruction-work modules are absent from this comparison.
- `animation-constructor-lifetimes-a` preserves all 104 existing checkpoints,
  79 shapes, 12 scene phases, 2,399 sounds and four focused checks. This older
  continuous comparison still has an initial fixture and observed logical
  allocation requests; it is not a fully generated game session.
- `animation-constructor-build-a/index.html` remains byte-identical to the
  served build, SHA-256
  `50db501cceb7b595f169978c2660d91e6346540992d7f20d2d85bb5d2e462542`.

The first comparison harness redundantly serialized entire archive payloads
six times and grew to 2 GB. It was explicitly terminated before comparison;
`animation-memory-check-a/report.json` records that failure. Shared shape
payloads make subsequent runs finish in seconds. B and C pass the native
checks; D additionally proves that every script body comes from the pinned
archives.

## Remaining integration

Connect palette loading, direct script ownership and animation preparation to
the generated startup state, then carry those lifetimes through activity and
board transitions. Playback can load additional sounds and resources and
change cache age; those operations also need continuous ownership.

No payment fix is delivered here. Newly converted pixel payloads, complete
startup-to-scene continuity, whole-session resource lifetimes, rendering and
sound timing remain outside this constructor comparison. Existing strict
fidelity failures remain required work.

## Continuous startup through the first title animation

`OriginalStartupResources.prepareTitle` now joins the previously verified
seven-archive startup to the first title-animation constructor. Overlay 5
206..308 supplies palette identifiers/bank masks, surface bounds, the title
sound and the first animation origin. The verifier extracts these values
from the pinned executable and SCR resource rather than from native events.

The generated sequence includes driver SND 65535, the title background's
palette and two shapes, its retained temporary surface, background palette
release, the animation palette, title music ownership, busy-cursor replacement,
an independently owned script copy and the complete animation constructor.
`OriginalPaletteLoading` handles explicit VGA bank masks; RGB hardware upload
is still the renderer's responsibility. `OriginalCatalogLoading.loadShape`
shares the catalog's persistent source cache with ordinary resource loading.

Joining these operations required a missing cleanup rule: original 64CE
clears the catalog backlink before freeing a cached source handle. The memory
model now tracks source ownership and clears that backlink on free. Discard
continues to retain it for reload. This prevents an old palette cache entry
from referring to a handle subsequently reused for another resource.

Evidence for the final models:

- `title-resources-check-b`: 24 comparisons at four original boundaries pass
  from continuously generated startup, with no native initial RAM, allocation
  requests or addresses driving the model. Complete allocator, DOS and catalog
  state match, as do all modeled source/font/cursor/sound payload hashes.
  Four extra checks cover palette release, discard, reload and handle reuse.
- `title-resource-control-a.json`: all 209 unchanged-original control checks.
- `title-resource-startup-regression-a`: 98 previous startup comparisons and
  six focused checks.
- `title-resource-animation-regression-a`: all six independent constructor
  comparisons, 24 checks and 80 shape loads.
- `title-resource-lifetimes-a`: 104 checkpoints, 79 shapes, 12 scene phases,
  2,399 sounds and four focused checks.
- `title-resource-board-load-a`: all four board-background ownership checks.
- `title-resource-build-a`: unchanged playable SHA `50db501cceb7`.

This comparison stops at the first title animation's preparation. It does
not establish playback, disposal or later startup/activity lifetimes. Between
the first and second native title constructors, the original restores CURS 0,
loads `midisnd:SND 20000`, disposes the first animation/script and selects the
busy cursor again. Those observations locate the next integration interval;
they must not become a recorded runtime resource schedule. The source caller
and sound-completion behavior need to drive it. The money-loss discrepancy and
all strict rendering/audio/timing failures remain open.

## Three title animation lifetimes and cleanup

The generated sequence now continues through all three title animations,
including normal/busy cursor replacement, repeated script ownership, disposal
of converted images and surfaces, and final palette/backdrop release. The
repeat count and origins are read from overlay 5 and its original data table.

The source explains the intervening SND 20000 load: main 4A56 calls resident
E5A2 to query playback status. E5A2 loads/resolves the sound before querying it.
It does not start that sound or replace the title music. The lifecycle model
now reproduces this resource side effect at script completion.

The first extended comparison (`title-lifecycle-check-a`) matched all three
constructors but failed at the final boundary on one flag: title music remained
locked in the model. Overlay 5:3C2 calls resident 577E to wait for active sound
completion before proceeding. `finishTitleMusic` now supplies the resource
release callback for the audio owner; completion scheduling is still the
audio player's responsibility.

`title-lifecycle-check-b` passes all **54** comparisons at nine boundaries and
the four cache checks, continuously from generated startup. It includes the
allocator, DOS state, catalog entries and all modeled source payloads after
title cleanup and sound completion, immediately before the next palette load.
No native initial RAM, addresses or recorded allocation sequence drive it.
`title-lifecycle-startup-regression-a` retains 98 earlier startup comparisons
and six focused checks. `title-lifecycle-build-a` remains byte-identical to
the served `50db501cceb7` build.

This is an ownership check at semantic completion boundaries. It does not
establish actual animation/audio durations, drawing during playback, title
interruption coverage or live runtime integration. Continue with the main
startup resources after the title and subsequent activity lifetimes; the
full money-loss discrepancy remains open.

## Resource startup reaches character selection

`OriginalStartupResources.initializeEntrance` now continues from completed
title ownership through main 547..D0E. It loads the six interface palettes,
selects the busy cursor, packs movable resources, creates the temporary full
screen, loads/draws/releases the original background and clock decorations,
and retains the two child palettes. It owns the saved rectangles around the
three initial child previews, releases the temporary screen, starts background
music ownership and restores the normal cursor.

The original wrapper is asked to stop after its first display for these
previews. The ownership model follows that caller branch; it does not pretend
to have timed or rendered complete child-entry animations. Palette identifiers,
bank masks, saved rectangles and script code are extracted from the original
executable and archives. The runtime module generates the sequence and the
verifier observes its results.

`entrance-resource-check-c` passes **144** comparisons at 24 native boundaries
and four focused cache checks, continuously from generated DOS startup to the
initial character-selection state. All allocator/handle metadata, DOS state,
catalogs and modeled source/font/cursor/sound payload hashes match. This
includes all six original constructor boundaries: three title animations and
three child previews. A and B are earlier passing increments; C verifies the
final reusable runtime orchestration.

The new `resource-startup-entrance-a` capture observes main ACE entry and D0E
return. All 209 ordinary-output and common-event control checks pass in
`entrance-resource-control-a.json`. The prior startup regression retains 98
comparisons and six focused checks in `entrance-resource-startup-regression-a`.
The `entrance-resource-build-a` output remains identical to served
`50db501cceb7`.

Next connect actual character selection, yard/room transitions and activity
lifetimes to this generated resource state. Startup interruptions, elapsed
animation/audio time, converted surface/image pixels and live integration
remain required. The full money-loss sequence still diverges at step 10; this
resource milestone does not close that failure or the strict fidelity issues.


## Character selection and entrance idle resources

`selectEntrance` implements main 0805..092B. It prepares the selected child's
SCR 8000/8001, the other child's script, then SCR 8002/8003 for the climb.
It releases each caller-owned background after the corresponding animation,
then releases both child palettes. It rejects a second selection after cleanup.
`prepareEntranceIdle` models main 05B6's cloud-dimension load.
`advanceEntranceCredit` models overlay 5:74's temporary screen, background draw,
next credit shape, and cleanup.

New ordinary mouse captures choose both children from cold boot. For each
variant, one observer records selection boundaries and another records all
animation constructors. Their complete ordinary PNG/WAV/RAM inventories and
callback timelines match independently booted plain controls: 423 boy and 407
girl checks. No native output is used as rendering input.

The final boy and girl resource checks each pass 192 comparisons at 32
boundaries plus six focused ownership/cache checks. All allocator/DOS/catalog
state and modeled payloads match through selection cleanup, continuously from
generated startup. Reports are `selection-resource-boy-final-a/report.json`
and `selection-resource-girl-final-a/report.json` under `output/treehouse`.

**Scope limitation:** the verifier supplies the initial cloud index 5 and two
visible credit-change events from this captured wait. Those semantic events
generate their own allocations and cleanup; they are not a captured allocator
request stream. Their live timing/renderer integration is still missing.
Animation playback likewise advances to semantic completion for this resource
check. This does not establish a continuously generated game clock, drawing,
audio, or complete payment behavior.

`selection-resource-baseline-a` fails because selection was unimplemented and
the entrance idle resources were missing. `selection-resource-check-a` retains
the failed first implementation before the cloud/credit operations were added.
`selection-resource-check-b` and `selection-resource-girl-a` are earlier passing
checks before adding explicit cleanup guards and scope metadata. They remain
unchanged. The live file and a fresh build both retain the delivered balloon
clearance SHA; no payment correction has been promoted.


## Initial interior construction

Generated ownership now reaches the first room for both children. See
[room resource lifetimes](treehouse_room_resource_lifetimes.md) for the two
corrected lifetime rules, native boundary evidence and remaining integration.
